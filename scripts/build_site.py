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
    expected={f'blocklists/{profile}{suffix}.txt' for profile in ('standard','family') for suffix in ('','-domains','-hosts')}
    if set(report['outputs']) != expected:
        raise ValueError('Missing or unexpected output manifest entries')
    for name,digest in report['outputs'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Output checksum mismatch: '+name)
    for profile,details in report['profiles'].items():
        domains=(root/f'blocklists/{profile}-domains.txt').read_text().splitlines()
        if domains != sorted(set(domains)) or len(domains)!=details['domains']:
            raise ValueError('Count/order/deduplication mismatch: '+profile)
    for source in report['sources']:
        if hashlib.sha256((root/f"sources/{source['id']}.txt").read_bytes()).hexdigest()!=source['sha256']:
            raise ValueError('Source checksum mismatch: '+source['id'])
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
    shutil.copytree(ROOT/'blocklists',dist/'blocklists')
    shutil.copytree(ROOT/'sources',dist/'sources')
    for name in ('LICENSE','NOTICE','sources.json'):
        shutil.copyfile(ROOT/name,dist/name)
    # Capture the exact deployed commit so the monitor can detect stale deployments.
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    (dist/'deployment.json').write_text(json.dumps({'commit':commit,'generated_utc':report['generated_utc']},indent=2)+'\n')
    print(f'Pages output: {dist}; commit {commit}')

if __name__=='__main__':
    build()
