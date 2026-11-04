"""Validate reviewed community submissions; no user text is executed."""
import json
import re
from datetime import datetime
from pathlib import Path
from build import domain

def targets(category):
    if category in {'ads-trackers','threats'}:
        return {category,'standard','family'}
    if category in {'malware','phishing','cryptomining'}:
        return {category,'threats','standard','family'}
    if category=='adult':
        return {'adult','family'}
    return {category}

def validate(entries,catalog):
    categories={item['id'] for item in catalog}-{'family','standard'}
    seen=set()
    if not isinstance(entries,list):
        raise ValueError('Community records must be a list')
    for entry in entries:
        if set(entry)!={'domain','category','username','issue','accepted_utc'}:
            raise ValueError('Unexpected contribution fields')
        if entry['category'] not in categories or domain(entry['domain'])!=entry['domain']:
            raise ValueError('Invalid category or non-canonical domain')
        if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?',entry['username']):
            raise ValueError('Invalid GitHub username')
        if type(entry['issue']) is not int or entry['issue']<1 or entry['issue'] in seen:
            raise ValueError('Invalid or duplicate issue')
        seen.add(entry['issue'])
        if datetime.fromisoformat(entry['accepted_utc']).utcoffset() is None:
            raise ValueError('Timestamp must include timezone')
    return entries

def load(root):
    path=Path(root)/'rules/community.json'
    return validate(json.loads(path.read_text()) if path.exists() else [],json.loads((Path(root)/'catalog.json').read_text()))

def markdown(entries):
    text='# Community contributors\n\nCredit for accepted, published domain submissions. Usernames are verified against the GitHub issue author.\n\n'
    ordered=sorted(entries,key=lambda item:datetime.fromisoformat(item['accepted_utc']),reverse=True)
    if not ordered:
        return text+'No community domain submissions have been published yet. [Suggest a domain](https://safeguard.avrxt.tech/update-list).\n'
    latest=ordered[0]
    text+='Last updated by [@'+latest['username']+'](https://github.com/'+latest['username']+').\n\n'
    text+='| Contributor | Domain | Category | Accepted (UTC) | Request |\n| --- | --- | --- | --- | --- |\n'
    for entry in ordered:
        text+='| <img src="https://github.com/'+entry['username']+'.png?size=64" width="32" height="32" alt=""> [@'+entry['username']+'](https://github.com/'+entry['username']+') | `'+entry['domain']+'` | '+entry['category']+' | '+entry['accepted_utc'][:10]+' | [#'+str(entry['issue'])+'](https://github.com/aviorxt/safeguard/issues/'+str(entry['issue'])+') |\n'
    return text
