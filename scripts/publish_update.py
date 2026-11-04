"""Publish daily generated data through a validated PR, never a direct main push."""
import json
import os
import subprocess
import time
import urllib.request
import urllib.error
import urllib.parse

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
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request,timeout=60) as response:
                    body=response.read()
                    return json.loads(body) if body else {}
            except urllib.error.HTTPError as exc:
                detail=exc.read().decode()
                if exc.code>=500:
                    # A server error can arrive after a mutation succeeded.
                    if method=='POST' and path=='pulls':
                        prior=api('pulls?state=open&head='+urllib.parse.quote(repo.split('/')[0]+':'+branch,safe=''))
                        if prior:
                            return prior[0]
                    if method=='PUT' and path.endswith('/merge'):
                        prior=api(path.rsplit('/',1)[0])
                        if prior.get('merged'):
                            return {'merged':True,'sha':prior['merge_commit_sha']}
                    if attempt<2:
                        time.sleep(2**attempt)
                        continue
                raise RuntimeError(f'GitHub API {method} {path}: HTTP {exc.code}: '+detail) from None
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
    api('statuses/'+sha,'POST',{'state':'pending','context':'Safeguard validation',
        'description':'Waiting for dispatched repository CI','target_url':pr['html_url']})
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
                    api('statuses/'+sha,'POST',{'state':'failure','context':'Safeguard validation',
                        'description':'Repository CI: '+run['conclusion'],'target_url':run['html_url']})
                    raise RuntimeError('Update remains unmerged; validation failed: '+run['html_url'])
                # GITHUB_TOKEN-dispatched CI does not trigger a downstream workflow_run.
                # Attest only the actual canonical CI run's success on this exact SHA.
                api('statuses/'+sha,'POST',{'state':'success','context':'Safeguard validation',
                    'description':'Dispatched repository CI passed','target_url':run['html_url']})
                # The server independently enforces PR rules and required status checks.
                for merge_attempt in range(6):
                    try:
                        result=api('pulls/'+str(pr['number'])+'/merge','PUT',{'merge_method':'squash','sha':sha,'commit_title':'Update validated Safeguard blocklists'})
                        break
                    except RuntimeError as exc:
                        if merge_attempt==5 or 'HTTP 405' not in str(exc) or 'Required status check' not in str(exc):
                            raise
                        # GitHub may briefly lag between run completion and rule evaluation.
                        time.sleep(15)
                if not result.get('merged'):
                    raise RuntimeError('Update PR was not merged; review '+pr['html_url'])
                print('Merged validated update:',result['sha'],flush=True)
                try:
                    api('git/refs/heads/'+branch,'DELETE')
                except RuntimeError:
                    print('Update merged; temporary branch cleanup can be completed later.')
                return
        time.sleep(15)
    api('statuses/'+sha,'POST',{'state':'error','context':'Safeguard validation',
        'description':'Repository validation timed out','target_url':pr['html_url']})
    raise RuntimeError('Validation timed out; update PR remains open for review: '+pr['html_url'])

if __name__=='__main__':
    main()
