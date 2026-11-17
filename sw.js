const CACHE_NAME = "amichat-v1";

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.add("/"))
  );
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", event => {
  if (event.request.method === "GET" &&
      new URL(event.request.url).origin === self.location.origin) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match("/"))
    );
  }
});

