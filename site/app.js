'use strict';
const $ = id => document.getElementById(id);
document.querySelectorAll('[data-copy]').forEach(button => button.addEventListener('click', async () => {
  const input=$(button.dataset.copy);
  try {
    await navigator.clipboard.writeText(input.value);
    button.textContent='Copied ✓'; $('copy-status').textContent='Subscription URL copied.';
    setTimeout(()=>{button.textContent='Copy ↗';},2000);
  } catch {
    input.focus(); input.select(); $('copy-status').textContent='Select and copy the subscription URL manually.';
  }
}));
const formatDate = value => new Intl.DateTimeFormat(undefined,{dateStyle:'medium',timeStyle:'short'}).format(new Date(value));
async function loadStatus() {
  try {
    const response=await fetch('/blocklists/report.json',{cache:'no-store'});
    if(!response.ok) throw new Error('Report unavailable');
    const report=await response.json();
    const age=(Date.now()-Date.parse(report.generated_utc))/3600000;
    if(!Number.isFinite(age) || !report.profiles?.family || !report.profiles?.standard) throw new Error('Invalid report');
    $('family-count').textContent=report.profiles.family.domains.toLocaleString();
    $('standard-count').textContent=report.profiles.standard.domains.toLocaleString();
    $('updated').textContent=new Intl.DateTimeFormat(undefined,{dateStyle:'medium'}).format(new Date(report.generated_utc));
    $('report-time').textContent=formatDate(report.generated_utc)+' (your time)';
    const fresh=age>=-0.1 && age<=48;
    $('freshness').textContent=fresh?'LIST REPORT CURRENT / <48H':'LIST UPDATE OVERDUE — CHECK ACTIONS';
    $('freshness').dataset.state=fresh?'fresh':'stale';
    $('sources').replaceChildren();
    for(const source of report.sources) {
      const card=document.createElement('article');card.className='source';
      const heading=document.createElement('h3');heading.textContent=source.name;
      const details=document.createElement('p');details.textContent=source.domains.toLocaleString()+' SOURCE DOMAINS';
      const link=document.createElement('a');link.href='/sources/'+encodeURIComponent(source.id)+'.txt';link.textContent='Inspect source snapshot ↗';
      card.append(heading,details,link);$('sources').append(card);
    }
  } catch {
    $('freshness').textContent='REPORT UNAVAILABLE — CHECK ACTIONS';$('freshness').dataset.state='stale';
    $('updated').textContent='Unavailable';$('report-time').textContent='Could not load list report';
    $('sources').textContent='Source information is available in the GitHub repository.';
  }
  try {
    const response=await fetch('/deployment.json',{cache:'no-store'});
    if(!response.ok) throw new Error('No deployment metadata');
    const deployment=await response.json();
    if(!/^[a-f0-9]{40}$/.test(deployment.commit)) throw new Error('Invalid revision');
    $('revision').textContent=deployment.commit.slice(0,8)+' ↗';
    $('revision').href='https://github.com/aviorxt/safeguard/commit/'+deployment.commit;
  } catch { $('revision').textContent='View GitHub history ↗'; }
}
loadStatus();
setInterval(loadStatus,300000);
