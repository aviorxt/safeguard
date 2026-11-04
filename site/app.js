'use strict';
const $ = id => document.getElementById(id);
document.addEventListener('click', async event => {
  const button=event.target.closest('[data-copy]');
  if(!button) return;
  const input=$(button.dataset.copy);
  try {
    await navigator.clipboard.writeText(input.value);
    button.textContent='Copied ✓'; $('copy-status').textContent='Subscription URL copied.';
    setTimeout(()=>{button.textContent='Copy ↗';},2000);
  } catch {
    input.focus(); input.select(); $('copy-status').textContent='Select and copy the subscription URL manually.';
  }
});
document.querySelectorAll('.main-format').forEach(select=>select.addEventListener('change',()=>{
  $(select.dataset.profile+'-url').value='https://safeguard.avrxt.tech/blocklists/'+select.dataset.profile+select.value;
}));
let categoryCatalog=[], categoryReport={}, selectedGroup='All';
function renderCategories() {
  const query=$('category-search').value.trim().toLowerCase();
  const suffix=$('category-format').value;
  const matching=categoryCatalog.filter(item=>item.group!=='Combined' && (selectedGroup==='All'||item.group===selectedGroup) && (item.name+' '+item.description+' '+item.group).toLowerCase().includes(query));
  $('category-results').textContent=matching.length+' categories / '+$('category-format').selectedOptions[0].text;
  $('category-grid').replaceChildren();
  for(const item of matching) {
    const card=document.createElement('article');card.className='category-card';
    const top=document.createElement('div');top.className='category-top';
    const tag=document.createElement('span');tag.className='tag';tag.textContent=item.group;
    const count=document.createElement('span');count.className='category-count';count.textContent=(categoryReport[item.id]?.domains??0).toLocaleString()+' domains';top.append(tag,count);
    const heading=document.createElement('h3');heading.textContent=item.name;
    const description=document.createElement('p');description.textContent=item.description;
    const warning=document.createElement('p');warning.className='category-warning';warning.textContent=item.warning;
    const field=document.createElement('div');field.className='copy-field';
    const input=document.createElement('input');input.id='category-'+item.id;input.readOnly=true;input.setAttribute('aria-label',item.name+' subscription URL');input.value='https://safeguard.avrxt.tech/blocklists/'+item.id+suffix;
    const button=document.createElement('button');button.type='button';button.dataset.copy=input.id;button.setAttribute('aria-label','Copy '+item.name+' URL');button.textContent='Copy ↗';field.append(input,button);
    const links=document.createElement('div');links.className='formats';
    for(const [label,extension] of [['AdGuard','.txt'],['Domains','-domains.txt'],['Hosts','-hosts.txt'],['dnsmasq','-dnsmasq.conf'],['Unbound','-unbound.conf'],['RPZ','-rpz.zone']]) {
      const link=document.createElement('a');link.href='/blocklists/'+item.id+extension;link.textContent=label;link.download='';links.append(link);
    }
    card.append(top,heading,description,warning,field,links);$('category-grid').append(card);
  }
}
$('category-search').addEventListener('input',renderCategories);
$('category-format').addEventListener('change',renderCategories);
document.querySelectorAll('[data-group]').forEach(button=>button.addEventListener('click',()=>{
  selectedGroup=button.dataset.group;
  document.querySelectorAll('[data-group]').forEach(other=>other.setAttribute('aria-pressed',String(other===button)));
  renderCategories();
}));
const formatDate = value => new Intl.DateTimeFormat(undefined,{dateStyle:'medium',timeStyle:'short'}).format(new Date(value));
async function loadStatus() {
  try {
    const response=await fetch('/blocklists/report.json',{cache:'no-store'});
    if(!response.ok) throw new Error('Report unavailable');
    const report=await response.json();
    categoryReport=report.profiles;
    const catalogResponse=await fetch('/catalog.json',{cache:'no-store'});
    if(!catalogResponse.ok) throw new Error('Category catalog unavailable');
    categoryCatalog=await catalogResponse.json();
    renderCategories();
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
    $('category-results').textContent='Catalog unavailable. Subscription links are available on GitHub.';
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
