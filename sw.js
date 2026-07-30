const CACHE_NAME = 'fkc-academy-v1';
const urlsToCache = [
  '/fkc-trading-academy/',
  '/fkc-trading-academy/index.html',
  '/fkc-trading-academy/manifest.json',
  '/fkc-trading-academy/icon-192.png',
  '/fkc-trading-academy/icon-512.png'
];

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        return response || fetch(event.request);
      })
  );
});
