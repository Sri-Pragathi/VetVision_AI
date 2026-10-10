import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  FileText,
  ArrowLeft,
  Printer,
  Copy,
  Check,
  AlertTriangle,
  Activity,
  Calendar,
  Clock,
  ExternalLink,
  ShieldAlert,
  Info,
  ChevronRight,
  Eye,
  Camera,
  CheckCircle2,
} from 'lucide-react';
import { reportApi } from '../api/reportApi';
import { API_BASE_URL } from '../api/client';
import TriageBadge from '../components/common/TriageBadge';
import EmergencyBanner from '../components/common/EmergencyBanner';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

export default function ReportViewerPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copiedHandoff, setCopiedHandoff] = useState(false);

  useEffect(() => {
    fetchReport();
  }, [id]);

  const fetchReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await reportApi.getReport(id);
      setReport(res.data || res);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load veterinary report.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyHandoff = () => {
    if (!report) return;
    const rd = report.report_data || {};
    const handoff = rd.veterinary_handoff || {};
    const pet = rd.pet_profile || {};
    const risk = rd.risk_analysis || {};
    const emergency = rd.emergency_evaluation || {};

    const textToCopy = `--- VETVISION AI CLINICAL HANDOFF SUMMARY ---
PATIENT: ${handoff.patient || pet.name || 'Pet'}
SPECIES/BREED: ${pet.species || 'Unknown'} - ${pet.breed || 'Unknown'} (Age: ${pet.age_display || 'Unknown'})
TRIAGE ASSESSMENT: ${risk.risk_level || 'UNKNOWN'} (Risk Score: ${risk.risk_score != null ? `${risk.risk_score}/100` : 'N/A'})
EMERGENCY STATUS: ${emergency.status || (emergency.is_emergency ? 'CRITICAL EMERGENCY' : 'Standard Monitoring')}

PRIMARY COMPLAINTS / REPORTED SYMPTOMS:
${(handoff.reported_symptoms || []).map((s) => `• ${s}`).join('\n') || 'None recorded'}

CLINICAL OBSERVATIONS:
${handoff.clinical_observations_summary || 'None recorded'}

ADAPTIVE Q&A FINDINGS:
${(handoff.relevant_follow_up_findings || []).map((f) => `• ${f}`).join('\n') || 'None recorded'}

COMPUTER VISION INSPECTION:
${(handoff.image_observations || []).map((img) => `• ${img}`).join('\n') || 'No distinct image abnormalities'}

RECOMMENDED ACTION:
${rd.recommendations?.primary_action || risk.recommendation || 'Consult your licensed veterinarian.'}

REPORT ID: ${report.id} (Version ${report.report_version || 1})
TIMESTAMP: ${report.generated_at ? new Date(report.generated_at).toUTCString() : 'Recorded'}
DISCLAIMER: VetVision AI is an AI-assisted triage and early-warning tool, not a definitive veterinary diagnosis.
--------------------------------------------`;

    navigator.clipboard.writeText(textToCopy);
    setCopiedHandoff(true);
    setTimeout(() => setCopiedHandoff(false), 2500);
  };

  const handlePrint = () => {
    window.print();
  };

  const handleViewHtml = () => {
    window.open(`${API_BASE_URL}/reports/${id}/html`, '_blank');
  };

  if (loading) {
    return (
      <div className="container" style={{ padding: '4rem 1rem' }}>
        <LoadingSpinner message="Retrieving veterinary clinical report snapshot..." />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="container" style={{ padding: '3rem 1rem' }}>
        <ErrorMessage message={error || 'Report not found.'} onRetry={fetchReport} />
        <button
          onClick={() => navigate('/dashboard')}
          className="btn btn-outline"
          style={{ marginTop: '1rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <ArrowLeft size={16} /> Return to Dashboard
        </button>
      </div>
    );
  }

  const rd = report.report_data || {};
  const pet = rd.pet_profile || {};
  const symptoms = rd.reported_symptoms || [];
  const followUp = rd.adaptive_follow_up_findings || [];
  const observations = rd.clinical_observations || {};
  const images = rd.image_analysis || [];
  const risk = rd.risk_analysis || {};
  const explainability = rd.explainability || [];
  const emergency = rd.emergency_evaluation || {};
  const recommendations = rd.recommendations || {};
  const qualityWarnings = rd.data_quality_warnings || risk.data_quality_warnings || rd.risk_analysis?.factor_breakdown?.data_quality_warnings || [];
  const structuredFactors = rd.structured_factors || risk.structured_factors || rd.risk_analysis?.factor_breakdown?.structured_factors || [];

  const isEmergency = Boolean(risk.is_emergency || emergency.is_emergency);

  return (
    <div style={{ backgroundColor: 'var(--color-bg)', minHeight: 'calc(100vh - 140px)', padding: '2rem 0 4rem' }}>
      <div className="container">
        {/* Navigation & Header Actions */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
          <button
            onClick={() => navigate(-1)}
            className="btn btn-outline btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <ArrowLeft size={16} /> Back
          </button>

          <div style={{ display: 'flex', gap: '0.6rem' }}>
            <button
              onClick={handleCopyHandoff}
              className="btn btn-outline btn-sm"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                backgroundColor: copiedHandoff ? 'rgba(16, 185, 129, 0.1)' : 'white',
                color: copiedHandoff ? 'var(--color-success)' : 'var(--color-text-main)',
                borderColor: copiedHandoff ? 'var(--color-success)' : 'var(--color-border)',
              }}
            >
              {copiedHandoff ? <Check size={15} /> : <Copy size={15} />}
              {copiedHandoff ? 'Handoff Copied!' : 'Copy Handoff Summary'}
            </button>

            <button
              onClick={handlePrint}
              className="btn btn-outline btn-sm"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <Printer size={15} /> Print Report
            </button>

            <button
              onClick={handleViewHtml}
              className="btn btn-primary btn-sm"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <ExternalLink size={15} /> Full HTML Format
            </button>
          </div>
        </div>

        {/* Emergency Alert Banner */}
        {isEmergency && (
          <div style={{ marginBottom: '1.5rem' }}>
            <EmergencyBanner
              message={emergency.status || 'Critical clinical indicators identified. Immediate veterinary medical attention recommended.'}
            />
          </div>
        )}

        {/* Data Quality & Uncertainty Notices */}
        {qualityWarnings && qualityWarnings.length > 0 && (
          <div
            style={{
              marginBottom: '1.5rem',
              padding: '1rem 1.25rem',
              borderRadius: 'var(--radius-md)',
              backgroundColor: '#fffbeb',
              border: '1px solid #fde68a',
            }}
          >
            <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#92400e', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span>⚠️</span> Clinical Evidence Quality & Uncertainty Notices
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              {qualityWarnings.map((w, wIdx) => (
                <div key={wIdx} style={{ fontSize: '0.825rem', color: '#78350f', lineHeight: 1.4 }}>
                  <strong>{w.title}:</strong> {w.message}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Report Master Container */}
        <div
          className="card"
          style={{
            padding: '2.5rem',
            backgroundColor: 'white',
            boxShadow: 'var(--shadow-md)',
            border: '1px solid var(--color-border)',
          }}
        >
          {/* Official Document Header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '1.5rem',
              paddingBottom: '2rem',
              borderBottom: '2px solid var(--color-border)',
              marginBottom: '2rem',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                <div
                  style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '10px',
                    backgroundColor: 'var(--color-primary-light)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--color-primary)',
                  }}
                >
                  <Activity size={24} />
                </div>
                <div>
                  <h1 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: 'var(--color-text-main)' }}>
                    VetVision AI Clinical Summary Report
                  </h1>
                  <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                    Intelligent Health Risk & Triage Assessment
                  </span>
                </div>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                <span><strong>Report ID:</strong> {report.id}</span>
                <span><strong>Version:</strong> v{report.report_version || 1}</span>
                <span><strong>Status:</strong> {report.report_status || 'GENERATED'}</span>
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ marginBottom: '0.5rem' }}>
                <TriageBadge level={risk.risk_level} />
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                Generated: {report.generated_at ? new Date(report.generated_at).toLocaleString() : 'Recent'}
              </div>
            </div>
          </div>

          {/* Section 1: Patient Demographic Card */}
          <div
            style={{
              padding: '1.25rem 1.5rem',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              marginBottom: '2rem',
            }}
          >
            <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 1rem 0', color: 'var(--color-primary)' }}>
              1. Patient Demographics & Profile
            </h2>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '1rem',
                fontSize: '0.875rem',
              }}
            >
              <div><strong>Patient Name:</strong> {pet.name || 'Unknown'}</div>
              <div><strong>Species:</strong> {pet.species || 'Unknown'}</div>
              <div><strong>Breed:</strong> {pet.breed || 'Not specified'}</div>
              <div><strong>Age:</strong> {pet.age_display || 'Not specified'}</div>
              <div><strong>Sex / Altered:</strong> {pet.sex || 'Not specified'}</div>
              <div><strong>Weight:</strong> {pet.weight != null ? `${pet.weight} kg` : 'Not specified'}</div>
              <div><strong>Known Allergies:</strong> {pet.allergies || 'None reported'}</div>
              <div><strong>Chronic Conditions:</strong> {pet.existing_conditions || 'None reported'}</div>
            </div>
          </div>

          {/* Section 2: Triage & Risk Score Breakdown */}
          <div style={{ marginBottom: '2rem' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 1rem 0', color: 'var(--color-primary)' }}>
              2. Clinical Triage & Risk Evaluation
            </h2>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                gap: '1.25rem',
              }}
            >
              <div
                style={{
                  padding: '1.25rem',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                }}
              >
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                  Determined Triage Level
                </div>
                <div style={{ marginTop: '0.5rem' }}>
                  <TriageBadge level={risk.risk_level} />
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>
                  Action Urgency: <strong>{emergency.action_urgency || 'Standard Evaluation'}</strong>
                </div>
              </div>

              <div
                style={{
                  padding: '1.25rem',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                }}
              >
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                  Calculated Risk Score
                </div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--color-text-main)', marginTop: '0.25rem' }}>
                  {risk.risk_score != null ? `${risk.risk_score}` : 'N/A'}{' '}
                  <span style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)', fontWeight: 500 }}>/ 100</span>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
                  Engine: {risk.engine_version || 'v1.0 (Rule-based)'}
                </div>
              </div>

              <div
                style={{
                  padding: '1.25rem',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                }}
              >
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                  Emergency Hard-Stop Status
                </div>
                <div
                  style={{
                    fontSize: '1.1rem',
                    fontWeight: 700,
                    marginTop: '0.5rem',
                    color: isEmergency ? 'var(--color-danger)' : 'var(--color-success)',
                  }}
                >
                  {isEmergency ? '⚠️ CRITICAL / EMERGENCY' : '✓ Normal Triage Protocol'}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
                  {emergency.status}
                </div>
              </div>
            </div>
          </div>

          {/* Section 3: Reported Symptoms Table */}
          <div style={{ marginBottom: '2rem' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 1rem 0', color: 'var(--color-primary)' }}>
              3. Reported Symptoms & Chronicity
            </h2>
            {symptoms.length === 0 ? (
              <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>No specific symptoms logged.</p>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                  <thead>
                    <tr style={{ backgroundColor: 'var(--color-surface)', textAlign: 'left' }}>
                      <th style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--color-border)' }}>Symptom</th>
                      <th style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--color-border)' }}>Category</th>
                      <th style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--color-border)' }}>Severity</th>
                      <th style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--color-border)' }}>Duration</th>
                      <th style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--color-border)' }}>Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {symptoms.map((s, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid var(--color-border)' }}>
                        <td style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>{s.name}</td>
                        <td style={{ padding: '0.75rem 1rem', color: 'var(--color-text-muted)', textTransform: 'capitalize' }}>
                          {s.category || 'General'}
                        </td>
                        <td style={{ padding: '0.75rem 1rem' }}>
                          <span
                            style={{
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              textTransform: 'uppercase',
                              padding: '0.2rem 0.5rem',
                              borderRadius: 'var(--radius-sm)',
                              backgroundColor:
                                s.severity === 'severe'
                                  ? 'rgba(239, 68, 68, 0.15)'
                                  : s.severity === 'moderate'
                                  ? 'rgba(234, 88, 12, 0.15)'
                                  : 'rgba(59, 130, 246, 0.15)',
                              color:
                                s.severity === 'severe'
                                  ? 'var(--color-danger)'
                                  : s.severity === 'moderate'
                                  ? 'var(--color-warning)'
                                  : 'var(--color-info)',
                            }}
                          >
                            {s.severity}
                          </span>
                        </td>
                        <td style={{ padding: '0.75rem 1rem' }}>{s.duration_display || s.duration || 'Not specified'}</td>
                        <td style={{ padding: '0.75rem 1rem', color: 'var(--color-text-muted)' }}>{s.notes || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Section 4: Adaptive Q&A & Clinical Observations */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '1.5rem',
              marginBottom: '2rem',
            }}
          >
            {/* Adaptive Q&A */}
            <div>
              <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 1rem 0', color: 'var(--color-primary)' }}>
                4. Adaptive Follow-Up Inquiry
              </h2>
              <div
                style={{
                  padding: '1.25rem',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  fontSize: '0.85rem',
                }}
              >
                {followUp.length === 0 ? (
                  <p style={{ color: 'var(--color-text-muted)', margin: 0 }}>No dynamic questions answered.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {followUp.map((item, idx) => (
                      <div key={idx} style={{ borderBottom: idx < followUp.length - 1 ? '1px solid var(--color-border)' : 'none', paddingBottom: '0.5rem' }}>
                        <div style={{ fontWeight: 600, color: 'var(--color-text-main)' }}>{item.question}</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.2rem' }}>
                          <span style={{ color: 'var(--color-primary)', fontWeight: 600 }}>Answer:</span>
                          <span>{item.answer}</span>
                          {item.triggered_emergency && (
                            <span style={{ fontSize: '0.7rem', color: 'var(--color-danger)', fontWeight: 700 }}>⚠️ Critical Response</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Observations Matrix */}
            <div>
              <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 1rem 0', color: 'var(--color-primary)' }}>
                5. Clinical Observations
              </h2>
              <div
                style={{
                  padding: '1.25rem',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  fontSize: '0.85rem',
                }}
              >
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div><strong>Appetite:</strong> <span style={{ textTransform: 'capitalize' }}>{observations.appetite || 'Not recorded'}</span></div>
                  <div><strong>Water Intake:</strong> <span style={{ textTransform: 'capitalize' }}>{observations.water_intake || 'Not recorded'}</span></div>
                  <div><strong>Activity Level:</strong> <span style={{ textTransform: 'capitalize' }}>{observations.activity_level || 'Not recorded'}</span></div>
                  <div><strong>Breathing:</strong> <span style={{ textTransform: 'capitalize' }}>{observations.breathing_change || 'Not recorded'}</span></div>
                  <div><strong>Pain Observed:</strong> {observations.pain_observed ? '⚠️ Yes' : 'No'}</div>
                  <div><strong>Stool Status:</strong> <span style={{ textTransform: 'capitalize' }}>{observations.stool_change || 'Normal'}</span></div>
                </div>
              </div>
            </div>
          </div>

          {/* Section 6: Computer Vision Findings */}
          <div style={{ marginBottom: '2rem' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 1rem 0', color: 'var(--color-primary)' }}>
              6. Photographic Computer Vision Inspection
            </h2>
            <div
              style={{
                padding: '1.25rem',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                fontSize: '0.85rem',
              }}
            >
              {images.length === 0 || images[0].status === 'NOT_PROVIDED' ? (
                <div style={{ color: 'var(--color-text-muted)' }}>
                  No pet photographs were uploaded during this assessment. Visual analysis was omitted.
                  <div style={{ fontSize: '0.8rem', marginTop: '0.35rem', color: '#64748b' }}>
                    * Omission of pet photos does not imply the absence of physical or dermatological abnormalities.
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {images.map((img, idx) => {
                    const isPassed = img.quality?.check_passed === true || img.quality_gate === 'PASSED';
                    const qMetrics = img.quality?.quality_metrics;

                    return (
                      <div
                        key={idx}
                        style={{
                          padding: '1rem',
                          borderRadius: 'var(--radius-md)',
                          backgroundColor: isPassed ? 'white' : '#fffbeb',
                          border: `1px solid ${isPassed ? 'var(--color-border)' : '#fde68a'}`,
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '0.5rem' }}>
                          <div>
                            <div style={{ fontWeight: 600, color: 'var(--color-text-main)' }}>Inspection Image #{idx + 1}</div>
                            <div style={{ color: 'var(--color-text-muted)', fontSize: '0.8rem' }}>
                              Status: {img.status} • Quality Gate: {img.quality_gate || 'EVALUATED'}
                            </div>
                          </div>
                          <span
                            style={{
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              padding: '0.2rem 0.55rem',
                              borderRadius: 'var(--radius-sm)',
                              backgroundColor: isPassed ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                              color: isPassed ? 'var(--color-success)' : 'var(--color-danger)',
                            }}
                          >
                            Gate: {isPassed ? 'PASSED' : 'REQUIRES BETTER PHOTO'}
                          </span>
                        </div>

                        {/* If quality gate failed: display warning and actionable tip */}
                        {!isPassed && (
                          <div style={{ fontSize: '0.8rem', color: '#92400e', marginBottom: '0.5rem' }}>
                            <div><strong>Quality Advisory:</strong> {img.quality_warnings || img.quality?.warning || 'Image quality insufficient for reliable feature inspection.'}</div>
                            {img.actionable_guidance && (
                              <div style={{ marginTop: '0.25rem', color: '#78350f' }}>
                                💡 <strong>Actionable Tip:</strong> {img.actionable_guidance}
                              </div>
                            )}
                          </div>
                        )}

                        {/* Quality Metrics */}
                        {qMetrics && (
                          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginBottom: '0.5rem', fontSize: '0.75rem' }}>
                            {qMetrics.width && (
                              <span style={{ padding: '0.15rem 0.4rem', backgroundColor: '#f1f5f9', borderRadius: '4px', color: '#475569' }}>
                                {qMetrics.width}x{qMetrics.height}px
                              </span>
                            )}
                            {qMetrics.is_well_lit !== undefined && (
                              <span style={{ padding: '0.15rem 0.4rem', backgroundColor: qMetrics.is_well_lit ? '#ecfdf5' : '#fef2f2', borderRadius: '4px', color: qMetrics.is_well_lit ? '#065f46' : '#991b1b' }}>
                                Lighting: {qMetrics.is_well_lit ? 'Balanced' : 'Sub-optimal'}
                              </span>
                            )}
                            {qMetrics.is_sharp !== undefined && (
                              <span style={{ padding: '0.15rem 0.4rem', backgroundColor: qMetrics.is_sharp ? '#ecfdf5' : '#fef2f2', borderRadius: '4px', color: qMetrics.is_sharp ? '#065f46' : '#991b1b' }}>
                                Focus: {qMetrics.is_sharp ? 'In Focus' : 'Blurry'}
                              </span>
                            )}
                          </div>
                        )}

                        {/* Findings summary and disclaimer */}
                        <div style={{ fontSize: '0.825rem', color: 'var(--color-text-main)' }}>
                          {img.findings_summary}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontStyle: 'italic', marginTop: '0.35rem' }}>
                          * Computational computer-vision observation; does not replace direct clinical veterinary examination.
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Section 7: Explainable Contributing Factors */}
          <div style={{ marginBottom: '2rem' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 1rem 0', color: 'var(--color-primary)' }}>
              7. Explainable Contributing Factors & Evidence Provenance
            </h2>

            {structuredFactors && structuredFactors.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {structuredFactors.map((sf, idx) => {
                  const isEmergency = sf.direction === 'emergency_override' || sf.is_emergency_flag;
                  const isReassuring = sf.direction === 'reassuring';
                  const isUnknown = sf.direction === 'unknown' || sf.status === 'UNKNOWN';

                  return (
                    <div
                      key={idx}
                      style={{
                        padding: '0.85rem 1.25rem',
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: isEmergency ? 'rgba(239, 68, 68, 0.05)' : isReassuring ? 'rgba(16, 185, 129, 0.05)' : 'var(--color-surface)',
                        border: `1px solid ${isEmergency ? 'rgba(239, 68, 68, 0.25)' : isReassuring ? 'rgba(16, 185, 129, 0.25)' : 'var(--color-border)'}`,
                        fontSize: '0.875rem',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', marginBottom: '0.35rem' }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                            <span style={{ fontWeight: 700, color: 'var(--color-text-main)' }}>{sf.factor_name}</span>
                            <span
                              style={{
                                fontSize: '0.7rem',
                                fontWeight: 700,
                                textTransform: 'uppercase',
                                padding: '0.15rem 0.45rem',
                                borderRadius: 'var(--radius-sm)',
                                backgroundColor: 'rgba(2, 132, 199, 0.12)',
                                color: 'var(--color-primary)',
                              }}
                            >
                              {sf.source?.replace('_', ' ') || 'CLINICAL'}
                            </span>
                            <span
                              style={{
                                fontSize: '0.7rem',
                                fontWeight: 700,
                                padding: '0.15rem 0.45rem',
                                borderRadius: 'var(--radius-sm)',
                                backgroundColor: isEmergency ? 'rgba(239, 68, 68, 0.15)' : isReassuring ? 'rgba(16, 185, 129, 0.15)' : isUnknown ? 'rgba(148, 163, 184, 0.2)' : 'rgba(234, 88, 12, 0.15)',
                                color: isEmergency ? 'var(--color-danger)' : isReassuring ? 'var(--color-success)' : isUnknown ? '#64748b' : 'var(--color-warning)',
                              }}
                            >
                              {isEmergency ? 'EMERGENCY OVERRIDE' : isReassuring ? 'REASSURING' : isUnknown ? 'UNKNOWN STATUS' : 'RISK INCREASING'}
                            </span>
                          </div>
                          <div style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
                            Finding: <strong>{sf.finding}</strong>
                          </div>
                        </div>

                        {sf.contribution_pts !== null && sf.contribution_pts !== undefined ? (
                          <span style={{ fontWeight: 800, fontSize: '0.85rem', color: 'var(--color-primary)', whiteSpace: 'nowrap' }}>
                            +{sf.contribution_pts} pts
                          </span>
                        ) : isEmergency ? (
                          <span style={{ fontWeight: 800, fontSize: '0.75rem', color: 'var(--color-danger)', whiteSpace: 'nowrap' }}>
                            {"FLOOR >= 90"}
                          </span>
                        ) : null}
                      </div>

                      {sf.rationale && (
                        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-main)', marginTop: '0.35rem', lineHeight: 1.4 }}>
                          💡 <em>{sf.rationale}</em>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {explainability.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '0.85rem 1.25rem',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--color-surface)',
                      border: '1px solid var(--color-border)',
                      fontSize: '0.875rem',
                      display: 'flex',
                      alignItems: 'flex-start',
                      justifyContent: 'space-between',
                      gap: '1rem',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700, color: 'var(--color-text-main)' }}>{item.factor}</div>
                      <div style={{ color: 'var(--color-text-muted)', fontSize: '0.8rem', marginTop: '0.1rem' }}>
                        {item.observed_finding || item.finding}
                      </div>
                      {item.explanation && (
                        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-main)', marginTop: '0.25rem' }}>
                          💡 {item.explanation}
                        </div>
                      )}
                    </div>
                    <span
                      style={{
                        fontWeight: 700,
                        fontSize: '0.8rem',
                        color: 'var(--color-primary)',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {item.contribution}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Section 8: Clinical Next Steps & Veterinary Recommendation */}
          <div
            style={{
              padding: '1.5rem',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: isEmergency ? 'rgba(239, 68, 68, 0.06)' : 'rgba(2, 132, 199, 0.06)',
              border: `1px solid ${isEmergency ? 'rgba(239, 68, 68, 0.3)' : 'rgba(2, 132, 199, 0.2)'}`,
              marginBottom: '2rem',
            }}
          >
            <h2
              style={{
                fontSize: '1.05rem',
                fontWeight: 700,
                margin: '0 0 0.5rem 0',
                color: isEmergency ? 'var(--color-danger)' : 'var(--color-primary)',
              }}
            >
              8. Clinical Next Steps & Veterinary Guidance
            </h2>
            <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--color-text-main)', marginBottom: '0.5rem' }}>
              {recommendations.primary_action || risk.recommendation || 'Consult your veterinarian.'}
            </div>
            <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', margin: 0 }}>
              {recommendations.guidance || 'Monitor hydration, posture, and appetite. Seek professional veterinary medical assistance if symptoms worsen or fail to resolve.'}
            </p>
          </div>

          {/* Section 9: Veterinary Handoff Summary (Structured for Copying) */}
          <div
            style={{
              padding: '1.5rem',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              marginBottom: '2rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <div>
                <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--color-text-main)' }}>
                  9. Veterinary Clinic Handoff Summary
                </h2>
                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', margin: 0 }}>
                  Pre-formatted clinical handoff ready to paste into clinic registration or email to your veterinary provider.
                </p>
              </div>
              <button
                onClick={handleCopyHandoff}
                className="btn btn-outline btn-sm"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
              >
                {copiedHandoff ? <Check size={14} color="var(--color-success)" /> : <Copy size={14} />}
                {copiedHandoff ? 'Copied!' : 'Copy Summary'}
              </button>
            </div>

            <div
              style={{
                backgroundColor: 'white',
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--color-border)',
                fontFamily: 'monospace',
                fontSize: '0.8rem',
                whiteSpace: 'pre-wrap',
                lineHeight: 1.5,
                color: 'var(--color-text-main)',
              }}
            >
              {`PATIENT: ${handoff.patient || pet.name}
TRIAGE: ${risk.risk_level} (Score: ${risk.risk_score}/100) | URGENCY: ${emergency.action_urgency}
PRIMARY CONCERNS: ${handoff.primary_complaint || 'General intake'}
OBSERVATIONS: ${handoff.clinical_observations_summary || 'Normal'}
RECOMMENDATION: ${recommendations.primary_action || risk.recommendation}`}
            </div>
          </div>

          {/* Legal / Medical Disclaimer Box */}
          <div
            style={{
              padding: '1rem 1.25rem',
              borderRadius: 'var(--radius-md)',
              backgroundColor: '#f8fafc',
              border: '1px solid #e2e8f0',
              fontSize: '0.775rem',
              color: 'var(--color-text-muted)',
              lineHeight: 1.5,
            }}
          >
            <strong>CLINICAL DISCLAIMER:</strong> {report.disclaimer || 'VetVision AI is an AI-assisted informational and triage support application. It does not provide definitive medical or veterinary diagnosis, nor does it establish a veterinarian-client-patient relationship. In cases of acute injury, poisoning, severe breathing distress, or sudden collapse, visit an emergency veterinary hospital immediately.'}
          </div>
        </div>
      </div>
    </div>
  );
}
