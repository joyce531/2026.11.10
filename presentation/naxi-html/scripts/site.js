(() => {
  const body = document.body;
  const fitCanvas = () => {
    body.style.setProperty('--fit', String(Math.min(window.innerWidth / 1600, window.innerHeight / 900)));
  };
  fitCanvas();
  window.addEventListener('resize', fitCanvas);
  document.querySelectorAll('[data-evidence]').forEach(slot => {
    if (slot.dataset.ready !== 'true' || !slot.dataset.src) return;
    const template = slot.querySelector('template');
    const img = template?.content.querySelector('img')?.cloneNode(true);
    if (!(img instanceof HTMLImageElement)) return;
    slot.append(img);
    img.addEventListener('load', () => {
      slot.classList.add('ready');
      slot.tabIndex = 0;
      slot.setAttribute('role', 'button');
      slot.setAttribute('aria-label', `放大查看：${img.alt}`);
    }, { once: true });
    img.addEventListener('error', () => {
      slot.classList.remove('ready');
      const note = slot.querySelector('.evidence-poster small');
      if (note) note.textContent = '截图无法读取，请检查文件后重新启用。';
    }, { once: true });
    img.src = slot.dataset.src;
    const open = () => {
      if (!slot.classList.contains('ready')) return;
      const dialog = document.createElement('dialog');
      dialog.className = 'evidence-lightbox';
      if (img.naturalHeight > img.naturalWidth * 1.6) dialog.classList.add('portrait');
      const full = document.createElement('img');
      full.src = img.src;
      full.alt = img.alt;
      const close = document.createElement('button');
      close.type = 'button';
      close.textContent = '关闭 ×';
      close.addEventListener('click', () => dialog.close());
      dialog.addEventListener('close', () => dialog.remove(), { once: true });
      dialog.append(full, close);
      document.body.append(dialog);
      dialog.showModal();
    };
    slot.addEventListener('click', open);
    slot.addEventListener('keydown', event => {
      if (event.key === 'Enter') { event.preventDefault(); open(); }
    });
  });
  document.querySelectorAll('.demo-switch').forEach(stage => {
    const tabs = [...stage.querySelectorAll('[role="tab"]')];
    const panels = [...stage.querySelectorAll('[role="tabpanel"]')];
    const select = index => {
      tabs.forEach((tab, i) => {
        tab.setAttribute('aria-selected', String(i === index));
        tab.tabIndex = i === index ? 0 : -1;
      });
      panels.forEach((panel, i) => {
        panel.hidden = i !== index;
        if (i !== index) panel.querySelector('video')?.pause();
      });
    };
    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => select(index));
      tab.addEventListener('keydown', event => {
        if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
        event.preventDefault();
        event.stopPropagation();
        const next = (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
        select(next);
        tabs[next].focus();
      });
    });
    select(0);
  });
  const fullButton = document.querySelector('[data-fullscreen]');
  fullButton?.addEventListener('click', () => {
    if (document.fullscreenElement) document.exitFullscreen?.();
    else document.documentElement.requestFullscreen?.();
  });
  document.addEventListener('keydown', event => {
    const target = event.target;
    if (target instanceof HTMLElement && (/^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName) || target.getAttribute('role') === 'tab')) return;
    if (event.key.toLowerCase() === 'f') {
      event.preventDefault();
      fullButton?.click();
      return;
    }
    if ((event.key === 'ArrowRight' || event.key === 'PageDown' || event.key === ' ') && body.dataset.next) {
      event.preventDefault();
      window.location.href = body.dataset.next;
    } else if ((event.key === 'ArrowLeft' || event.key === 'PageUp') && body.dataset.prev) {
      event.preventDefault();
      window.location.href = body.dataset.prev;
    }
  });
})();
