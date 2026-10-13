// VetVision AI — Clinical Healthcare Progressive Web App Service Worker
// Version: 2.1.0

const CACHE_NAME = 'vetvision-v2.1';

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

// Installation: Pre-cache static app shell and activate immediately
self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('VetVision PWA precache partial warning:', err);
      });
    })
  );
});

// Activation: Clean up all old versions of the static cache and claim clients
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

// Fetch Interceptor: Security, Privacy, and Robust Caching Protocols
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // RULE 0: Never intercept Vite dev server URLs, hot module reloads, or WebSockets
  if (
    url.pathname.startsWith('/@') ||
    url.pathname.startsWith('/src/') ||
    url.pathname.includes('node_modules') ||
    url.search.includes('t=') ||
    url.search.includes('import') ||
    url.protocol === 'ws:' ||
    url.protocol === 'wss:'
  ) {
    return;
  }

  // RULE 1: Never intercept or cache non-GET requests (POST, PUT, DELETE, PATCH)
  if (request.method !== 'GET') {
    return;
  }

  // RULE 2: STRICT PRIVACY & CLINICAL SAFETY:
  // Never cache API responses, private health records, assessment submissions,
  // authentication flows, Groq AI guidance, or doctor reviews.
  if (url.pathname.startsWith('/api') || url.pathname.includes('/api/v1')) {
    return;
  }

  // RULE 3: HTML Navigation Requests (Page transitions & deep links)
  // Use Network-First strategy so users always get the freshest deployment,
  // with fallback to cached /index.html, and a styled fallback if offline.
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
        .catch(async () => {
          const cached = (await caches.match('/index.html')) || (await caches.match('/'));
          if (cached) {
            return cached;
          }
          // Valid styled HTML response — NEVER return undefined/null
          return new Response(
            `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VetVision AI — Reconnecting</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #0f172a; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 1.5rem; box-sizing: border-box; text-align: center; }
    .card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 2.5rem 2rem; max-width: 440px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    h1 { color: #0d9488; font-size: 1.5rem; margin-top: 0; }
    p { color: #64748b; font-size: 0.95rem; line-height: 1.5; }
    button { background: #0d9488; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 0.95rem; margin-top: 1rem; }
    button:hover { background: #0f766e; }
  </style>
</head>
<body>
  <div class="card">
    <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🩺</div>
    <h1>VetVision AI</h1>
    <p>The application is offline or the server connection is initializing. Please click retry once the server is available.</p>
    <button onclick="window.location.reload()">Retry Connection</button>
  </div>
</body>
</html>`,
            { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
          );
        })
    );
    return;
  }

  // RULE 4: Static Bundles & Assets (JS, CSS, Images, Fonts)
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
        if (cachedResponse) {
          // Stale-while-revalidate: return cached instantly, update in background if available
          fetch(request)
            .then((networkResponse) => {
              if (networkResponse && networkResponse.status === 200) {
                const responseClone = networkResponse.clone();
                caches.open(CACHE_NAME).then((cache) => {
                  cache.put(request, responseClone);
                });
              }
            })
            .catch(() => {});
          return cachedResponse;
        }

        // Cache miss: fetch from network and cache for next time
        return fetch(request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return networkResponse;
        });
      })
    );
  }
});

// Allow client pages to trigger immediate activation
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
