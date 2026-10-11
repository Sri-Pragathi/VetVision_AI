import React, { useState, useEffect } from 'react';
import { WifiOff, RefreshCw, Sparkles, X } from 'lucide-react';

export default function PwaStatusBanner() {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [waitingWorker, setWaitingWorker] = useState(null);
  const [dismissedOffline, setDismissedOffline] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setDismissedOffline(false);
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    const handleUpdateAvailable = (e) => {
      setUpdateAvailable(true);
      if (e.detail?.registration?.waiting) {
        setWaitingWorker(e.detail.registration.waiting);
      }
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    window.addEventListener('vetvision_pwa_update_available', handleUpdateAvailable);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('vetvision_pwa_update_available', handleUpdateAvailable);
    };
  }, []);

  const handleApplyUpdate = () => {
    if (waitingWorker) {
      waitingWorker.postMessage({ type: 'SKIP_WAITING' });
    } else {
      window.location.reload();
    }
  };

  const handleRetryConnection = () => {
    if (navigator.onLine) {
      setIsOnline(true);
    } else {
      // Small pulse effect to acknowledge click
      setDismissedOffline(false);
    }
  };

  // If online and no update, render nothing
  if (isOnline && !updateAvailable) {
    return null;
  }

  return (
    <>
      {/* Offline Alert Banner */}
      {!isOnline && !dismissedOffline && (
        <div
          role="status"
          aria-live="polite"
          style={{
            backgroundColor: '#fffbeb',
            borderBottom: '1px solid #fde68a',
            padding: '10px 20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '13px',
            color: '#92400e',
            zIndex: 9999,
            position: 'sticky',
            top: 0,
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <WifiOff size={16} color="#d97706" />
            <span>
              <strong>Offline Mode:</strong> You are disconnected. Core pages are accessible, but clinical triage, AI guidance, and assessment saving require an active internet connection.
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={handleRetryConnection}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 10px',
                borderRadius: '6px',
                border: '1px solid #d97706',
                backgroundColor: '#ffffff',
                color: '#92400e',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <RefreshCw size={12} />
              <span>Retry</span>
            </button>
            <button
              onClick={() => setDismissedOffline(true)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#b45309',
                cursor: 'pointer',
                padding: '4px',
              }}
              title="Dismiss banner"
            >
              <X size={14} />
            </button>
          </div>
        </div>
      )}

      {/* PWA Update Ready Banner */}
      {updateAvailable && (
        <div
          role="status"
          style={{
            backgroundColor: '#f0fdfa',
            borderBottom: '1px solid #99f6e4',
            padding: '10px 20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '13px',
            color: '#0f766e',
            zIndex: 9999,
            position: 'sticky',
            top: !isOnline && !dismissedOffline ? '42px' : 0,
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={16} color="#0d9488" />
            <span>
              <strong>Update Ready:</strong> A new version of VetVision AI has been downloaded in the background.
            </span>
          </div>

          <button
            onClick={handleApplyUpdate}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '5px 12px',
              borderRadius: '6px',
              backgroundColor: '#0d9488',
              color: '#ffffff',
              border: 'none',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={13} />
            <span>Reload & Update</span>
          </button>
        </div>
      )}
    </>
  );
}
