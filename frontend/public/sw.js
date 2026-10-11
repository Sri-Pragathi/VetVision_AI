// VetVision AI — Clinical Healthcare Progressive Web App Service Worker
// Version: 1.0.0

const CACHE_NAME = 'vetvision-static-v1';

// Static application shell assets to pre-cache on install
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/manifest.webmanifest',
  '/favicon.svg',
  '/icons/apple-touch-icon.png',
  '/icons/pwa-192x192.png',
  '/icons/pwa-512x512.png',
  '/icons/pwa-maskable-512x512.png',
];

// Installation: Pre-cache static app shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Activation: Clean up old versions of the static cache and claim clients
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((name) => {
          if (name !== CACHE_NAME) {
            return caches.delete(name);
          }
          return null;
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch Interceptor: Security and Caching Protocols
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // RULE 1: Never intercept or cache non-GET requests (POST, PUT, DELETE, PATCH)
  if (request.method !== 'GET') {
    return;
  }

  // RULE 2: STRICT PRIVACY & CLINICAL SAFETY:
  // Never cache API responses, private health records, assessment submissions,
  // authentication flows, Groq AI guidance, or doctor reviews.
  // Bypass the service worker cache entirely and go to network.
  if (url.pathname.startsWith('/api') || url.pathname.includes('/api/v1')) {
    return;
  }

  // RULE 3: HTML Navigation Requests (Page transitions & deep links)
  // Use Network-First strategy so users always get the freshest deployment,
  // with fallback to cached /index.html if completely offline.
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response && response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put('/index.html', responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          return caches.match('/index.html');
        })
    );
    return;
  }

  // RULE 4: Static Bundles & Assets (JS, CSS, Images, Fonts)
  // Vite generates content-hashed assets in /assets/ (*.js, *.css).
  // Use Stale-While-Revalidate for instant loading + background update.
  const isStaticAsset =
    url.pathname.startsWith('/assets/') ||
    url.pathname.startsWith('/icons/') ||
    url.pathname.endsWith('.svg') ||
    url.pathname.endsWith('.png') ||
    url.pathname.endsWith('.css') ||
    url.pathname.endsWith('.js') ||
    url.hostname.includes('fonts.googleapis.com') ||
    url.hostname.includes('fonts.gstatic.com');

  if (isStaticAsset) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        const fetchPromise = fetch(request)
          .then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              const responseClone = networkResponse.clone();
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(request, responseClone);
              });
            }
            return networkResponse;
          })
          .catch(() => null);

        return cachedResponse || fetchPromise;
      })
    );
  }
});

// Allow client pages to trigger immediate activation upon user confirmation
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
