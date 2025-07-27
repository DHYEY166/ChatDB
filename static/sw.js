// ChatDB Service Worker
const CACHE_NAME = 'chatdb-v1.0.0';

// Install event
self.addEventListener('install', event => {
  console.log('Service Worker installed');
});

// Fetch event
self.addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request).catch(() => {
      return new Response('Offline content not available');
    })
  );
}); 