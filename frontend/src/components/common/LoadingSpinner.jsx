import React from 'react';
import { Activity } from 'lucide-react';

export const LoadingSpinner = ({ label = 'Loading clinical data...', fullScreen = false }) => {
  const content = (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '12px',
      padding: '32px',
      color: 'var(--text-muted)',
    }}>
      <div style={{
        position: 'relative',
        width: '48px',
        height: '48px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <div style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          border: '3px solid var(--primary-border)',
          borderTopColor: 'var(--primary)',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }} />
        <Activity size={20} color="var(--primary)" />
      </div>
      {label && <p style={{ fontSize: '14px', fontWeight: '500' }}>{label}</p>}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );

  if (fullScreen) {
    return (
      <div style={{
        minHeight: '60vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        {content}
      </div>
    );
  }

  return content;
};

export default LoadingSpinner;
