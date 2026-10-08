import React from 'react';
import { ShieldAlert, Heart, Activity } from 'lucide-react';

export const Footer = () => {
  return (
    <footer style={{
      backgroundColor: 'var(--bg-surface)',
      borderTop: '1px solid var(--border-light)',
      padding: '40px 0 24px',
      marginTop: 'auto',
    }}>
      <div className="container">
        {/* Medical disclaimer alert banner */}
        <div style={{
          backgroundColor: '#f1f5f9',
          borderLeft: '4px solid #64748b',
          borderRadius: 'var(--radius-md)',
          padding: '16px 20px',
          marginBottom: '32px',
          display: 'flex',
          gap: '14px',
          alignItems: 'flex-start',
        }}>
          <ShieldAlert size={22} style={{ color: '#475569', flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h4 style={{ fontSize: '13px', fontWeight: '700', color: '#1e293b', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
              Veterinary Clinical Medical Notice & Disclaimer
            </h4>
            <p style={{ fontSize: '12px', color: '#475569', lineHeight: 1.5 }}>
              VetVision AI provides AI-assisted early-warning information and structured triage support for educational and veterinary-consultation preparation. 
              <strong> It does not provide a definitive veterinary medical diagnosis, prescribe pharmaceutical treatment, or replace comprehensive physical examination by a licensed veterinarian.</strong> 
              If your pet exhibits signs of acute distress, labored breathing, seizures, unresponsiveness, or trauma, contact a veterinary emergency hospital immediately.
            </p>
          </div>
        </div>

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
          paddingTop: '16px',
          borderTop: '1px solid var(--border-subtle)',
          fontSize: '13px',
          color: 'var(--text-muted)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={16} color="var(--primary)" />
            <span style={{ fontWeight: '600', color: 'var(--text-main)' }}>VetVision AI</span>
            <span>— University Innovation Day Healthcare Prototype</span>
          </div>

          <div style={{ display: 'flex', gap: '20px' }}>
            <span>Built with clean clinical triage standards</span>
            <span>Steps 1–6 Verified</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
