'use strict';
// Keep the native data model and change events; render a fully themed interaction.
document.querySelectorAll('select').forEach((select,index)=>{
  const wrapper=document.createElement('div');wrapper.className='sg-select';
  const button=document.createElement('button');button.type='button';button.className='sg-select-trigger';
  const value=document.createElement('span');
  const arrow=document.createElement('span');arrow.className='sg-select-arrow';arrow.textContent='⌄';arrow.setAttribute('aria-hidden','true');
  const list=document.createElement('div');list.className='sg-select-list';list.id='sg-options-'+index;list.role='listbox';list.hidden=true;
  button.role='combobox';button.setAttribute('aria-haspopup','listbox');button.setAttribute('aria-expanded','false');button.setAttribute('aria-controls',list.id);
  const label=select.labels?.[0];
  if(label){const name=Array.from(label.childNodes).filter(node=>node.nodeType===3).map(node=>node.textContent).join(' ').trim();button.setAttribute('aria-label',name||select.getAttribute('aria-label')||'Choose an option');label.addEventListener('click',event=>{if(event.target===label){event.preventDefault();button.focus();}});}
  else button.setAttribute('aria-label',select.getAttribute('aria-label')||'Choose an option');
  select.before(wrapper);wrapper.append(select,button,list);button.append(value,arrow);
  select.classList.add('sg-native');select.tabIndex=-1;select.setAttribute('aria-hidden','true');
  // The submission handler validates the selected category with an inline message.
  select.required=false;
  let active=0,options=[],typeahead='',typeaheadAt=0;
  const close=()=>{list.hidden=true;button.setAttribute('aria-expanded','false');button.removeAttribute('aria-activedescendant');};
  const highlight=number=>{
    active=(number+options.length)%options.length;
    list.querySelectorAll('[role=option]').forEach((item,i)=>item.dataset.active=String(i===active));
    const item=list.children[active];if(item){button.setAttribute('aria-activedescendant',item.id);item.scrollIntoView({block:'nearest'});}
  };
  const open=()=>{if(!options.length||button.disabled)return;list.hidden=false;button.setAttribute('aria-expanded','true');highlight(Math.max(0,options.findIndex(o=>o.value===select.value)));};
  const choose=i=>{
    if(!options[i]||options[i].disabled)return;
    select.value=options[i].value;select.dispatchEvent(new Event('change',{bubbles:true}));close();button.focus();
  };
  function render(){
    options=Array.from(select.options);value.textContent=select.selectedOptions[0]?.textContent||'Choose an option';button.disabled=select.disabled;
    list.replaceChildren();
    options.forEach((option,i)=>{
      const item=document.createElement('div');item.role='option';item.id=list.id+'-'+i;item.textContent=option.textContent;item.setAttribute('aria-selected',String(option.selected));item.setAttribute('aria-disabled',String(option.disabled));
      item.addEventListener('pointerdown',event=>event.preventDefault());item.addEventListener('click',()=>choose(i));list.append(item);
    });
  }
  button.addEventListener('click',()=>list.hidden?open():close());
  button.addEventListener('keydown',event=>{
    if(['ArrowDown','ArrowUp','Home','End','Enter',' '].includes(event.key)){
      event.preventDefault();const wasOpen=!list.hidden;if(!wasOpen)open();
      if(event.key==='ArrowDown'&&wasOpen)highlight(active+1);
      else if(event.key==='ArrowUp'&&wasOpen)highlight(active-1);
      else if(event.key==='Home')highlight(0);
      else if(event.key==='End')highlight(options.length-1);
      else if(wasOpen&&['Enter',' '].includes(event.key))choose(active);
    }else if(event.key==='Escape'){event.preventDefault();close();}
    else if(event.key==='Tab')close();
    else if(event.key.length===1&&!event.ctrlKey&&!event.metaKey&&!event.altKey){
      const now=Date.now();typeahead=(now-typeaheadAt>700?'':typeahead)+event.key.toLowerCase();typeaheadAt=now;
      if(list.hidden)open();const match=options.findIndex(o=>o.textContent.toLowerCase().startsWith(typeahead));if(match>=0)highlight(match);
    }
  });
  document.addEventListener('pointerdown',event=>{if(!wrapper.contains(event.target))close();});
  wrapper.addEventListener('focusout',event=>{if(!wrapper.contains(event.relatedTarget))close();});
  select.addEventListener('change',render);
  new MutationObserver(()=>{close();render();}).observe(select,{childList:true,subtree:true,attributes:true});
  render();
});
