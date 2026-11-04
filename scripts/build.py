"""Build strict DNS-only blocklists. Standard library only; Python 3.11+."""
import hashlib
import ipaddress
import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
MAX_BYTES = 50_000_000

def domain(value):
    try:
        value = value.rstrip('.').encode('idna').decode('ascii').lower()
        ipaddress.ip_address(value)
        raise ValueError('IP addresses are not domains')
    except UnicodeError:
        raise ValueError('Invalid IDN')
    except ValueError as exc:
        if str(exc) == 'IP addresses are not domains':
            raise
    parts = value.split('.')
    if len(value)>253 or len(parts)<2 or not all(LABEL.fullmatch(p) for p in parts):
        raise ValueError('Invalid domain: '+value)
    if parts[-1].isdigit() or parts[-1] in {'local','localhost','invalid','test','example','internal'}:
        raise ValueError('Reserved domain')
    # Reject broad registry suffixes; trusted manifest inputs still require review.
    if value in {'co.uk','org.uk','ac.uk','gov.uk','com.au','net.au','org.au','co.in','net.in','org.in','co.jp','co.nz','co.za','com.br','com.cn','com.sg','com.mx','com.tr'}:
        raise ValueError('Broad registry suffix')
    return value

def parse(text):
    result=set()
    for number, raw in enumerate(text.splitlines(),1):
        line=raw.strip()
        if not line or line.startswith(('!','#','[')):
            continue
        if line.startswith(('0.0.0.0 ', '0.0.0.0\t')):
            fields=line.split()
            if len(fields)!=2:
                raise ValueError(f'Unsupported hosts rule at line {number}')
            line=fields[1]
        if line.startswith('||') and line.endswith('^'):
            line=line[2:-1]
        try:
            result.add(domain(line))
        except ValueError as exc:
            raise ValueError(f'Unsupported rule at line {number}: {raw[:100]}') from exc
    return result

def related(a,b):
    return a==b or a.endswith('.'+b) or b.endswith('.'+a)

def parse_source(text,source):
    if not source.get('exclude_invalid_hostnames',False):
        return parse(text),[]
    result=set(); rejected=[]; total=0
    for number,line in enumerate(text.splitlines(),1):
        if not line.strip() or line.startswith(('!','#','[')):
            continue
        # Reviewed hosts-only feeds may contain syntactically invalid hostnames.
        # Preserve their full source and audit every exclusion; never relax DNS syntax.
        if not re.fullmatch(r'0\.0\.0\.0\s+\S+',line):
            raise ValueError(f'Unexpected source syntax at line {number}')
        total+=1
        try:
            result.update(parse(line))
        except ValueError:
            rejected.append({'line':number,'rule':line,'reason':'Not a portable DNS hostname'})
    if len(rejected)>total*.01:
        raise ValueError('More than 1% invalid hostnames in source')
    return result,rejected

def apply_allow(blocked, allowed):
    # Enumerate ancestors, avoiding quadratic scans across large family lists.
    remove=set()
    for a in allowed:
        p=a.split('.')
        remove.update('.'.join(p[i:]) for i in range(len(p)-1))
    for b in blocked:
        p=b.split('.')
        if any('.'.join(p[i:]) in allowed for i in range(len(p)-1)):
            remove.add(b)
    return blocked-remove, sorted(blocked & remove)

def download(url):
    approved=('https://raw.githubusercontent.com/hagezi/dns-blocklists/',
              'https://raw.githubusercontent.com/hoshsadiq/adblock-nocoin-list/',
              'https://curbengh.github.io/phishing-filter/',
              'https://curbengh.github.io/malware-filter/')
    if not url.startswith(approved):
        raise ValueError('Source must be on the reviewed HTTPS source allowlist')
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'AVRXT-Safeguard/1.0'}),timeout=90) as response:
                data=response.read(MAX_BYTES+1)
            if len(data)>MAX_BYTES:
                raise ValueError('Source too large')
            return data
        except (OSError,TimeoutError):
            if attempt==2:
                raise
            time.sleep(2**attempt)

def build():
    manifest=json.loads((ROOT/'sources.json').read_text())
    stage={}
    catalog=json.loads((ROOT/'catalog.json').read_text())
    if len({item['id'] for item in catalog}) != len(catalog):
        raise ValueError('Duplicate catalog IDs')
    if not all(re.fullmatch('[a-z0-9-]+',item['id']) for item in catalog):
        raise ValueError('Unsafe catalog ID')
    profiles={item['id']:set() for item in catalog}
    report={'generated_utc':datetime.now(timezone.utc).isoformat(),'sources':[],'profiles':{}}
    for source in manifest:
        source_id=source['id']
        if not re.fullmatch('[a-z0-9-]+',source_id):
            raise ValueError('Invalid source ID')
        data=download(source['url'])
        entries,rejected=parse_source(data.decode('utf-8-sig'),source)
        previous=ROOT/'sources'/f'{source_id}.txt'
        if len(entries)<source['minimum']:
            raise ValueError(f'{source_id}: below minimum')
        if previous.exists() and len(entries)<len(parse_source(previous.read_text(encoding='utf-8-sig'),source)[0])*.75:
            raise ValueError(f'{source_id}: unexpected reduction over 25%')
        stage[f'sources/{source_id}.txt']=data
        stage[f'sources/{source_id}-excluded.json']=(json.dumps(rejected,indent=2)+'\n').encode()
        report['sources'].append({**source,'domains':len(entries),'sha256':hashlib.sha256(data).hexdigest(),'rejected_rules':len(rejected)})
        for profile in source['profiles']:
            profiles[profile].update(entries)
    allowed=parse((ROOT/'rules/allow.txt').read_text())
    custom=parse((ROOT/'rules/block.txt').read_text())
    scoped={}
    report['scoped_overrides']={}
    from community import load, targets as community_targets, markdown
    contributions=load(ROOT)
    report['community']=contributions
    stage['CONTRIBUTORS.md']=markdown(contributions).encode('utf-8')
    for rule_id,targets in [('ads-trackers',{'standard','family','ads-trackers'}),('adult',{'family','adult'})]:
        path=ROOT/'rules'/f'{rule_id}.txt'
        data=path.read_bytes() if path.exists() else b''
        scoped[rule_id]=(parse(data.decode('utf-8')),targets)
        report['scoped_overrides'][rule_id]={'path':f'rules/{rule_id}.txt','domains':len(scoped[rule_id][0]),'profiles':sorted(targets),'sha256':hashlib.sha256(data).hexdigest()}
    for name,entries in profiles.items():
        entries=entries|{item['domain'] for item in contributions if name in community_targets(item['category'])}
        for extra,targets in scoped.values():
            if name in targets:
                entries=entries|extra
        entries,suppressed=apply_allow(entries|custom,allowed)
        ordered=sorted(entries)
        if not entries:
            raise ValueError('Empty profile: '+name)
        title=next(item['name'] for item in catalog if item['id']==name)
        header=f'! Title: AVRXT Safeguard {title}\n! Homepage: https://github.com/aviorxt/safeguard\n! License: GPL-3.0; MIT notices in licenses/; see NOTICE\n! Modified aggregation of reviewed upstream lists; {len(entries)} unique domains\n! Expires: 1 day\n'
        stage[f'blocklists/{name}.txt']=(header+''.join('||'+d+'^\n' for d in ordered)).encode()
        stage[f'blocklists/{name}-domains.txt']=('\n'.join(ordered)+'\n').encode()
        stage[f'blocklists/{name}-hosts.txt']=('# AVRXT Safeguard; GPL-3.0; see NOTICE\n'+''.join('0.0.0.0 '+d+'\n' for d in ordered)).encode()
        stage[f'blocklists/{name}-dnsmasq.conf']=('# AVRXT Safeguard; GPL-3.0; see NOTICE\n'+''.join('local=/'+d+'/\n' for d in ordered)).encode()
        stage[f'blocklists/{name}-unbound.conf']=('# AVRXT Safeguard; include inside server:; GPL-3.0; see NOTICE\n'+''.join('local-zone: "'+d+'" always_nxdomain\n' for d in ordered)).encode()
        rpz='; AVRXT Safeguard; GPL-3.0; see NOTICE\n$TTL 60\n@ IN SOA localhost. hostmaster.localhost. ( '+str(int(datetime.now(timezone.utc).timestamp()))+' 3600 600 86400 60 )\n@ IN NS localhost.\n'
        stage[f'blocklists/{name}-rpz.zone']=(rpz+''.join(d+' CNAME .\n*.'+d+' CNAME .\n' for d in ordered)).encode()
        report['profiles'][name]={'domains':len(entries),'suppressed_by_allowlist':suppressed}
    report['outputs']={k:hashlib.sha256(v).hexdigest() for k,v in stage.items() if k.startswith('blocklists/')}
    stage['blocklists/report.json']=(json.dumps(report,indent=2)+'\n').encode()
    # All downloads/validation complete before any published file is touched.
    for path,data in stage.items():
        dest=ROOT/path
        dest.parent.mkdir(parents=True,exist_ok=True)
        temp=dest.with_suffix(dest.suffix+'.tmp')
        temp.write_bytes(data)
        temp.replace(dest)
    print(json.dumps(report['profiles'],indent=2))

if __name__=='__main__':
    build()
