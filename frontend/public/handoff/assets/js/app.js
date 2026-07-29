
(function(){
  const root=document.documentElement;
  const themeBtn=document.querySelector('[data-theme-toggle]');
  function applyTheme(theme){
    root.setAttribute('data-theme',theme);
    if(themeBtn){themeBtn.textContent=theme==='dark'?'夜間':'日間';themeBtn.setAttribute('aria-pressed',theme==='dark'?'true':'false');}
  }
  applyTheme(localStorage.getItem('handoff-theme')||'light');
  if(themeBtn){themeBtn.addEventListener('click',()=>{const next=root.getAttribute('data-theme')==='dark'?'light':'dark';localStorage.setItem('handoff-theme',next);applyTheme(next);});}

  const topbar=document.querySelector('.topbar');
  function updateTopbarHeight(){ if(topbar){root.style.setProperty('--topbar-height',Math.ceil(topbar.getBoundingClientRect().height)+'px');} }
  updateTopbarHeight(); window.addEventListener('resize',updateTopbarHeight,{passive:true});
  if('ResizeObserver' in window && topbar){new ResizeObserver(updateTopbarHeight).observe(topbar);}

  const navToggle=document.querySelector('.nav-toggle');
  const nav=document.querySelector('.main-nav');
  if(navToggle&&nav){navToggle.addEventListener('click',()=>nav.classList.toggle('open'));}

  const tocLayout=document.querySelector('[data-toc-layout]');
  const pageToc=document.querySelector('[data-page-toc]');
  const collapseBtn=document.querySelector('[data-toc-collapse]');
  const expandBtn=document.querySelector('[data-toc-expand]');
  const mobileOpenBtn=document.querySelector('[data-toc-mobile-open]');
  const backdrop=document.querySelector('[data-toc-backdrop]');
  const tocLinks=[...document.querySelectorAll('.page-toc-link')];
  const mobileQuery=window.matchMedia('(max-width: 900px)');
  function isMobile(){return mobileQuery.matches;}
  function setDesktopCollapsed(collapsed){
    if(!tocLayout) return;
    localStorage.setItem('handoff-toc-collapsed',collapsed?'true':'false');
    syncTocState();
  }
  function syncTocState(){
    if(!tocLayout) return;
    const collapsed=localStorage.getItem('handoff-toc-collapsed')==='true';
    tocLayout.classList.toggle('toc-collapsed',collapsed && !isMobile());
    if(collapseBtn){collapseBtn.setAttribute('aria-expanded',collapsed && !isMobile()?'false':'true');collapseBtn.textContent=isMobile()?'關閉導覽':'收起導覽 ◀';collapseBtn.setAttribute('aria-label',isMobile()?'關閉本頁導覽':'收起本頁導覽');}
    if(expandBtn){expandBtn.setAttribute('aria-expanded',collapsed && !isMobile()?'false':'true');}
    if(mobileOpenBtn){mobileOpenBtn.setAttribute('aria-expanded',document.body.classList.contains('toc-drawer-open')?'true':'false');}
    updateTopbarHeight();
  }
  function openDrawer(){ if(!pageToc) return; document.body.classList.add('toc-drawer-open'); if(backdrop) backdrop.hidden=false; if(mobileOpenBtn) mobileOpenBtn.setAttribute('aria-expanded','true'); if(collapseBtn) collapseBtn.setAttribute('aria-expanded','true'); }
  function closeDrawer(){ document.body.classList.remove('toc-drawer-open'); if(backdrop) backdrop.hidden=true; if(mobileOpenBtn) mobileOpenBtn.setAttribute('aria-expanded','false'); }
  if(collapseBtn){collapseBtn.addEventListener('click',()=>{isMobile()?closeDrawer():setDesktopCollapsed(true);});}
  if(expandBtn){expandBtn.addEventListener('click',()=>setDesktopCollapsed(false));}
  if(mobileOpenBtn){mobileOpenBtn.addEventListener('click',()=>openDrawer());}
  if(backdrop){backdrop.addEventListener('click',()=>closeDrawer());}
  document.addEventListener('keydown',event=>{if(event.key==='Escape' && document.body.classList.contains('toc-drawer-open')) closeDrawer();});
  mobileQuery.addEventListener?.('change',()=>{closeDrawer();syncTocState();});
  syncTocState();

  function setActiveToc(id){
    tocLinks.forEach(link=>link.classList.toggle('active',link.getAttribute('href')==='#'+id));
  }
  const tocSections=tocLinks.map(link=>document.getElementById((link.getAttribute('href')||'').slice(1))).filter(Boolean);
  if(tocLinks.length && tocSections.length){
    setActiveToc(tocSections[0].id);
    tocLinks.forEach(link=>link.addEventListener('click',()=>{setActiveToc((link.getAttribute('href')||'').slice(1)); if(isMobile()) closeDrawer();}));
    if('IntersectionObserver' in window){
      const visible=new Map();
      const observer=new IntersectionObserver(entries=>{
        entries.forEach(entry=>{entry.isIntersecting?visible.set(entry.target.id,entry.boundingClientRect.top):visible.delete(entry.target.id);});
        if(visible.size){
          const active=[...visible.entries()].sort((a,b)=>Math.abs(a[1])-Math.abs(b[1]))[0][0];
          setActiveToc(active);
        }
      },{root:null,rootMargin:'-22% 0px -62% 0px',threshold:[0,0.12,0.35]});
      tocSections.forEach(section=>observer.observe(section));
    }
  }

  document.querySelectorAll('.copy-btn').forEach(btn=>{
    btn.addEventListener('click',async()=>{
      const code=btn.parentElement.querySelector('code')?.innerText||'';
      try{await navigator.clipboard.writeText(code);btn.textContent='已複製';setTimeout(()=>btn.textContent='複製',1200);}catch(e){btn.textContent='無法複製';}
    });
  });

  const origin=window.location.origin;
  const urlMap={handoff:origin+'/handoff/',handoffTools:origin+'/handoff/tools.html',dashboard:origin+'/dashboard',health:origin+'/api/health'};
  document.querySelectorAll('[data-url-template]').forEach(el=>{const key=el.getAttribute('data-url-template');if(urlMap[key]) el.textContent=urlMap[key];});

  const toolSearch=document.getElementById('toolSearch');
  const familyFilter=document.getElementById('familyFilter');
  const metricFilter=document.getElementById('metricFilter');
  const evidenceFilter=document.getElementById('evidenceFilter');
  const exposureFilter=document.getElementById('exposureFilter');
  const toolCards=[...document.querySelectorAll('[data-tool-card]')];
  function matchesList(value, selected){return !selected || (value||'').split('|').includes(selected)}
  function applyToolFilters(){
    const q=(toolSearch?.value||'').trim().toLowerCase();
    const fam=familyFilter?.value||''; const metric=metricFilter?.value||''; const evidence=evidenceFilter?.value||''; const exposure=exposureFilter?.value||'';
    toolCards.forEach(card=>{
      const text=card.innerText.toLowerCase();
      const show=(!q||text.includes(q)) && matchesList(card.dataset.families,fam) && matchesList(card.dataset.metrics,metric) && (!evidence||card.dataset.evidence===evidence) && (!exposure||card.dataset.exposure===exposure);
      card.classList.toggle('hidden',!show);
    });
  }
  [toolSearch,familyFilter,metricFilter,evidenceFilter,exposureFilter].forEach(el=>el&&el.addEventListener('input',applyToolFilters));

  const fileSearch=document.getElementById('fileSearch');
  const fileResults=document.getElementById('fileResults');
  const fileHint=document.getElementById('fileSearchHint');
  let fileRows=null;
  function flattenFileIndex(index){const rows=[];Object.entries(index||{}).forEach(([group,items])=>(items||[]).forEach(item=>rows.push({...item,group})));return rows;}
  function cleanList(items){return (items||[]).filter(Boolean).filter(v=>!String(v).startsWith('目前程式中未確認'));}
  function renderFileResults(q){
    if(!fileResults) return;
    if(!q || q.length<2){fileResults.innerHTML=''; if(fileHint) fileHint.textContent='輸入至少 2 個字後，才會在本頁用本地 JSON 顯示結果。'; return;}
    if(!fileRows){ if(fileHint) fileHint.textContent='正在載入本地索引...'; return; }
    const needle=q.toLowerCase();
    const matched=fileRows.filter(row=>[row.path,row.group,row.purpose,...(row.symbols||[]),...(row.tests||[]),...(row.sync||[])].join(' ').toLowerCase().includes(needle)).slice(0,40);
    if(fileHint) fileHint.textContent=matched.length?`顯示 ${matched.length} 筆結果；請輸入更精準關鍵字縮小範圍。`:'沒有符合結果。';
    fileResults.innerHTML=matched.map(row=>{const symbols=cleanList(row.symbols); const tests=cleanList(row.tests); const sync=cleanList(row.sync);return `<article class="file-result"><h3><code>${escapeHtml(row.path||'')}</code></h3><p>${escapeHtml(row.purpose||'')}</p><p><span class="status">${escapeHtml(row.group||'')}</span></p>${symbols.length?`<p><strong>主要 symbols：</strong>${symbols.map(v=>`<code>${escapeHtml(v)}</code>`).join(' ')}</p>`:''}${tests.length?`<p><strong>相關測試：</strong>${tests.map(v=>`<code>${escapeHtml(v)}</code>`).join(' ')}</p>`:''}${sync.length?`<p><strong>修改時同步：</strong>${sync.map(v=>`<code>${escapeHtml(v)}</code>`).join(' ')}</p>`:''}</article>`;}).join('');
  }
  function escapeHtml(value){return String(value).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));}
  if(fileSearch&&fileResults){
    fetch('assets/data/file-index.json').then(r=>r.json()).then(data=>{fileRows=flattenFileIndex(data); renderFileResults(fileSearch.value.trim());}).catch(()=>{if(fileHint) fileHint.textContent='本地索引載入失敗，請確認 assets/data/file-index.json 存在。';});
    fileSearch.addEventListener('input',()=>renderFileResults(fileSearch.value.trim()));
  }
})();
