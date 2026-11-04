"""Turn a maintainer-approved issue into validated, attributed policy data."""
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from build import ROOT, domain
from community import load, validate

def main():
    event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    repo=os.environ['GITHUB_REPOSITORY']
    token=os.environ['GH_TOKEN']
    def api(path):
        request=urllib.request.Request('https://api.github.com/repos/'+repo+'/'+path,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'Safeguard-community'})
        with urllib.request.urlopen(request,timeout=30) as response:
            return json.load(response)
    actor=event['sender']['login']
    if api('collaborators/'+actor+'/permission')['permission'] not in {'admin','maintain','write'}:
        raise ValueError('Only maintainers may approve submissions')
    issue=api('issues/'+str(event['issue']['number']))
    if issue['state']!='open' or 'pull_request' in issue or 'approved-domain' not in {x['name'] for x in issue['labels']}:
        raise ValueError('Issue is not an approved open submission')
    def field(name):
        found=re.findall(r'^### '+re.escape(name)+r'\r?\n\r?\n([^\r\n]+)',issue.get('body') or '',re.M)
        if len(found)!=1:
            raise ValueError('Missing or duplicate '+name)
        return found[0].strip()
    username=field('GitHub username').lstrip('@')
    if username.lower()!=issue['user']['login'].lower():
        raise ValueError('Entered username must match authenticated issue author')
    entry={'domain':domain(field('Domain')),'category':field('Category'),'username':issue['user']['login'],'issue':issue['number'],'accepted_utc':datetime.now(timezone.utc).isoformat()}
    entries=load(ROOT)
    if any(x['issue']==entry['issue'] for x in entries):
        raise ValueError('Submission has already been accepted')
    entries.append(entry)
    validate(entries,json.loads((ROOT/'catalog.json').read_text()))
    (ROOT/'rules/community.json').write_text(json.dumps(entries,indent=2)+'\n')
    print('Validated submission from @'+entry['username']+' for '+entry['category'])

if __name__=='__main__':
    main()
