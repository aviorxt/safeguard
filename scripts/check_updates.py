"""Verify published Pages freshness, integrity and synchronization with GitHub."""
import argparse
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone

REPO='https://raw.githubusercontent.com/aviorxt/safeguard/main/'

def fetch(url,limit=30_000_000):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'AVRXT-Safeguard-Monitor/1.0','Cache-Control':'no-cache'}),timeout=60) as response:
        data=response.read(limit+1)
    if len(data)>limit:
        raise ValueError('Response exceeds expected size')
    return data

def verify(base):
    repo=json.loads(fetch(REPO+'blocklists/report.json'))
    report=json.loads(fetch(base+'/blocklists/report.json'))
    age=(datetime.now(timezone.utc)-datetime.fromisoformat(report['generated_utc'])).total_seconds()
    if not -300 <= age <= 48*3600:
        raise ValueError('Published lists have not refreshed within 48 hours')
    if report != repo:
        raise ValueError('Cloudflare Pages is behind the repository report')
    for path,digest in repo['outputs'].items():
        if hashlib.sha256(fetch(base+'/'+path)).hexdigest()!=digest:
            raise ValueError('Published list checksum mismatch: '+path)
    deployment=json.loads(fetch(base+'/deployment.json'))
    page=fetch(base+'/').decode()
    if 'AVRXT Safeguard' not in page or len(deployment['commit'])!=40:
        raise ValueError('Unexpected site response or missing deployment identity')
    print('PASS: HTTPS site, all six list checksums, GitHub report sync, and <48h freshness')
    print('Deployed commit:',deployment['commit'])
    print('Last successful list update:',report['generated_utc'])

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--base',default='https://safeguard.avrxt.tech')
    parser.add_argument('--attempts',type=int,default=1)
    args=parser.parse_args()
    if not args.base.startswith('https://'):
        parser.error('HTTPS required')
    for attempt in range(args.attempts):
        try:
            verify(args.base.rstrip('/'))
            break
        except (OSError,ValueError) as exc:
            if attempt+1==args.attempts:
                raise
            print(f'Waiting for Pages deployment: {exc}',flush=True)
            time.sleep(30)
