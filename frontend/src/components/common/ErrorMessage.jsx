import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export const ErrorMessage = ({ message, onRetry }) => {
  return (
    <div style={{
      backgroundColor: '#fef2f2',
      border: '1px solid #fecaca',
      borderRadius: 'var(--radius-md)',
      padding: '16px 20px',
      margin: '16px 0',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '16px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <AlertTriangle size={20} color="#dc2626" style={{ flexShrink: 0 }} />
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#991b1b', marginBottom: '2px' }}>
            Action Required
          </h4>
          <p style={{ fontSize: '13px', color: '#b91c1c' }}>
            {message || 'Unable to load clinical records. Please verify connection and try again.'}
          </p>
        </div>
      </div>

      {onRetry && (
        <button 
          onClick={onRetry}
          className="btn btn-sm btn-secondary"
          style={{ borderColor: '#fca5a5', color: '#991b1b', flexShrink: 0 }}
        >
          <RefreshCw size={14} />
          Retry
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;
