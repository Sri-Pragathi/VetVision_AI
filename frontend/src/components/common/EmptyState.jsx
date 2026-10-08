import React from 'react';
import { FolderOpen } from 'lucide-react';

export const EmptyState = ({
  icon: Icon = FolderOpen,
  title = 'No records found',
  description = 'There are no active records in this section yet.',
  actionLabel,
  onAction,
}) => {
  return (
    <div style={{
      padding: '48px 24px',
      textAlign: 'center',
      backgroundColor: 'var(--bg-surface)',
      border: '1px dashed var(--border-light)',
      borderRadius: 'var(--radius-lg)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      margin: '20px 0',
    }}>
      <div style={{
        width: '54px',
        height: '54px',
        borderRadius: 'var(--radius-full)',
        backgroundColor: 'var(--bg-muted)',
        color: 'var(--text-muted)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '16px',
      }}>
        <Icon size={26} strokeWidth={1.5} />
      </div>
      <h3 style={{ fontSize: '17px', fontWeight: '700', color: 'var(--text-main)', marginBottom: '6px' }}>
        {title}
      </h3>
      <p style={{ fontSize: '14px', color: 'var(--text-muted)', maxWidth: '420px', marginBottom: actionLabel ? '20px' : 0 }}>
        {description}
      </p>

      {actionLabel && onAction && (
        <button onClick={onAction} className="btn btn-primary">
          {actionLabel}
        </button>
      )}
    </div>
  );
};

export default EmptyState;
