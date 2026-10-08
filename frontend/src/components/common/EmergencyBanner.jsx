import React from 'react';
import { AlertOctagon, PhoneCall } from 'lucide-react';

export const EmergencyBanner = ({ message, triggers = [] }) => {
  return (
    <div style={{
      backgroundColor: '#fef2f2',
      border: '2px solid #ef4444',
      borderRadius: 'var(--radius-lg)',
      padding: '24px',
      margin: '20px 0',
      boxShadow: '0 8px 16px rgba(239, 68, 68, 0.12)',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
        <div style={{
          backgroundColor: '#dc2626',
          color: '#ffffff',
          borderRadius: 'var(--radius-md)',
          padding: '10px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}>
          <AlertOctagon size={28} strokeWidth={2.5} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{
              backgroundColor: '#dc2626',
              color: '#ffffff',
              fontSize: '11px',
              fontWeight: '800',
              padding: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              letterSpacing: '0.05em',
              textTransform: 'uppercase',
            }}>
              Acute Triage Flag
            </span>
            <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#991b1b' }}>
              Immediate Emergency Veterinary Attention Recommended
            </h3>
          </div>

          <p style={{ fontSize: '14px', color: '#b91c1c', marginBottom: '12px', lineHeight: 1.5 }}>
            {message || 'Critical physiological or symptom indicators have been detected. Do not wait for a routine consultation — seek care at the nearest veterinary emergency hospital immediately.'}
          </p>

          {triggers.length > 0 && (
            <div style={{
              backgroundColor: '#fee2e2',
              borderRadius: 'var(--radius-sm)',
              padding: '12px 14px',
              marginBottom: '14px',
            }}>
              <strong style={{ fontSize: '12px', color: '#991b1b', textTransform: 'uppercase', letterSpacing: '0.03em', display: 'block', marginBottom: '6px' }}>
                Emergency Trigger Factors:
              </strong>
              <ul style={{ paddingLeft: '18px', margin: 0, fontSize: '13px', color: '#7f1d1d' }}>
                {triggers.map((t, idx) => (
                  <li key={idx} style={{ marginBottom: '2px' }}>{t}</li>
                ))}
              </ul>
            </div>
          )}

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            fontWeight: '600',
            color: '#991b1b',
          }}>
            <PhoneCall size={16} />
            <span>Transport your pet safely and alert the emergency hospital en route.</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmergencyBanner;
