(()=>{
  const nav=document.querySelector('[data-site-nav]');
  if(!nav)return;
  const menu=nav.querySelector('.navlinks');
  const toggle=nav.querySelector('.nav-toggle');
  const links=[...menu.querySelectorAll('a')];
  const sectionLinks=links.filter(link=>link.dataset.section);
  const sections=sectionLinks.map(link=>document.getElementById(link.dataset.section)).filter(Boolean);

  function setActive(link){
    links.forEach(item=>{
      const active=item===link;
      item.classList.toggle('active',active);
      if(active)item.setAttribute('aria-current','page');
      else item.removeAttribute('aria-current');
    });
  }

  function closeMenu(){
    menu.classList.remove('open');
    toggle.setAttribute('aria-expanded','false');
  }

  if(/(?:^|\/)dictionary\.html$/.test(location.pathname)){
    setActive(links.find(link=>link.dataset.page==='dictionary'));
  }else{
    let queued=false;
    const updateActiveSection=()=>{
      queued=false;
      const marker=window.scrollY+nav.offsetHeight+120;
      let current=sectionLinks[0];
      sections.forEach(section=>{
        if(section.offsetTop<=marker){
          current=sectionLinks.find(link=>link.dataset.section===section.id)||current;
        }
      });
      setActive(current);
    };
    const queueUpdate=()=>{
      if(queued)return;
      queued=true;
      requestAnimationFrame(updateActiveSection);
    };
    const activateHash=()=>{
      const id=location.hash.slice(1);
      const hashLink=sectionLinks.find(link=>link.dataset.section===id);
      if(!hashLink)return false;
      setActive(hashLink);
      return true;
    };
    addEventListener('scroll',queueUpdate,{passive:true});
    addEventListener('hashchange',()=>{if(!activateHash())queueUpdate();});
    addEventListener('pageshow',()=>{if(!activateHash())queueUpdate();});
    if(!activateHash())queueUpdate();
  }

  toggle.addEventListener('click',()=>{
    const open=!menu.classList.contains('open');
    menu.classList.toggle('open',open);
    toggle.setAttribute('aria-expanded',String(open));
  });
  links.forEach(link=>link.addEventListener('click',closeMenu));
  document.addEventListener('click',event=>{if(!nav.contains(event.target))closeMenu();});
  document.addEventListener('keydown',event=>{if(event.key==='Escape')closeMenu();});
})();
