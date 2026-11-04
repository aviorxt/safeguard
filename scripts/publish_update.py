"""Publish daily generated data through a validated PR, never a direct main push."""
import json
import os
import subprocess
import time
import urllib.request
import urllib.error

def git(*args):
    return subprocess.check_output(['git',*args],text=True).strip()

def main():
    if os.environ.get('GITHUB_REF')!='refs/heads/main':
        raise RuntimeError('Publishing is allowed only from main')
    repo=os.environ['GITHUB_REPOSITORY']
    token=os.environ['GH_TOKEN']
    branch='automation/blocklists-'+os.environ['GITHUB_RUN_ID']+'-'+os.environ['GITHUB_RUN_ATTEMPT']
    def api(path,method='GET',data=None):
        request=urllib.request.Request('https://api.github.com/repos/'+repo+'/'+path,method=method,
            headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'Safeguard-publisher','X-GitHub-Api-Version':'2022-11-28'},
            data=json.dumps(data).encode() if data is not None else None)
        try:
            with urllib.request.urlopen(request,timeout=60) as response:
                body=response.read()
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            # Only fixed GitHub API paths are used; never include token-bearing URLs.
            raise RuntimeError(f'GitHub API {method} {path}: HTTP {exc.code}: '+exc.read().decode()) from None
    git('add','blocklists','sources')
    if not git('diff','--cached','--name-only'):
        print('No generated changes to publish.')
        return
    git('config','user.name','github-actions[bot]')
    git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    git('switch','-c',branch)
    git('commit','-m','Update validated Safeguard blocklists')
    sha=git('rev-parse','HEAD')
    for attempt in range(3):
        try:
            git('push','origin',branch)
            break
        except subprocess.CalledProcessError:
            if attempt==2:
                raise
            time.sleep(2**attempt)
    pr=api('pulls','POST',{'title':'Update validated Safeguard blocklists','head':branch,'base':'main',
        'body':'## Generated update\nRefresh reviewed upstream feeds and regenerate every subscription format.\n\n## Validation\nSource safeguards, unit tests and site integrity validation passed before this PR. The publisher dispatches the required repository validation and waits for its result before merging. Native RPZ, dnsmasq and Unbound checks run in that validation.\n\n## Compatibility\nExisting subscription URLs and category policy are preserved. Review the report diff for source counts, exclusions and hashes.\n\n## Rollback\nRevert this generated-data commit through a validated pull request and rerun the updater.'})
    print('Generated update PR:',pr['html_url'],flush=True)
    # workflow_dispatch is one of the events permitted to trigger from GITHUB_TOKEN.
    api('actions/workflows/ci.yml/dispatches','POST',{'ref':branch})
    deadline=time.monotonic()+600
    while time.monotonic()<deadline:
        runs=api('actions/workflows/ci.yml/runs?event=workflow_dispatch&per_page=30')['workflow_runs']
        matching=[run for run in runs if run['head_sha']==sha]
        if matching:
            run=max(matching,key=lambda item:item['id'])
            if run['status']=='completed':
                if run['conclusion']!='success':
                    raise RuntimeError('Update remains unmerged; validation failed: '+run['html_url'])
                # The server independently enforces PR rules and required status checks.
                result=api('pulls/'+str(pr['number'])+'/merge','PUT',{'merge_method':'squash','sha':sha,'commit_title':'Update validated Safeguard blocklists'})
                if not result.get('merged'):
                    raise RuntimeError('Update PR was not merged; review '+pr['html_url'])
                print('Merged validated update:',result['sha'],flush=True)
                api('git/refs/heads/'+branch,'DELETE')
                return
        time.sleep(15)
    raise RuntimeError('Validation timed out; update PR remains open for review: '+pr['html_url'])

if __name__=='__main__':
    main()
