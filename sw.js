// Service worker: offline support for the app shell.
// Cache-first for static assets, network-first for data (so new weeks show up).
var CACHE = '52at52-logo-6d060f936c50cd2c-season-two-autoplay-v4';
var PRECACHE = [
  './', 'index.html', 'tips.html', 'reviews.html', 'summaries/index.html', 'summaries/season-two/index.html',
  'assets/brand-shield.png', 'assets/style.css', 'assets/app.js', 'assets/config.js',
  'assets/comments.js', 'assets/comments.css', 'assets/comment-policy.js',
  'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png'
];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(PRECACHE); }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener('fetch', function (e) {
  if (e.request.method !== 'GET') return;
  var url = new URL(e.request.url);
  if (url.origin !== location.origin) return; // let comments/videos cross-origin pass through
  var isData = e.request.mode === 'navigate' || url.pathname.endsWith('.html') ||
    url.pathname.endsWith('.js') || url.pathname.endsWith('.css') ||
    url.pathname.indexOf('/data/') > -1 || url.pathname.indexOf('/media/') > -1;

  if (isData) {
    // Network first, fall back to cache when offline
    e.respondWith(fetch(e.request).then(function (r) {
      var copy = r.clone();
      caches.open(CACHE).then(function (c) { c.put(e.request, copy); });
      return r;
    }).catch(function () { return caches.match(e.request); }));
  } else {
    // Cache first for the app shell
    e.respondWith(caches.match(e.request).then(function (hit) {
      return hit || fetch(e.request).then(function (r) {
        var copy = r.clone();
        caches.open(CACHE).then(function (c) { c.put(e.request, copy); });
        return r;
      });
    }));
  }
});
