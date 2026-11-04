"""Package verified repository outputs for Cloudflare Pages. No network access."""
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def validate(root=ROOT):
    report=json.loads((root/'blocklists/report.json').read_text())
    stamp=datetime.fromisoformat(report['generated_utc'])
    age=(datetime.now(timezone.utc)-stamp).total_seconds()
    if not -300 <= age <= 48*3600:
        raise ValueError('Blocklist report is stale or future-dated')
    catalog=json.loads((root/'catalog.json').read_text())
    from community import load
    if report.get('community',[])!=load(root):
        raise ValueError('Community policy must be rebuilt before publishing')
    if set(report['profiles'])!={item['id'] for item in catalog}:
        raise ValueError('Catalog and report profiles do not match')
    expected={f'blocklists/{profile}{suffix}' for profile in report['profiles'] for suffix in ('.txt','-domains.txt','-hosts.txt','-dnsmasq.conf','-unbound.conf','-rpz.zone')}
    if set(report['outputs']) != expected:
        raise ValueError('Missing or unexpected output manifest entries')
    for name,digest in report['outputs'].items():
        if (root/name).stat().st_size > 25*1024*1024:
            raise ValueError('Output exceeds Cloudflare Pages 25 MiB file limit: '+name)
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Output checksum mismatch: '+name)
    for profile,details in report['profiles'].items():
        domains=(root/f'blocklists/{profile}-domains.txt').read_text().splitlines()
        if domains != sorted(set(domains)) or len(domains)!=details['domains']:
            raise ValueError('Count/order/deduplication mismatch: '+profile)
    for source in report['sources']:
        if hashlib.sha256((root/f"sources/{source['id']}.txt").read_bytes()).hexdigest()!=source['sha256']:
            raise ValueError('Source checksum mismatch: '+source['id'])
    for rule_id,entry in report.get('scoped_overrides',{}).items():
        if rule_id not in {'ads-trackers','adult'} or entry['path']!=f'rules/{rule_id}.txt':
            raise ValueError('Unexpected scoped override path')
        if hashlib.sha256((root/entry['path']).read_bytes()).hexdigest()!=entry['sha256']:
            raise ValueError('Scoped override checksum mismatch: '+rule_id)
    return report

def build():
    report=validate()
    dist=ROOT/'dist'
    if dist.exists():
        # Fixed, repository-local build directory only.
        if dist.resolve().parent != ROOT.resolve():
            raise ValueError('Unsafe build directory')
        shutil.rmtree(dist)
    shutil.copytree(ROOT/'site',dist)
    # Content-addressed URLs prevent new HTML from using stale browser-cached code.
    replacements={}
    for name in ('style.css','app.js','submit.js','select.js'):
        data=(dist/name).read_bytes()
        stem,extension=name.rsplit('.',1)
        versioned=stem+'.'+hashlib.sha256(data).hexdigest()[:12]+'.'+extension
        (dist/versioned).write_bytes(data)
        replacements['/'+name]='/'+versioned
    for html in dist.glob('*.html'):
        text=html.read_text(encoding='utf-8')
        for original,versioned in replacements.items():
            text=text.replace('"'+original+'"','"'+versioned+'"')
        html.write_text(text,encoding='utf-8',newline='\n')
    shutil.copytree(ROOT/'blocklists',dist/'blocklists')
    shutil.copytree(ROOT/'sources',dist/'sources')
    shutil.copytree(ROOT/'rules',dist/'rules')
    shutil.copytree(ROOT/'licenses',dist/'licenses')
    for name in ('LICENSE','NOTICE','sources.json','catalog.json'):
        shutil.copyfile(ROOT/name,dist/name)
    # Capture the exact deployed commit so the monitor can detect stale deployments.
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    (dist/'deployment.json').write_text(json.dumps({'commit':commit,'generated_utc':report['generated_utc']},indent=2)+'\n')
    print(f'Pages output: {dist}; commit {commit}')

if __name__=='__main__':
    build()
