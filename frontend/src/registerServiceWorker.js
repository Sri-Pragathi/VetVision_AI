// VetVision AI — Service Worker Registration Helper

export function registerServiceWorker() {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return;
  }

  // Register when page has finished loading
  window.addEventListener('load', () => {
    const swUrl = '/sw.js';

    navigator.serviceWorker
      .register(swUrl)
      .then((registration) => {
        // Registration successful
        registration.onupdatefound = () => {
          const installingWorker = registration.installing;
          if (installingWorker == null) {
            return;
          }

          installingWorker.onstatechange = () => {
            if (installingWorker.state === 'installed') {
              if (navigator.serviceWorker.controller) {
                // New content is available; notify user
                window.dispatchEvent(new CustomEvent('vetvision_pwa_update_available', {
                  detail: { registration },
                }));
              } else {
                // Content cached for offline use
                window.dispatchEvent(new CustomEvent('vetvision_pwa_cached'));
              }
            }
          };
        };
      })
      .catch((error) => {
        // Silently log or handle non-fatal registration failures (e.g. in non-HTTPS local testing)
        console.warn('VetVision AI Service Worker registration failed:', error);
      });

    // Handle controller change (reloads on update activation)
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
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then((registration) => {
        registration.unregister();
      })
      .catch((error) => {
        console.error(error.message);
      });
  }
}
