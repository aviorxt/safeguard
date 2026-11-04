'use strict';
const el=id=>document.getElementById(id);
let categories=[];
function normalizeDomain(raw) {
  if(/[\s/@:#?*\\]/.test(raw)||!raw.includes('.')) throw new Error('Enter one domain, without a URL, port, wildcard, or path.');
  const value=new URL('https://'+raw).hostname.replace(/\.$/,'').toLowerCase();
  const parts=value.split('.');
  if(value.length>253||parts.some(p=>! /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(p))||/^\d+$/.test(parts.at(-1))||['local','localhost','test','invalid','internal','example'].includes(parts.at(-1))) throw new Error('Enter a valid public domain name.');
  return value;
}
el('domain-category').addEventListener('change',()=>{
  el('category-policy').textContent=categories.find(x=>x.id===el('domain-category').value)?.warning||'';
});
el('domain-form').addEventListener('submit',event=>{
  event.preventDefault();
  try {
    const username=el('github-username').value.trim();
    const category=el('domain-category').value;
    if(!categories.some(x=>x.id===category)) throw new Error('Select a category.');
    const domain=normalizeDomain(el('domain-name').value.trim());
    el('domain-name').value=domain;
    const url=new URL('https://github.com/aviorxt/safeguard/issues/new');
    url.searchParams.set('template','domain-submission.yml');
    url.searchParams.set('title','[Domain submission]: '+domain);
    for(const [key,value] of Object.entries({username,category,domain,evidence:el('domain-evidence').value.trim()})) url.searchParams.set(key,value);
    el('submission-status').textContent='Opening GitHub. Confirm the request there; accepted updates are credited after publication.';
    window.location.assign(url.href);
  } catch(error) {el('submission-status').textContent=error.message;}
});
async function load() {
  try {
    const response=await fetch('/catalog.json');if(!response.ok) throw new Error();
    categories=(await response.json()).filter(x=>!['family','standard'].includes(x.id));
    el('domain-category').replaceChildren(new Option('Choose a category',''),...categories.map(x=>new Option(x.name,x.id)));
    el('submit-domain').disabled=false;
  } catch {el('submission-status').textContent='Categories are unavailable. Please reload or use the GitHub submission form.';}
  try {
    const response=await fetch('/blocklists/report.json',{cache:'no-store'});if(!response.ok) throw new Error();
    const entries=(await response.json()).community||[];
    entries.sort((a,b)=>Date.parse(b.accepted_utc)-Date.parse(a.accepted_utc));
    el('last-contributor').textContent=entries.length?'Last updated by @'+entries[0].username+' · accepted '+new Date(entries[0].accepted_utc).toLocaleDateString():'No community submissions have been published yet. Your discovery could be the first.';
    for(const entry of entries.slice(0,20)) {
      const row=document.createElement('article');row.className='contribution-row';
      const domain=document.createElement('strong');domain.textContent=entry.domain;
      const category=document.createElement('span');category.textContent=entry.category;
      const credit=document.createElement('a');credit.textContent='@'+entry.username+' ↗';credit.href='https://github.com/aviorxt/safeguard/issues/'+Number(entry.issue);
      row.append(domain,category,credit);el('contribution-list').append(row);
    }
  } catch {el('last-contributor').textContent='Contribution history is unavailable. View requests on GitHub.';}
}
load();
