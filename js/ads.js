(function () {
  const config = window.AD_CONFIG || {};
  const slots = config.slots || {};

  function loadAdsense(client) {
    if (!client || document.querySelector('script[data-ad-client-loader]')) return;
    if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') return;
    const script = document.createElement('script');
    script.async = true;
    script.crossOrigin = 'anonymous';
    script.setAttribute('data-ad-client-loader', 'true');
    script.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=' + encodeURIComponent(client);
    document.head.appendChild(script);
  }

  function hideUnfilledSlots() {
    document.querySelectorAll('.ad-slot').forEach(el => {
      const frame = el.querySelector('iframe');
      const ins = el.querySelector('ins.adsbygoogle');
      if (!frame || !ins || ins.clientHeight < 24) el.classList.add('ad-pending');
    });
  }

  function fillSlot(el) {
    if (!config.enabled || config.provider !== 'adsense' || !config.client) {
      el.classList.add('ad-pending');
      return;
    }
    const key = el.dataset.adKey || 'inline';
    const slotId = slots[key] || '';
    if (!slotId) {
      el.classList.add('ad-pending');
      return;
    }
    el.innerHTML = '';
    const ins = document.createElement('ins');
    ins.className = 'adsbygoogle';
    ins.style.display = 'block';
    ins.dataset.adClient = config.client;
    if (slotId) ins.dataset.adSlot = slotId;
    ins.dataset.adFormat = 'auto';
    ins.dataset.fullWidthResponsive = 'true';
    el.appendChild(ins);
    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch (e) {
      console.warn('AdSense push failed', e);
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
      document.querySelectorAll('.ad-slot').forEach(el => { el.style.display = 'none'; });
      return;
    }
    if (config.enabled && config.provider === 'adsense') loadAdsense(config.client);
    document.querySelectorAll('.ad-slot').forEach(fillSlot);
    setTimeout(hideUnfilledSlots, 2200);
    setTimeout(hideUnfilledSlots, 5200);
  });
})();
