// Shared site behavior and activity media slideshows.
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
    document.querySelectorAll('.lang button').forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.lang === l ? 'true' : 'false'); });
    document.querySelectorAll('[data-language]').forEach(function (el) { el.hidden = el.dataset.language !== l; });
    var translatedTitle = document.querySelector('[data-page-title-' + l + ']');
    if (translatedTitle) document.title = translatedTitle.getAttribute('data-page-title-' + l) + ' · 52 at 52';
    document.dispatchEvent(new CustomEvent('site:language', {detail: l}));
    loadComments(l);
  }
  window.setLang = applyLang;
  document.querySelectorAll('.lang button').forEach(function (b) { b.addEventListener('click', function () { applyLang(b.dataset.lang); }); });

  // Enhance existing generated YouTube links; no page rebuild is needed.
  function youtubeId(value) {
    try {
      var u = new URL(value), host = u.hostname.toLowerCase(), id = null;
      if (u.protocol !== 'https:') return null;
      if (host === 'youtu.be') id = u.pathname.split('/')[1];
      else if (['youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtube-nocookie.com', 'www.youtube-nocookie.com'].indexOf(host) !== -1) {
        if (u.pathname === '/watch') id = u.searchParams.get('v');
        else { var p = u.pathname.split('/'); if (['embed', 'shorts', 'live'].indexOf(p[1]) !== -1) id = p[2]; }
      }
      return /^[A-Za-z0-9_-]{11}$/.test(id || '') ? id : null;
    } catch (e) { return null; }
  }
  document.querySelectorAll('.activity-tile').forEach(function (tile) {
    var videos = [], seen = {};
    tile.querySelectorAll('.tile-links a').forEach(function (link) {
      var id = youtubeId(link.href);
      if (id && !seen[id]) { videos.push(id); seen[id] = true; }
    });
    if (!videos.length) return;
    var pt = !!tile.closest('[data-language=pt]');
    var show = tile.querySelector('[data-slideshow]');
    if (!show) {
      show = document.createElement('div'); show.className = 'slideshow'; show.setAttribute('data-slideshow', '');
      var slides = document.createElement('div'); slides.className = 'slides'; show.appendChild(slides);
      var header = tile.querySelector('.tile-head');
      if (header) header.insertAdjacentElement('afterend', show); else tile.prepend(show);
    }
    var track = show.querySelector('.slides');
    videos.forEach(function (id, i) {
      var figure = document.createElement('figure'); figure.dataset.videoId = id;
      figure.style.position = 'relative'; figure.style.minWidth = '0';
      var frame = document.createElement('iframe');
      frame.title = (pt ? 'Vídeo da atividade ' : 'Activity video ') + (i + 1);
      frame.style.cssText = 'width:100%;height:100%;border:0;display:block;min-width:0';
      frame.allow = 'accelerometer; encrypted-media; gyroscope; picture-in-picture; fullscreen';
      frame.allowFullscreen = true; frame.referrerPolicy = 'strict-origin-when-cross-origin';
      figure.appendChild(frame); track.appendChild(figure);
    });
    if (track.children.length > 1) {
      ['prev', 'next'].forEach(function (direction) {
        var button = show.querySelector('.' + direction);
        if (!button) { button = document.createElement('button'); button.type = 'button'; button.className = 'slide-btn ' + direction; button.textContent = direction === 'prev' ? '‹' : '›'; show.appendChild(button); }
        button.setAttribute('aria-label', direction === 'prev' ? (pt ? 'Mídia anterior' : 'Previous media') : (pt ? 'Próxima mídia' : 'Next media'));
        // Keep navigation below the player instead of covering its controls.
        button.style.top = 'auto'; button.style.bottom = '4px'; button.style.transform = 'none';
      });
      if (!show.querySelector('.slide-count')) { var count = document.createElement('span'); count.className = 'slide-count'; show.appendChild(count); }
    }
    show.style.paddingBottom = '52px';
    var counter = show.querySelector('.slide-count');
    if (counter) { counter.style.right = '50%'; counter.style.transform = 'translateX(50%)'; counter.style.bottom = '14px'; }
  });

  // Photos advance every 3 seconds; video slides wait for the visitor.
  var motionQuery = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
  document.querySelectorAll('[data-slideshow]').forEach(function (show) {
    var track = show.querySelector('.slides');
    if (!track || !track.children.length) return;
    var count = show.querySelector('.slide-count'), total = track.children.length;
    var delay = parseInt(show.dataset.interval || '3000', 10);
    var timer = null, visible = false, hovering = false, touching = false;
    function current() { return Math.max(0, Math.min(total - 1, Math.round(track.scrollLeft / Math.max(1, track.clientWidth)))); }
    function isVideo(i) { return !!track.children[i].dataset.videoId; }
    function stop() { clearTimeout(timer); timer = null; }
    function unloadVideos(except) {
      Array.prototype.forEach.call(track.children, function (slide, i) {
        var frame = slide.querySelector('iframe');
        // Unloading stops audio reliably, without a global YouTube API dependency.
        if (frame && i !== except && frame.hasAttribute('src')) frame.removeAttribute('src');
      });
    }
    function syncVideo() {
      var i = current();
      var active = visible && !document.hidden && !!show.getClientRects().length;
      unloadVideos(active ? i : -1);
      if (active && isVideo(i)) {
        var frame = track.children[i].querySelector('iframe');
        if (!frame.hasAttribute('src')) frame.src = 'https://www.youtube-nocookie.com/embed/' + track.children[i].dataset.videoId + '?autoplay=0&playsinline=1';
      }
      if (count) count.textContent = (i + 1) + ' / ' + total;
    }
    function start() {
      stop(); syncVideo();
      if (total > 1 && visible && !hovering && !touching && !show.contains(document.activeElement) && !(motionQuery && motionQuery.matches) && !document.hidden && show.getClientRects().length && !isVideo(current())) {
        timer = setTimeout(function () { go(current() + 1); }, delay);
      }
    }
    function go(i) {
      stop(); unloadVideos(-1);
      // Immediate snapping avoids loading a passing video during smooth scrolling.
      track.scrollTo({left: ((i + total) % total) * track.clientWidth, behavior: 'instant'});
      start();
    }
    var prev = show.querySelector('.prev'), next = show.querySelector('.next');
    if (prev) prev.addEventListener('click', function () { go(current() - 1); });
    if (next) next.addEventListener('click', function () { go(current() + 1); });
    track.addEventListener('scroll', start, {passive: true});
    show.addEventListener('mouseenter', function () { hovering = true; stop(); });
    show.addEventListener('mouseleave', function () { hovering = false; start(); });
    show.addEventListener('focusin', stop);
    show.addEventListener('focusout', function () { setTimeout(start, 0); });
    track.addEventListener('touchstart', function () { touching = true; stop(); }, {passive: true});
    function endTouch() { touching = false; start(); }
    track.addEventListener('touchend', endTouch, {passive: true});
    track.addEventListener('touchcancel', endTouch, {passive: true});
    document.addEventListener('visibilitychange', start);
    document.addEventListener('site:language', start);
    if (motionQuery && motionQuery.addEventListener) motionQuery.addEventListener('change', start);
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) { visible = entries[0].isIntersecting && entries[0].intersectionRatio >= 0.5; start(); }, {threshold: [0, 0.5]}).observe(show);
    } else { visible = true; start(); }
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
  if ('serviceWorker' in navigator && location.protocol === 'https:') {
    try { navigator.serviceWorker.register(new URL('sw.js', siteRoot)).catch(function () {}); } catch (e) {}
  }
  document.querySelectorAll('.sub-form').forEach(function (form) {
    var cfg = (window.SITE_CONFIG && window.SITE_CONFIG.subscribe) || {};
    var msg = form.parentElement.querySelector('.subscribe-msg');
    var input = form.querySelector('input[type=email]');
    input.name = 'email';
    if (!cfg.action) return;
    form.action = cfg.action; form.method = 'post'; form.target = '_blank';
    form.addEventListener('submit', function () {
      if (msg) msg.textContent = LANG === 'pt'
        ? 'Quase lá: confirme a inscrição na página do follow.it que abriu e depois no seu e-mail.'
        : 'Almost there: confirm on the follow.it page that just opened, then in your inbox.';
      setTimeout(function () { input.value = ''; }, 300);
    });
  });
  var slot = document.getElementById('giscus-slot');
  function loadComments(l) {
    if ((window.SITE_CONFIG?.comments || {}).provider !== 'giscus') return;
    slot = document.getElementById('giscus-slot');
    var g = (window.SITE_CONFIG || {}).giscus || {};
    if (!slot || !g.repoId || !g.categoryId) return;
    slot.innerHTML = '';
    var s = document.createElement('script');
    s.src = 'https://giscus.app/client.js'; s.async = true; s.crossOrigin = 'anonymous';
    Object.entries({repo: g.repo, 'repo-id': g.repoId, category: g.category, 'category-id': g.categoryId,
      mapping: 'specific', term: publicURL(), 'reactions-enabled': '1', 'input-position': 'top', theme: 'light',
      lang: l === 'pt' ? 'pt' : 'en', loading: 'lazy'
    }).forEach(function (kv) { s.setAttribute('data-' + kv[0], kv[1]); });
    slot.appendChild(s);
  }
  window.loadComments = loadComments;
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
      fallback.hidden = false; input.value = publicURL(); input.focus(); input.select();
      say('Select and copy the link below.', 'Selecione e copie o link abaixo.');
    }
    async function copyLink() {
      try {
        if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('Clipboard unavailable');
        await navigator.clipboard.writeText(publicURL()); fallback.hidden = true;
        say('Link copied. Ready to share!', 'Link copiado. Pronto para compartilhar!');
      } catch (e) { manualCopy(); }
    }
    sharing.querySelector('[data-copy]').addEventListener('click', copyLink);
    sharing.querySelector('[data-share]').addEventListener('click', async function () {
      if (!navigator.share) { await copyLink(); return; }
      try {
        await navigator.share({title: document.title, url: publicURL()});
        say('Thanks for sharing!', 'Obrigado por compartilhar!');
      } catch (e) { if (e.name !== 'AbortError') await copyLink(); }
    });
  }
  var initial = (navigator.language || '').toLowerCase().startsWith('pt') ? 'pt' : 'en';
  applyLang(initial);
})();
