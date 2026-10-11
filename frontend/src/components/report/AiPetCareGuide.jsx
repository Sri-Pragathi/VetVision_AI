import React, { useState } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  AlertOctagon,
  AlertTriangle,
  Clock,
  HeartPulse,
  PhoneCall,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Info,
  CheckCircle2,
  XCircle,
  Eye,
  HelpCircle,
} from 'lucide-react';

export default function AiPetCareGuide({ careGuide, petName, riskLevel }) {
  const [showHelplineDetails, setShowHelplineDetails] = useState(false);

  if (!careGuide) {
    return null;
  }

  const scenario_title = careGuide.title || careGuide.scenario_title || 'Supportive Pet Care';
  const intro_summary = careGuide.subtitle || careGuide.intro_summary || 'Careful supportive care and monitoring are recommended.';
  const rawTier = careGuide.urgency?.classification || careGuide.triage_urgency_level || riskLevel || 'HOME_MONITORING';
  const currentTier = String(rawTier).toUpperCase().includes('EMERGENCY')
    ? 'EMERGENCY'
    : String(rawTier).toUpperCase().includes('URGENT')
    ? 'URGENT'
    : String(rawTier).toUpperCase().includes('APPOINTMENT')
    ? 'APPOINTMENT'
    : 'HOME_MONITORING';

  const rawWhatToDo = careGuide.section_a_what_to_do_now || careGuide.what_to_do_now || [];
  const what_to_do_now = rawWhatToDo.map((item, idx) => ({
    title: item.title || `Measure #${idx + 1}`,
    detail: item.instruction || item.detail || '',
    badge: item.badge || (item.is_critical ? 'CRITICAL' : `STEP ${item.step || idx + 1}`),
  }));

  const rawWhatNotToDo = careGuide.section_b_what_to_avoid || careGuide.what_not_to_do || [];
  const what_not_to_do = rawWhatNotToDo.map((item) => ({
    warning: item.rule || item.warning || '',
    reason: item.detail || item.reason || '',
  }));

  const rawWhatToMonitor = careGuide.section_c_what_to_monitor || careGuide.what_to_monitor || [];
  const what_to_monitor = rawWhatToMonitor.map((item) =>
    typeof item === 'object'
      ? {
          indicator: item.indicator || item.name || 'Vital Sign',
          red_flag: item.red_flag || item.cutoff || 'Sudden worsening or change',
        }
      : {
          indicator: 'Health Indicator',
          red_flag: String(item),
        }
  );

  const when_to_seek_care = careGuide.section_d_when_to_seek_care || careGuide.when_to_seek_care || {};
  const tiers = when_to_seek_care.tiers || {
    EMERGENCY: when_to_seek_care.cutoff_instruction || 'Seek immediate 24/7 emergency veterinary care.',
    URGENT: 'Same-day veterinary evaluation recommended.',
    APPOINTMENT: 'Book an appointment within 24 to 48 hours.',
    HOME_MONITORING: when_to_seek_care.action_recommendation || 'Continue close supportive monitoring at home.',
  };
  const redFlags = when_to_seek_care.emergency_escalation_criteria || when_to_seek_care.critical_red_flags || [];

  const why_guidance_shown = careGuide.section_e_why_shown || careGuide.why_guidance_shown || {};
  const primaryReasons = (why_guidance_shown.rationale_factors || why_guidance_shown.primary_reasons || []).map((r) =>
    typeof r === 'object' ? `${r.category}: ${r.finding} (${r.impact})` : String(r)
  );
  const visualVsReported = why_guidance_shown.visual_vs_reported || '';
  const uncertainties = why_guidance_shown.uncertainty_and_missing_data || why_guidance_shown.uncertainty_notes || [];

  const tierStyles = {
    EMERGENCY: {
      border: '2px solid #ef4444',
      bg: '#fef2f2',
      badgeBg: '#dc2626',
      badgeText: '#ffffff',
      label: 'Emergency — Immediate Care (Do Not Wait)',
    },
    URGENT: {
      border: '2px solid #f97316',
      bg: '#fff7ed',
      badgeBg: '#ea580c',
      badgeText: '#ffffff',
      label: 'Urgent — Same-Day Veterinary Evaluation',
    },
    APPOINTMENT: {
      border: '2px solid #0284c7',
      bg: '#f0f9ff',
      badgeBg: '#0284c7',
      badgeText: '#ffffff',
      label: 'Appointment Recommended (Within 24–48 Hours)',
    },
    HOME_MONITORING: {
      border: '2px solid #10b981',
      bg: '#f0fdf4',
      badgeBg: '#059669',
      badgeText: '#ffffff',
      label: 'Home Monitoring (Stable — Re-evaluate If Symptoms Persist)',
    },
  };

  const activeStyle = tierStyles[currentTier] || tierStyles.HOME_MONITORING;

  return (
    <div
      id="ai-pet-care-guide"
      style={{
        borderRadius: '16px',
        backgroundColor: '#ffffff',
        border: '2px solid #0284c7',
        boxShadow: '0 10px 25px -5px rgba(2, 132, 199, 0.1), 0 8px 10px -6px rgba(2, 132, 199, 0.05)',
        marginBottom: '2.5rem',
        overflow: 'hidden',
      }}
    >
      {/* Header Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #0369a1 0%, #0284c7 100%)',
          color: '#ffffff',
          padding: '1.5rem 1.75rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div
            style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <HeartPulse size={26} color="#ffffff" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0, color: '#ffffff' }}>
              🐾 AI Pet Care Guide & Safety Precautions
            </h2>
            <p style={{ margin: '0.25rem 0 0', fontSize: '0.85rem', color: '#e0f2fe' }}>
              Understand what you can safely do now, what to avoid, and when {petName || 'your pet'} needs urgent veterinary care.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
          <span
            style={{
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
              color: '#ffffff',
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '0.35rem 0.75rem',
              borderRadius: '20px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            Scenario: {scenario_title}
          </span>
          <span
            style={{
              backgroundColor: activeStyle.badgeBg,
              color: activeStyle.badgeText,
              fontSize: '0.8rem',
              fontWeight: 800,
              padding: '0.4rem 0.85rem',
              borderRadius: '20px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.15)',
            }}
          >
            {currentTier}
          </span>
        </div>
      </div>

      <div style={{ padding: '1.75rem' }}>
        {/* Intro Context Card */}
        <div
          style={{
            backgroundColor: '#f8fafc',
            borderLeft: '4px solid #0284c7',
            padding: '1rem 1.25rem',
            borderRadius: '8px',
            marginBottom: '1.75rem',
            fontSize: '0.925rem',
            lineHeight: 1.5,
            color: '#1e293b',
          }}
        >
          <strong>Immediate Assessment Summary:</strong> {intro_summary}
        </div>

        {/* Section A: What to Do Now */}
        <div style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.85rem' }}>
            <ShieldCheck size={20} color="#059669" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0, color: '#065f46' }}>
              A. What to Do Now (First-Aid & Low-Risk Comfort Measures)
            </h3>
          </div>
          <p style={{ fontSize: '0.825rem', color: '#64748b', margin: '0 0 1rem 0' }}>
            Safe supportive measures you can immediately take at home while monitoring or preparing for a veterinary consult.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
            {what_to_do_now.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: '1rem 1.15rem',
                  borderRadius: '10px',
                  backgroundColor: '#f0fdf4',
                  border: '1px solid #bbf7d0',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#166534' }}>{item.title}</span>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      fontWeight: 800,
                      backgroundColor: '#dcfce7',
                      color: '#15803d',
                      padding: '0.15rem 0.5rem',
                      borderRadius: '12px',
                    }}
                  >
                    {item.badge || 'SAFE'}
                  </span>
                </div>
                <div style={{ fontSize: '0.85rem', color: '#1e293b', lineHeight: 1.45 }}>{item.detail}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Section B: What NOT to Do (Strict Contraindications) */}
        <div
          style={{
            marginBottom: '2rem',
            padding: '1.25rem 1.5rem',
            borderRadius: '12px',
            backgroundColor: '#fef2f2',
            border: '2px solid #f87171',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <AlertOctagon size={22} color="#dc2626" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0, color: '#991b1b' }}>
              B. What NOT to Do (Strict Precautions & Harm Prevention)
            </h3>
          </div>
          <p style={{ fontSize: '0.825rem', color: '#b91c1c', margin: '0 0 1rem 0', fontWeight: 500 }}>
            Never perform these actions. Well-intentioned home remedies can cause acute toxicity, internal bleeding, or asphyxiation.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {what_not_to_do.map((item, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.75rem',
                  backgroundColor: '#ffffff',
                  padding: '0.85rem 1rem',
                  borderRadius: '8px',
                  border: '1px solid #fecaca',
                }}
              >
                <XCircle size={18} color="#dc2626" style={{ marginTop: '0.15rem', flexShrink: 0 }} />
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.875rem', color: '#991b1b' }}>{item.warning}</div>
                  <div style={{ fontSize: '0.8rem', color: '#7f1d1d', marginTop: '0.2rem', lineHeight: 1.4 }}>
                    <strong>Why:</strong> {item.reason}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Section C: What to Monitor */}
        <div style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.85rem' }}>
            <Eye size={20} color="#ea580c" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0, color: '#9a3412' }}>
              C. What to Monitor (Objective Warning Signs & Deterioration Indicators)
            </h3>
          </div>
          <p style={{ fontSize: '0.825rem', color: '#64748b', margin: '0 0 1rem 0' }}>
            Check these signs every 1–2 hours. Any red-flag shift requires immediate escalation to an emergency veterinarian.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
            {what_to_monitor.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: '1rem 1.15rem',
                  borderRadius: '10px',
                  backgroundColor: '#fff7ed',
                  border: '1px solid #fed7aa',
                }}
              >
                <div style={{ fontWeight: 700, fontSize: '0.875rem', color: '#c2410c', marginBottom: '0.35rem' }}>
                  {item.indicator}
                </div>
                <div style={{ fontSize: '0.825rem', color: '#7c2d12', lineHeight: 1.4 }}>
                  <span style={{ fontWeight: 700, color: '#ea580c' }}>🚩 Red Flag: </span>
                  {item.red_flag}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Section D: When to Seek Veterinary Care */}
        <div style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.85rem' }}>
            <Clock size={20} color="#0369a1" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0, color: '#075985' }}>
              D. When to Seek Veterinary Care (4-Tier Decision Matrix)
            </h3>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '0.85rem', marginBottom: '1.25rem' }}>
            {['EMERGENCY', 'URGENT', 'APPOINTMENT', 'HOME_MONITORING'].map((tierKey) => {
              const isCurrent = currentTier === tierKey;
              const style = tierStyles[tierKey];
              const desc = tiers[tierKey] || '';

              return (
                <div
                  key={tierKey}
                  style={{
                    padding: '1rem',
                    borderRadius: '10px',
                    border: isCurrent ? style.border : '1px solid #e2e8f0',
                    backgroundColor: isCurrent ? style.bg : '#f8fafc',
                    boxShadow: isCurrent ? '0 4px 12px rgba(0,0,0,0.06)' : 'none',
                    position: 'relative',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                    <span
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: 800,
                        color: isCurrent ? style.badgeBg : '#64748b',
                        textTransform: 'uppercase',
                      }}
                    >
                      {tierKey}
                    </span>
                    {isCurrent && (
                      <span
                        style={{
                          fontSize: '0.65rem',
                          fontWeight: 800,
                          backgroundColor: style.badgeBg,
                          color: '#ffffff',
                          padding: '0.15rem 0.45rem',
                          borderRadius: '10px',
                        }}
                      >
                        CURRENT ADVICE
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: isCurrent ? '#0f172a' : '#475569', lineHeight: 1.45, fontWeight: isCurrent ? 500 : 400 }}>
                    {desc}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Red Flag Symptoms Box */}
          {redFlags.length > 0 && (
            <div
              style={{
                backgroundColor: '#fff1f2',
                borderLeft: '4px solid #e11d48',
                padding: '1rem 1.25rem',
                borderRadius: '8px',
              }}
            >
              <div style={{ fontWeight: 800, fontSize: '0.85rem', color: '#be123c', marginBottom: '0.4rem' }}>
                🚨 Critical Red-Flag Triggers (Seek Emergency Care Immediately If Any Appear):
              </div>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.825rem', color: '#881337', lineHeight: 1.5 }}>
                {redFlags.map((flag, idx) => (
                  <li key={idx}>{flag}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Section E: Why This Guidance Is Shown */}
        <div
          style={{
            marginBottom: '2rem',
            padding: '1.25rem 1.5rem',
            borderRadius: '12px',
            backgroundColor: '#f8fafc',
            border: '1px solid #cbd5e1',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <HelpCircle size={20} color="#475569" />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0, color: '#334155' }}>
              E. Why This Guidance Is Shown (Transparent Clinical Rationale)
            </h3>
          </div>

          <div style={{ fontSize: '0.85rem', color: '#1e293b', marginBottom: '0.75rem' }}>
            <strong>Synthesized Clinical Factors:</strong>
            <ul style={{ margin: '0.35rem 0 0', paddingLeft: '1.25rem', color: '#475569', lineHeight: 1.45 }}>
              {primaryReasons.map((reason, idx) => (
                <li key={idx}>{reason}</li>
              ))}
            </ul>
          </div>

          {visualVsReported && (
            <div style={{ fontSize: '0.825rem', color: '#475569', marginBottom: '0.75rem', lineHeight: 1.45 }}>
              <strong>Visual vs. Reported Correlation:</strong> {visualVsReported}
            </div>
          )}

          {uncertainties.length > 0 && (
            <div
              style={{
                backgroundColor: '#fffbeb',
                border: '1px solid #fef3c7',
                borderRadius: '8px',
                padding: '0.85rem 1rem',
                fontSize: '0.8rem',
                color: '#92400e',
              }}
            >
              <strong>Clinical Uncertainty & Missing Information:</strong>
              <ul style={{ margin: '0.35rem 0 0', paddingLeft: '1.25rem', lineHeight: 1.45 }}>
                {uncertainties.map((u, idx) => (
                  <li key={idx}>{u}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Night, Weekend & Holiday Veterinary Emergency Contacts */}
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderRadius: '12px',
            backgroundColor: '#eff6ff',
            border: '1px solid #bfdbfe',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <PhoneCall size={20} color="#1d4ed8" />
              <div>
                <h4 style={{ margin: 0, fontSize: '0.975rem', fontWeight: 800, color: '#1e40af' }}>
                  🌙 Night, Weekend & Holiday Emergency Veterinary Resources
                </h4>
                <p style={{ margin: '0.15rem 0 0', fontSize: '0.8rem', color: '#3b82f6' }}>
                  Verified 24/7 toxicological and hospital resources when your regular clinic is closed.
                </p>
              </div>
            </div>

            <button
              onClick={() => setShowHelplineDetails(!showHelplineDetails)}
              className="btn btn-outline btn-sm"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.35rem',
                borderColor: '#93c5fd',
                color: '#1d4ed8',
                backgroundColor: '#ffffff',
              }}
            >
              {showHelplineDetails ? (
                <>
                  Hide Numbers <ChevronUp size={14} />
                </>
              ) : (
                <>
                  View Helplines & Clinics <ChevronDown size={14} />
                </>
              )}
            </button>
          </div>

          {showHelplineDetails && (
            <div
              style={{
                marginTop: '1.25rem',
                paddingTop: '1rem',
                borderTop: '1px solid #dbeafe',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                gap: '1rem',
                fontSize: '0.85rem',
              }}
            >
              <div
                style={{
                  backgroundColor: '#ffffff',
                  padding: '1rem',
                  borderRadius: '8px',
                  border: '1px solid #bfdbfe',
                }}
              >
                <div style={{ fontWeight: 800, color: '#1e3a8a', marginBottom: '0.25rem' }}>
                  ASPCA Animal Poison Control Center (APCC)
                </div>
                <div style={{ color: '#1d4ed8', fontWeight: 700, fontSize: '1rem', marginBottom: '0.25rem' }}>
                  (888) 426-4435
                </div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                  Available 24 hours a day, 365 days a year. Consultation fee may apply.
                </div>
              </div>

              <div
                style={{
                  backgroundColor: '#ffffff',
                  padding: '1rem',
                  borderRadius: '8px',
                  border: '1px solid #bfdbfe',
                }}
              >
                <div style={{ fontWeight: 800, color: '#1e3a8a', marginBottom: '0.25rem' }}>
                  Pet Poison Helpline
                </div>
                <div style={{ color: '#1d4ed8', fontWeight: 700, fontSize: '1rem', marginBottom: '0.25rem' }}>
                  (855) 764-7661
                </div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                  24/7 animal poison control service for pet owners and veterinarians.
                </div>
              </div>

              <div
                style={{
                  backgroundColor: '#ffffff',
                  padding: '1rem',
                  borderRadius: '8px',
                  border: '1px solid #bfdbfe',
                }}
              >
                <div style={{ fontWeight: 800, color: '#1e3a8a', marginBottom: '0.25rem' }}>
                  AAHA Accredited Hospital Locator
                </div>
                <a
                  href="https://www.aaha.org/your-pet/find-a-hospital/"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    color: '#2563eb',
                    fontWeight: 700,
                    textDecoration: 'none',
                    marginTop: '0.25rem',
                  }}
                >
                  Locate 24/7 Emergency Clinics <ExternalLink size={14} />
                </a>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
                  Search accredited emergency pet hospitals near your postal code.
                </div>
              </div>

              <div
                style={{
                  gridColumn: '1 / -1',
                  backgroundColor: '#fef3c7',
                  border: '1px solid #fde68a',
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  color: '#92400e',
                  fontSize: '0.8rem',
                }}
              >
                🚨 <strong>Transport Safety Tip:</strong> Always phone the emergency clinic while in transit so their staff can prepare an intake stretcher, oxygen, or immediate triage bay before you arrive. Keep your pet gently wrapped and calm.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
