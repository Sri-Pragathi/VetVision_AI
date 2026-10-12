// VetVision AI — Service Worker Registration Helper

export function registerServiceWorker() {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return;
  }

  // During local development (Vite dev server), unregister any active service worker
  // to prevent stale caching of dynamic ES modules or HMR disruption.
  if (import.meta.env.DEV) {
    navigator.serviceWorker.getRegistrations().then((registrations) => {
      for (const reg of registrations) {
        reg.unregister();
      }
    });
    return;
  }

  // In production builds, register the service worker for reliable PWA capabilities
  window.addEventListener('load', () => {
    const swUrl = '/sw.js';

    navigator.serviceWorker
      .register(swUrl)
      .then((registration) => {
        // Check for updates on every page load
        registration.update().catch(() => {});

        registration.onupdatefound = () => {
          const installingWorker = registration.installing;
          if (installingWorker == null) {
            return;
          }

          installingWorker.onstatechange = () => {
            if (installingWorker.state === 'installed') {
              if (navigator.serviceWorker.controller) {
                // If a new worker is installed, activate it immediately
                installingWorker.postMessage({ type: 'SKIP_WAITING' });
                window.dispatchEvent(
                  new CustomEvent('vetvision_pwa_update_available', {
                    detail: { registration },
                  })
                );
              } else {
                window.dispatchEvent(new CustomEvent('vetvision_pwa_cached'));
              }
            }
          };
        };
      })
      .catch((error) => {
        console.warn('VetVision AI Service Worker registration failed:', error);
      });

    // Handle controller change (reloads automatically once new service worker activates)
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (!refreshing) {
        refreshing = true;
        window.location.reload();
      }
    });
  });
}

export function unregisterServiceWorker() {
  if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then((registration) => {
        registration.unregister();
      })
      .catch((error) => {
        console.error(error.message);
      });
  }
}
