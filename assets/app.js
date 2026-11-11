// Shared: language (browser-detected, not saved), nav highlight, PWA install, subscribe form, comments
(function () {
  'use strict';
  var LANG = 'en';
  var appScript = document.currentScript;
  var siteRoot = new URL('../', appScript.src);

  function applyLang(l) {
    LANG = l;
    document.documentElement.lang = l === 'pt' ? 'pt-BR' : 'en';
    document.querySelectorAll('.txt').forEach(function (el) {
      var t = el.getAttribute('data-' + l);
      if (t !== null && t !== '') el.innerHTML = t;
    });
    document.querySelectorAll('.lang button').forEach(function (b) {
      b.setAttribute('aria-pressed', b.dataset.lang === l ? 'true' : 'false');
    });
    document.querySelectorAll('[data-language]').forEach(function (el) {
      el.hidden = el.dataset.language !== l;
    });
    var translatedTitle = document.querySelector('[data-page-title-' + l + ']');
    if (translatedTitle) document.title = translatedTitle.getAttribute('data-page-title-' + l) + ' · 52 at 52';
    document.dispatchEvent(new CustomEvent('site:language', {detail: l}));
    loadComments(l); // reload comments in the new language
  }
  window.setLang = applyLang;

  document.querySelectorAll('.lang button').forEach(function (b) {
    b.addEventListener('click', function () { applyLang(b.dataset.lang); });
  });

  // Photo slideshows on week pages (one per activity tile)
  document.querySelectorAll('[data-slideshow]').forEach(function (show) {
    var track = show.querySelector('.slides');
    var count = show.querySelector('.slide-count');
    var total = track.children.length;
    function current() { return Math.round(track.scrollLeft / Math.max(1, track.clientWidth)); }
    function go(i) { track.scrollTo({left: ((i + total) % total) * track.clientWidth}); }
    var prev = show.querySelector('.prev'), next = show.querySelector('.next');
    if (prev) prev.addEventListener('click', function () { go(current() - 1); });
    if (next) next.addEventListener('click', function () { go(current() + 1); });
    track.addEventListener('scroll', function () { if (count) count.textContent = (current() + 1) + ' / ' + total; }, {passive: true});
  });

  // Navigation highlight
  var path = location.pathname.replace(siteRoot.pathname, '');
  document.querySelectorAll('.topbar nav a.site-link').forEach(function (a) {
    var target = new URL(a.href).pathname.replace(siteRoot.pathname, '');
    if (target === path || (target === 'tips.html' && path.startsWith('tips/')) ||
        (target === 'summaries/index.html' && path.startsWith('summaries/')) ||
        (target === 'reviews.html' && path.startsWith('reviews/')) ||
        (target === 'weeks/index.html' && /^(weeks|activities)\//.test(path))) a.classList.add('active');
  });

  // PWA: register service worker (best effort)
  if ('serviceWorker' in navigator && location.protocol === 'https:') {
    try { navigator.serviceWorker.register(new URL('sw.js', siteRoot)).catch(function () {}); } catch (e) {}
  }

  // Subscribe form (free service endpoint configured in config.js)
  var form = document.getElementById('subscribe-form');
  if (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var cfg = (window.SITE_CONFIG && window.SITE_CONFIG.subscribe) || {};
      var email = form.querySelector('input[type=email]').value.trim();
      var msg = document.getElementById('subscribe-msg');
      if (!email) return;
      if (!cfg.endpoint) {
        msg.textContent = cfg.setupNoteEn || 'Subscriptions will be enabled once the free mailing service is configured.';
        return;
      }
      fetch(cfg.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({ email: email })
      }).then(function () {
        msg.textContent = { en: 'Subscribed! Check your inbox to confirm.', pt: 'Inscrito! Confirme no seu e-mail.' }[LANG];
      }).catch(function () {
        msg.textContent = { en: 'Something went wrong — please try again.', pt: 'Algo deu errado — tente novamente.' }[LANG];
      });
    });
  }

  // Comments (giscus) — only on pages that have the slot
  var slot = document.getElementById('giscus-slot');
  function loadComments(l) {
    if ((window.SITE_CONFIG?.comments || {}).provider !== "giscus") return;
    slot = document.getElementById('giscus-slot');
    var g = (window.SITE_CONFIG || {}).giscus || {};
    if (!slot || !g.repoId || !g.categoryId) return;
    slot.innerHTML = '';
    var s = document.createElement('script');
    s.src = 'https://giscus.app/client.js'; s.async = true; s.crossOrigin = 'anonymous';
    Object.entries({
      repo: g.repo, 'repo-id': g.repoId, category: g.category, 'category-id': g.categoryId,
      mapping: 'specific', term: publicURL(), 'reactions-enabled': '1', 'input-position': 'top', theme: 'light',
      lang: l === 'pt' ? 'pt' : 'en', loading: 'lazy'
    }).forEach(function (kv) { s.setAttribute('data-' + kv[0], kv[1]); });
    slot.appendChild(s);
  }
  window.loadComments = loadComments;

  // Permanent public URL, independent of preview URLs or selected language.
  function publicURL() {
    var canonical = document.querySelector('link[rel="canonical"]');
    return canonical ? canonical.href : location.href.split('#')[0];
  }
  var firstSection = document.querySelector('main section');
  if (firstSection) {
    var sharing = document.createElement('div');
    sharing.className = 'page-share';
    sharing.innerHTML =
      '<div class="share-actions"><button type="button" class="share-button" data-share>' +
      '<span class="txt" data-en="Share this page" data-pt="Compartilhar esta página">Share this page</span></button>' +
      '<button type="button" class="copy-button" data-copy>' +
      '<span class="txt" data-en="Copy link" data-pt="Copiar link">Copy link</span></button></div>' +
      '<p class="share-status muted" role="status" aria-live="polite"></p>' +
      '<div class="share-fallback" hidden><label class="txt" data-en="Page link (select and copy)" ' +
      'data-pt="Link da página (selecione e copie)">Page link (select and copy)</label>' +
      '<input readonly type="url" aria-label="Page link"></div>';
    firstSection.prepend(sharing);
    var status = sharing.querySelector('.share-status');
    var fallback = sharing.querySelector('.share-fallback');
    var input = fallback.querySelector('input');
    function say(en, pt) { status.textContent = LANG === 'pt' ? pt : en; }
    function manualCopy() {
      fallback.hidden = false;
      input.value = publicURL();
      input.focus();
      input.select();
      say('Select and copy the link below.', 'Selecione e copie o link abaixo.');
    }
    async function copyLink() {
      try {
        if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('Clipboard unavailable');
        await navigator.clipboard.writeText(publicURL());
        fallback.hidden = true;
        say('Link copied. Ready to share!', 'Link copiado. Pronto para compartilhar!');
      } catch (e) { manualCopy(); }
    }
    sharing.querySelector('[data-copy]').addEventListener('click', copyLink);
    sharing.querySelector('[data-share]').addEventListener('click', async function () {
      if (!navigator.share) { await copyLink(); return; }
      try {
        await navigator.share({title: document.title, url: publicURL()});
        say('Thanks for sharing!', 'Obrigado por compartilhar!');
      } catch (e) {
        if (e.name !== 'AbortError') await copyLink();
      }
    });
  }

  // Initial language from the browser (not saved)
  var initial = (navigator.language || '').toLowerCase().startsWith('pt') ? 'pt' : 'en';
  applyLang(initial);
})();
