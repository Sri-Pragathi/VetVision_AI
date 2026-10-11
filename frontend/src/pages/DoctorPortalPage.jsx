import React, { useState, useEffect, useCallback } from 'react';
import {
  ShieldCheck,
  Stethoscope,
  Search,
  Filter,
  AlertTriangle,
  CheckCircle2,
  Clock,
  User,
  Activity,
  FileText,
  Calendar,
  X,
  Save,
  RefreshCw,
  ExternalLink,
  Pill,
  ClipboardList,
  Eye,
  Info,
} from 'lucide-react';
import { doctorApi } from '../api/doctorApi';
import TriageBadge from '../components/common/TriageBadge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import { getSpeciesEmoji } from '../utils/petSpecies';

export default function DoctorPortalPage() {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [reviewStatusFilter, setReviewStatusFilter] = useState('all');
  const [triageFilter, setTriageFilter] = useState('all');
  const [pagination, setPagination] = useState({ page: 1, per_page: 20, total: 0, pages: 1 });

  // Detail Modal State
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [caseDetail, setCaseDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);
  const [activeTab, setActiveTab] = useState('clinical_notes'); // 'clinical_notes' | 'patient_intake' | 'ai_analysis'

  // Review Form State
  const [reviewFormData, setReviewFormData] = useState({
    override_triage_level: '',
    doctor_notes: '',
    recommendations: '',
    prescriptions: '',
    status: 'reviewed',
  });
  const [savingReview, setSavingReview] = useState(false);
  const [reviewSuccessMsg, setReviewSuccessMsg] = useState(null);

  const fetchCases = useCallback(async (page = 1) => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page,
        per_page: 20,
      };
      if (searchQuery.trim()) params.search = searchQuery.trim();
      if (reviewStatusFilter !== 'all') params.review_status = reviewStatusFilter;
      if (triageFilter !== 'all') params.triage_level = triageFilter;

      const res = await doctorApi.getCases(params);
      const data = res?.data || res;
      setCases(data.items || []);
      setPagination({
        page: data.page || 1,
        per_page: data.per_page || 20,
        total: data.total || 0,
        pages: data.pages || 1,
      });
    } catch (err) {
      console.error('Failed to load clinical cases:', err);
      setError(err?.response?.data?.message || 'Failed to load clinical cases. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [searchQuery, reviewStatusFilter, triageFilter]);

  useEffect(() => {
    fetchCases(1);
  }, [fetchCases]);

  // Handle opening case detail
  const handleOpenCase = async (assessmentId) => {
    setSelectedCaseId(assessmentId);
    setDetailLoading(true);
    setDetailError(null);
    setReviewSuccessMsg(null);
    setActiveTab('clinical_notes');

    try {
      const res = await doctorApi.getCaseDetail(assessmentId);
      const detail = res?.data || res;
      setCaseDetail(detail);

      // Prepopulate form if existing review exists
      const existing = detail.latest_review;
      if (existing) {
        setReviewFormData({
          override_triage_level: existing.override_triage_level || '',
          doctor_notes: existing.doctor_notes || '',
          recommendations: existing.recommendations || '',
          prescriptions: existing.prescriptions || '',
          status: existing.status || 'reviewed',
        });
      } else {
        // Default override to AI triage level if available
        const defaultTriage = detail.risk_analysis?.risk_level
          ? detail.risk_analysis.risk_level.toLowerCase() === 'emergency'
            ? 'critical'
            : detail.risk_analysis.risk_level.toLowerCase() === 'high'
            ? 'urgent'
            : detail.risk_analysis.risk_level.toLowerCase() === 'moderate'
            ? 'routine'
            : 'non_urgent'
          : 'routine';

        setReviewFormData({
          override_triage_level: defaultTriage,
          doctor_notes: '',
          recommendations: '',
          prescriptions: '',
          status: 'reviewed',
        });
      }
    } catch (err) {
      console.error('Failed to load case detail:', err);
      setDetailError(err?.response?.data?.message || 'Failed to retrieve case details.');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseModal = () => {
    setSelectedCaseId(null);
    setCaseDetail(null);
    setDetailError(null);
    setReviewSuccessMsg(null);
  };

  const handleSaveReview = async (e) => {
    e.preventDefault();
    if (!selectedCaseId) return;

    try {
      setSavingReview(true);
      setReviewSuccessMsg(null);

      const payload = {
        override_triage_level: reviewFormData.override_triage_level || null,
        doctor_notes: reviewFormData.doctor_notes.trim() || null,
        recommendations: reviewFormData.recommendations.trim() || null,
        prescriptions: reviewFormData.prescriptions.trim() || null,
        status: reviewFormData.status || 'reviewed',
      };

      const res = await doctorApi.submitReview(selectedCaseId, payload);
      const savedReview = res?.data || res;

      setReviewSuccessMsg('Clinical review and treatment plan saved successfully.');

      // Update case detail locally
      setCaseDetail((prev) => ({
        ...prev,
        latest_review: savedReview,
        doctor_reviews: [savedReview, ...(prev?.doctor_reviews?.filter((r) => r.id !== savedReview.id) || [])],
      }));

      // Refresh cases queue in background
      fetchCases(pagination.page);
    } catch (err) {
      console.error('Failed to submit clinical review:', err);
      alert(err?.response?.data?.message || 'Failed to submit clinical review.');
    } finally {
      setSavingReview(false);
    }
  };

  // Queue metrics
  const totalCases = pagination.total;
  const pendingCount = cases.filter((c) => c.review_status === 'pending').length;
  const criticalCount = cases.filter(
    (c) => c.effective_triage === 'critical' || c.effective_triage === 'urgent'
  ).length;
  const reviewedCount = cases.filter((c) => c.review_status === 'reviewed').length;

  return (
    <div className="container" style={{ padding: '2rem 1rem 4rem' }}>
      {/* Top Banner & Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '0.75rem' }}>
          <div>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 10px', borderRadius: 'var(--radius-full)', backgroundColor: '#ecfdf5', color: '#065f46', fontSize: '12px', fontWeight: 700, border: '1px solid #a7f3d0', marginBottom: '0.5rem' }}>
              <ShieldCheck size={14} />
              <span>Veterinary Clinical Portal</span>
            </div>
            <h1 style={{ fontSize: '1.875rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em', margin: 0 }}>
              Clinical Triage & Review Queue
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', margin: '4px 0 0' }}>
              Review patient intake sessions, AI risk assessments, diagnostic findings, and issue veterinary treatment plans.
            </p>
          </div>

          <button
            onClick={() => fetchCases(pagination.page)}
            className="btn btn-secondary btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
            disabled={loading}
          >
            <RefreshCw size={15} className={loading ? 'spin-icon' : ''} />
            <span>Refresh Queue</span>
          </button>
        </div>

        {/* Clinical Queue Metrics Strip */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginTop: '1.5rem' }}>
          <div style={{ backgroundColor: 'var(--bg-surface)', padding: '1.25rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-light)', boxShadow: 'var(--shadow-sm)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 600 }}>
              <span>Total Intake Sessions</span>
              <ClipboardList size={18} color="var(--primary)" />
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-main)', marginTop: '0.5rem' }}>
              {totalCases}
            </div>
          </div>

          <div style={{ backgroundColor: 'var(--bg-surface)', padding: '1.25rem', borderRadius: 'var(--radius-lg)', border: '1px solid #fef3c7', boxShadow: 'var(--shadow-sm)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#b45309', fontSize: '0.85rem', fontWeight: 600 }}>
              <span>Pending Reviews</span>
              <Clock size={18} color="#f59e0b" />
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#b45309', marginTop: '0.5rem' }}>
              {pendingCount}
            </div>
          </div>

          <div style={{ backgroundColor: 'var(--bg-surface)', padding: '1.25rem', borderRadius: 'var(--radius-lg)', border: '1px solid #fee2e2', boxShadow: 'var(--shadow-sm)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#b91c1c', fontSize: '0.85rem', fontWeight: 600 }}>
              <span>Critical / Urgent Priority</span>
              <AlertTriangle size={18} color="#ef4444" />
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#b91c1c', marginTop: '0.5rem' }}>
              {criticalCount}
            </div>
          </div>

          <div style={{ backgroundColor: 'var(--bg-surface)', padding: '1.25rem', borderRadius: 'var(--radius-lg)', border: '1px solid #d1fae5', boxShadow: 'var(--shadow-sm)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#065f46', fontSize: '0.85rem', fontWeight: 600 }}>
              <span>Reviewed & Verified</span>
              <CheckCircle2 size={18} color="#10b981" />
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#065f46', marginTop: '0.5rem' }}>
              {reviewedCount}
            </div>
          </div>
        </div>
      </div>

      {/* Filters and Search Bar */}
      <div style={{
        backgroundColor: 'var(--bg-surface)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-light)',
        padding: '1rem',
        marginBottom: '1.5rem',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: '1 1 300px' }}>
          <div style={{ position: 'relative', width: '100%' }}>
            <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search pet name, breed, or owner..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem 0.5rem 2.5rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-light)',
                fontSize: '0.9rem',
                backgroundColor: 'var(--bg-main)',
              }}
            />
          </div>
        </div>

        {/* Review Status Tabs */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', backgroundColor: 'var(--bg-muted)', padding: '3px', borderRadius: 'var(--radius-md)' }}>
          {['all', 'pending', 'reviewed'].map((st) => (
            <button
              key={st}
              onClick={() => setReviewStatusFilter(st)}
              style={{
                border: 'none',
                padding: '5px 12px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                backgroundColor: reviewStatusFilter === st ? 'var(--bg-surface)' : 'transparent',
                color: reviewStatusFilter === st ? 'var(--primary)' : 'var(--text-muted)',
                boxShadow: reviewStatusFilter === st ? 'var(--shadow-sm)' : 'none',
                textTransform: 'capitalize',
              }}
            >
              {st === 'pending' ? 'Needs Review' : st}
            </button>
          ))}
        </div>

        {/* Triage Level Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Filter size={16} color="var(--text-muted)" />
          <select
            value={triageFilter}
            onChange={(e) => setTriageFilter(e.target.value)}
            style={{
              padding: '0.5rem 0.75rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-light)',
              fontSize: '0.85rem',
              backgroundColor: 'var(--bg-main)',
              color: 'var(--text-main)',
            }}
          >
            <option value="all">All Triage Levels</option>
            <option value="critical">Critical / Emergency</option>
            <option value="urgent">Urgent / High</option>
            <option value="routine">Routine / Moderate</option>
            <option value="non_urgent">Non-Urgent / Low</option>
          </select>
        </div>
      </div>

      {/* Main Cases Table / Content */}
      {error && <ErrorMessage message={error} onRetry={() => fetchCases(pagination.page)} />}

      {loading ? (
        <div style={{ padding: '4rem 1rem', display: 'flex', justifyContent: 'center' }}>
          <LoadingSpinner message="Loading clinical queue..." />
        </div>
      ) : cases.length === 0 ? (
        <div style={{
          backgroundColor: 'var(--bg-surface)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-light)',
          padding: '3.5rem 1rem',
          textAlign: 'center',
        }}>
          <Stethoscope size={48} color="var(--primary)" style={{ opacity: 0.7, margin: '0 auto 1rem' }} />
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 0.5rem' }}>No clinical cases found</h3>
          <p style={{ color: 'var(--text-muted)', maxWidth: '440px', margin: '0 auto 1.5rem', fontSize: '0.95rem' }}>
            There are currently no patient intake sessions matching your search or filter parameters.
          </p>
          <button
            onClick={() => {
              setSearchQuery('');
              setReviewStatusFilter('all');
              setTriageFilter('all');
            }}
            className="btn btn-secondary btn-sm"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div style={{
          backgroundColor: 'var(--bg-surface)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-light)',
          boxShadow: 'var(--shadow-sm)',
          overflow: 'hidden',
        }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--bg-muted)', borderBottom: '1px solid var(--border-light)', color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  <th style={{ padding: '0.85rem 1.25rem' }}>Patient & Owner</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Reported Symptoms</th>
                  <th style={{ padding: '0.85rem 1rem' }}>AI Triage & Score</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Review Status</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Intake Date</th>
                  <th style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {cases.map((c) => {
                  const pet = c.pet || {};
                  const isReviewed = c.review_status === 'reviewed';
                  const effectiveTriage = c.effective_triage || 'routine';
                  const riskAnalysis = c.risk_analysis;

                  return (
                    <tr
                      key={c.assessment_id}
                      style={{
                        borderBottom: '1px solid var(--border-light)',
                        transition: 'background-color 0.15s ease',
                      }}
                      className="case-row"
                    >
                      {/* Patient & Owner */}
                      <td style={{ padding: '1rem 1.25rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <div style={{
                            width: '42px',
                            height: '42px',
                            borderRadius: 'var(--radius-md)',
                            backgroundColor: 'var(--bg-muted)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '22px',
                            overflow: 'hidden',
                            flexShrink: 0,
                          }}>
                            {pet.photo_url ? (
                              <img src={pet.photo_url} alt={pet.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                            ) : (
                              <span>{getSpeciesEmoji(pet.species)}</span>
                            )}
                          </div>
                          <div>
                            <div style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '0.95rem' }}>
                              {pet.name || 'Unnamed Pet'}
                            </div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                              {pet.breed || pet.species || 'Unknown'} &bull; {pet.weight ? `${pet.weight} ${pet.weight_unit || 'kg'}` : ''}
                            </div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--primary)', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '3px' }}>
                              <User size={11} />
                              <span>{pet.owner_name}</span>
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Reported Symptoms */}
                      <td style={{ padding: '1rem' }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '3px 8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--bg-muted)', fontSize: '0.8rem', fontWeight: 600 }}>
                          <Activity size={13} color="var(--primary)" />
                          <span>{c.symptoms_count} symptom{c.symptoms_count === 1 ? '' : 's'}</span>
                        </div>
                        {c.images_count > 0 && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                            {c.images_count} image{c.images_count === 1 ? '' : 's'} attached
                          </div>
                        )}
                      </td>

                      {/* AI Triage & Score */}
                      <td style={{ padding: '1rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                          <TriageBadge level={effectiveTriage} />
                          {riskAnalysis?.risk_score !== undefined && (
                            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                              Score: {riskAnalysis.risk_score}/100
                            </span>
                          )}
                        </div>
                        {c.latest_review?.override_triage_level && (
                          <div style={{ fontSize: '0.75rem', color: '#065f46', marginTop: '4px', fontWeight: 600 }}>
                            Dr. Triage: {c.latest_review.override_triage_level}
                          </div>
                        )}
                      </td>

                      {/* Review Status */}
                      <td style={{ padding: '1rem' }}>
                        {isReviewed ? (
                          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '4px 9px', borderRadius: 'var(--radius-full)', backgroundColor: '#ecfdf5', color: '#065f46', fontSize: '0.8rem', fontWeight: 700, border: '1px solid #a7f3d0' }}>
                            <CheckCircle2 size={13} />
                            <span>Reviewed</span>
                          </div>
                        ) : (
                          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '4px 9px', borderRadius: 'var(--radius-full)', backgroundColor: '#fef3c7', color: '#b45309', fontSize: '0.8rem', fontWeight: 700, border: '1px solid #fde68a' }}>
                            <Clock size={13} />
                            <span>Needs Review</span>
                          </div>
                        )}
                        {c.latest_review?.doctor_name && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '3px' }}>
                            by {c.latest_review.doctor_name}
                          </div>
                        )}
                      </td>

                      {/* Intake Date */}
                      <td style={{ padding: '1rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                        {c.completed_at || c.created_at ? (
                          <span>{new Date(c.completed_at || c.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                        ) : (
                          'Recently'
                        )}
                      </td>

                      {/* Actions */}
                      <td style={{ padding: '1rem 1.25rem', textAlign: 'right' }}>
                        <button
                          onClick={() => handleOpenCase(c.assessment_id)}
                          className={`btn btn-sm ${isReviewed ? 'btn-secondary' : 'btn-primary'}`}
                          style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                        >
                          <Stethoscope size={14} />
                          <span>{isReviewed ? 'View & Edit' : 'Review Case'}</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination controls if multiple pages */}
          {pagination.pages > 1 && (
            <div style={{ padding: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-light)', backgroundColor: 'var(--bg-muted)' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Page {pagination.page} of {pagination.pages} ({pagination.total} cases)
              </span>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  disabled={pagination.page <= 1}
                  onClick={() => fetchCases(pagination.page - 1)}
                  className="btn btn-secondary btn-sm"
                >
                  Previous
                </button>
                <button
                  disabled={pagination.page >= pagination.pages}
                  onClick={() => fetchCases(pagination.page + 1)}
                  className="btn btn-secondary btn-sm"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Case Clinical Review Modal */}
      {selectedCaseId && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.6)',
          backdropFilter: 'blur(3px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1.5rem',
        }}>
          <div style={{
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 'var(--radius-xl)',
            border: '1px solid var(--border-light)',
            boxShadow: 'var(--shadow-xl)',
            width: '100%',
            maxWidth: '960px',
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}>
            {/* Modal Header */}
            <div style={{
              padding: '1.25rem 1.5rem',
              borderBottom: '1px solid var(--border-light)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: 'var(--bg-muted)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--primary)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Stethoscope size={20} />
                </div>
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0, color: 'var(--text-main)' }}>
                    Clinical Case Review &mdash; {caseDetail?.pet?.name || 'Patient'}
                  </h2>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    ID: {selectedCaseId} &bull; Owner: {caseDetail?.pet?.owner?.name || 'Owner'} ({caseDetail?.pet?.owner?.email})
                  </span>
                </div>
              </div>

              <button
                onClick={handleCloseModal}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}
                aria-label="Close modal"
              >
                <X size={22} />
              </button>
            </div>

            {/* Modal Body */}
            {detailLoading ? (
              <div style={{ padding: '4rem 1rem', display: 'flex', justifyContent: 'center' }}>
                <LoadingSpinner message="Retrieving clinical records and history..." />
              </div>
            ) : detailError ? (
              <div style={{ padding: '2rem' }}>
                <ErrorMessage message={detailError} />
              </div>
            ) : caseDetail ? (
              <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
                {/* Modal Navigation Tabs */}
                <div style={{ display: 'flex', borderBottom: '1px solid var(--border-light)', backgroundColor: 'var(--bg-surface)', padding: '0 1.5rem' }}>
                  <button
                    onClick={() => setActiveTab('clinical_notes')}
                    style={{
                      padding: '0.85rem 1.25rem',
                      border: 'none',
                      background: 'none',
                      fontWeight: 700,
                      fontSize: '0.9rem',
                      cursor: 'pointer',
                      borderBottom: activeTab === 'clinical_notes' ? '2px solid var(--primary)' : '2px solid transparent',
                      color: activeTab === 'clinical_notes' ? 'var(--primary)' : 'var(--text-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}
                  >
                    <Stethoscope size={16} />
                    <span>Doctor Review & Rx</span>
                  </button>
                  <button
                    onClick={() => setActiveTab('patient_intake')}
                    style={{
                      padding: '0.85rem 1.25rem',
                      border: 'none',
                      background: 'none',
                      fontWeight: 700,
                      fontSize: '0.9rem',
                      cursor: 'pointer',
                      borderBottom: activeTab === 'patient_intake' ? '2px solid var(--primary)' : '2px solid transparent',
                      color: activeTab === 'patient_intake' ? 'var(--primary)' : 'var(--text-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}
                  >
                    <ClipboardList size={16} />
                    <span>Patient Intake & History</span>
                  </button>
                  <button
                    onClick={() => setActiveTab('ai_analysis')}
                    style={{
                      padding: '0.85rem 1.25rem',
                      border: 'none',
                      background: 'none',
                      fontWeight: 700,
                      fontSize: '0.9rem',
                      cursor: 'pointer',
                      borderBottom: activeTab === 'ai_analysis' ? '2px solid var(--primary)' : '2px solid transparent',
                      color: activeTab === 'ai_analysis' ? 'var(--primary)' : 'var(--text-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}
                  >
                    <Activity size={16} />
                    <span>AI Risk & Computer Vision</span>
                  </button>
                </div>

                {/* Tab Contents (Scrollable) */}
                <div style={{ padding: '1.5rem', overflowY: 'auto', flex: 1 }}>
                  {reviewSuccessMsg && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', backgroundColor: '#ecfdf5', color: '#065f46', border: '1px solid #a7f3d0', marginBottom: '1.25rem', fontSize: '0.9rem', fontWeight: 600 }}>
                      <CheckCircle2 size={18} />
                      <span>{reviewSuccessMsg}</span>
                    </div>
                  )}

                  {/* TAB 1: DOCTOR REVIEW FORM */}
                  {activeTab === 'clinical_notes' && (
                    <form onSubmit={handleSaveReview} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                        {/* Triage Override */}
                        <div>
                          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.4rem', color: 'var(--text-main)' }}>
                            Veterinary Clinical Triage Assignment
                          </label>
                          <select
                            value={reviewFormData.override_triage_level}
                            onChange={(e) => setReviewFormData({ ...reviewFormData, override_triage_level: e.target.value })}
                            style={{
                              width: '100%',
                              padding: '0.65rem 0.85rem',
                              borderRadius: 'var(--radius-md)',
                              border: '1px solid var(--border-light)',
                              fontSize: '0.9rem',
                              backgroundColor: 'var(--bg-main)',
                              color: 'var(--text-main)',
                              fontWeight: 600,
                            }}
                          >
                            <option value="routine">Routine (Mild / Elective Care)</option>
                            <option value="non_urgent">Non-Urgent (Monitoring / Wellness)</option>
                            <option value="urgent">Urgent (Clinical Care Required within 24-48h)</option>
                            <option value="critical">Critical / Emergency (Immediate Clinical Stabilization)</option>
                          </select>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                            AI recommended triage: <strong>{caseDetail.risk_analysis?.risk_level || 'Routine'}</strong>
                          </span>
                        </div>

                        {/* Review Status */}
                        <div>
                          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.4rem', color: 'var(--text-main)' }}>
                            Review Queue Status
                          </label>
                          <select
                            value={reviewFormData.status}
                            onChange={(e) => setReviewFormData({ ...reviewFormData, status: e.target.value })}
                            style={{
                              width: '100%',
                              padding: '0.65rem 0.85rem',
                              borderRadius: 'var(--radius-md)',
                              border: '1px solid var(--border-light)',
                              fontSize: '0.9rem',
                              backgroundColor: 'var(--bg-main)',
                              color: 'var(--text-main)',
                              fontWeight: 600,
                            }}
                          >
                            <option value="reviewed">Reviewed & Approved</option>
                            <option value="pending">Pending Further Diagnostics</option>
                          </select>
                        </div>
                      </div>

                      {/* Doctor Clinical Notes */}
                      <div>
                        <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.4rem', color: 'var(--text-main)' }}>
                          Clinical Assessment & Differential Diagnosis Notes
                        </label>
                        <textarea
                          rows={4}
                          placeholder="Document your clinical impressions, diagnostic reasoning, examination findings..."
                          value={reviewFormData.doctor_notes}
                          onChange={(e) => setReviewFormData({ ...reviewFormData, doctor_notes: e.target.value })}
                          style={{
                            width: '100%',
                            padding: '0.75rem',
                            borderRadius: 'var(--radius-md)',
                            border: '1px solid var(--border-light)',
                            fontSize: '0.9rem',
                            backgroundColor: 'var(--bg-main)',
                            color: 'var(--text-main)',
                            resize: 'vertical',
                          }}
                        />
                      </div>

                      {/* Clinical Recommendations */}
                      <div>
                        <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.4rem', color: 'var(--text-main)' }}>
                          Recommendations & Owner Care Plan
                        </label>
                        <textarea
                          rows={3}
                          placeholder="Home monitoring instructions, follow-up timeline, red-flag triggers to watch for..."
                          value={reviewFormData.recommendations}
                          onChange={(e) => setReviewFormData({ ...reviewFormData, recommendations: e.target.value })}
                          style={{
                            width: '100%',
                            padding: '0.75rem',
                            borderRadius: 'var(--radius-md)',
                            border: '1px solid var(--border-light)',
                            fontSize: '0.9rem',
                            backgroundColor: 'var(--bg-main)',
                            color: 'var(--text-main)',
                            resize: 'vertical',
                          }}
                        />
                      </div>

                      {/* Prescriptions */}
                      <div>
                        <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.4rem', color: 'var(--text-main)' }}>
                          Prescriptions & Medications (Rx)
                        </label>
                        <textarea
                          rows={3}
                          placeholder="Medication name, dosage, frequency, administration route, and duration..."
                          value={reviewFormData.prescriptions}
                          onChange={(e) => setReviewFormData({ ...reviewFormData, prescriptions: e.target.value })}
                          style={{
                            width: '100%',
                            padding: '0.75rem',
                            borderRadius: 'var(--radius-md)',
                            border: '1px solid var(--border-light)',
                            fontSize: '0.9rem',
                            backgroundColor: 'var(--bg-main)',
                            color: 'var(--text-main)',
                            resize: 'vertical',
                          }}
                        />
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                        <button
                          type="button"
                          onClick={handleCloseModal}
                          className="btn btn-secondary"
                        >
                          Close
                        </button>
                        <button
                          type="submit"
                          className="btn btn-primary"
                          disabled={savingReview}
                          style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                        >
                          <Save size={16} />
                          <span>{savingReview ? 'Saving Review...' : 'Save & Publish Review'}</span>
                        </button>
                      </div>
                    </form>
                  )}

                  {/* TAB 2: PATIENT INTAKE & MEDICAL HISTORY */}
                  {activeTab === 'patient_intake' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                      {/* Pet Profile Card */}
                      <div style={{ backgroundColor: 'var(--bg-muted)', padding: '1.25rem', borderRadius: 'var(--radius-lg)' }}>
                        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, margin: '0 0 0.75rem', color: 'var(--text-main)' }}>
                          Patient Medical Record
                        </h4>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem', fontSize: '0.85rem' }}>
                          <div><span style={{ color: 'var(--text-muted)' }}>Species:</span> <strong>{caseDetail.pet?.species}</strong></div>
                          <div><span style={{ color: 'var(--text-muted)' }}>Breed:</span> <strong>{caseDetail.pet?.breed || 'Unknown'}</strong></div>
                          <div><span style={{ color: 'var(--text-muted)' }}>Age:</span> <strong>{caseDetail.pet?.age ? `${caseDetail.pet.age} years` : 'Unknown'}</strong></div>
                          <div><span style={{ color: 'var(--text-muted)' }}>Sex:</span> <strong>{caseDetail.pet?.sex || 'Unknown'}</strong></div>
                          <div><span style={{ color: 'var(--text-muted)' }}>Weight:</span> <strong>{caseDetail.pet?.weight ? `${caseDetail.pet.weight} ${caseDetail.pet.weight_unit || 'kg'}` : 'Unknown'}</strong></div>
                          <div><span style={{ color: 'var(--text-muted)' }}>Spayed/Neutered:</span> <strong>{caseDetail.pet?.spayed_neutered ? 'Yes' : 'No'}</strong></div>
                        </div>

                        {caseDetail.pet?.vaccination_history && (
                          <div style={{ marginTop: '0.75rem', fontSize: '0.85rem' }}>
                            <span style={{ color: 'var(--text-muted)' }}>Vaccination History:</span>
                            <div style={{ fontWeight: 600, marginTop: '2px' }}>{caseDetail.pet.vaccination_history}</div>
                          </div>
                        )}
                        {caseDetail.pet?.medical_history && (
                          <div style={{ marginTop: '0.75rem', fontSize: '0.85rem' }}>
                            <span style={{ color: 'var(--text-muted)' }}>Past Medical History:</span>
                            <div style={{ fontWeight: 600, marginTop: '2px' }}>{caseDetail.pet.medical_history}</div>
                          </div>
                        )}
                      </div>

                      {/* Reported Symptoms */}
                      <div>
                        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, margin: '0 0 0.75rem', color: 'var(--text-main)' }}>
                          Reported Clinical Symptoms ({caseDetail.symptoms?.length || 0})
                        </h4>
                        {caseDetail.symptoms && caseDetail.symptoms.length > 0 ? (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            {caseDetail.symptoms.map((s, idx) => (
                              <div key={idx} style={{ padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)', backgroundColor: 'var(--bg-surface)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                                <div>
                                  <div style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '0.9rem' }}>
                                    {s.symptom_name || s.name || 'Symptom'}
                                  </div>
                                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                    Duration: {s.duration?.value ? `${s.duration.value} ${s.duration.unit}` : (s.duration_value ? `${s.duration_value} ${s.duration_unit}` : 'Not specified')}
                                    {s.notes && ` &bull; Notes: ${s.notes}`}
                                  </div>
                                </div>
                                <span style={{
                                  padding: '3px 8px',
                                  borderRadius: 'var(--radius-sm)',
                                  fontSize: '0.75rem',
                                  fontWeight: 700,
                                  textTransform: 'uppercase',
                                  backgroundColor: s.severity === 'severe' ? '#fee2e2' : s.severity === 'moderate' ? '#fef3c7' : '#ecfdf5',
                                  color: s.severity === 'severe' ? '#b91c1c' : s.severity === 'moderate' ? '#b45309' : '#065f46',
                                }}>
                                  {s.severity || 'Mild'}
                                </span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No symptoms logged.</p>
                        )}
                      </div>

                      {/* Dynamic Triage Questions & Answers */}
                      <div>
                        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, margin: '0 0 0.75rem', color: 'var(--text-main)' }}>
                          Dynamic Follow-Up Questionnaire Responses ({caseDetail.answers?.length || 0})
                        </h4>
                        {caseDetail.answers && caseDetail.answers.length > 0 ? (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            {caseDetail.answers.map((ans, idx) => (
                              <div key={idx} style={{ padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)', backgroundColor: 'var(--bg-surface)' }}>
                                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)' }}>
                                  {ans.question?.question_text || `Question #${idx + 1}`}
                                </div>
                                <div style={{ fontSize: '0.85rem', color: 'var(--primary)', fontWeight: 600, marginTop: '3px' }}>
                                  Answer: {ans.selected_option?.option_text || ans.answer_text || (ans.boolean_value !== null ? (ans.boolean_value ? 'Yes' : 'No') : ans.numeric_value || 'None')}
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No follow-up questions recorded.</p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* TAB 3: AI RISK & COMPUTER VISION */}
                  {activeTab === 'ai_analysis' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                      {/* Risk Analysis Card */}
                      <div style={{ backgroundColor: 'var(--bg-muted)', padding: '1.25rem', borderRadius: 'var(--radius-lg)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                          <div>
                            <h4 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0, color: 'var(--text-main)' }}>
                              AI Explainable Risk Evaluation
                            </h4>
                            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                              Engine: {caseDetail.risk_analysis?.engine_version || 'Hybrid Rule & CV Engine v1.0'}
                            </span>
                          </div>
                          {caseDetail.risk_analysis && (
                            <TriageBadge level={caseDetail.risk_analysis.risk_level.toLowerCase()} />
                          )}
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
                          <div style={{ backgroundColor: 'var(--bg-surface)', padding: '0.85rem', borderRadius: 'var(--radius-md)' }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Assigned Risk Level</span>
                            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>
                              {caseDetail.risk_analysis?.risk_level || 'N/A'}
                            </div>
                          </div>
                          <div style={{ backgroundColor: 'var(--bg-surface)', padding: '0.85rem', borderRadius: 'var(--radius-md)' }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Calculated Risk Score</span>
                            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--primary)' }}>
                              {caseDetail.risk_analysis?.risk_score ?? 'N/A'} / 100
                            </div>
                          </div>
                        </div>

                        {caseDetail.risk_analysis?.recommendation && (
                          <div style={{ backgroundColor: 'var(--bg-surface)', padding: '0.85rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem' }}>
                            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                              Automated Clinical Guidance
                            </span>
                            <p style={{ margin: '4px 0 0', fontSize: '0.9rem', color: 'var(--text-main)' }}>
                              {caseDetail.risk_analysis.recommendation}
                            </p>
                          </div>
                        )}

                        {caseDetail.risk_analysis?.key_factors && caseDetail.risk_analysis.key_factors.length > 0 && (
                          <div>
                            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                              Contributing Risk Factors
                            </span>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
                              {caseDetail.risk_analysis.key_factors.map((factor, idx) => (
                                <span key={idx} style={{ padding: '3px 8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-light)', fontSize: '0.8rem', fontWeight: 600 }}>
                                  {factor}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Computer Vision Images */}
                      <div>
                        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, margin: '0 0 0.75rem', color: 'var(--text-main)' }}>
                          Diagnostic Images & Computer Vision Findings ({caseDetail.images?.length || 0})
                        </h4>
                        {caseDetail.images && caseDetail.images.length > 0 ? (
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
                            {caseDetail.images.map((img) => (
                              <div key={img.id} style={{ borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)', overflow: 'hidden', backgroundColor: 'var(--bg-surface)' }}>
                                <img
                                  src={img.image_url || img.url}
                                  alt="Clinical upload"
                                  style={{ width: '100%', height: '160px', objectFit: 'cover' }}
                                />
                                <div style={{ padding: '0.75rem', fontSize: '0.8rem' }}>
                                  <div style={{ fontWeight: 700, color: 'var(--text-main)' }}>
                                    Region: {img.body_part || 'General'}
                                  </div>
                                  {img.analysis && (
                                    <div style={{ color: 'var(--text-muted)', marginTop: '4px' }}>
                                      Findings: {img.analysis?.prediction || 'Normal'}
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No clinical images uploaded for this intake.</p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}

      <style>{`
        .case-row:hover {
          background-color: var(--bg-muted);
        }
        .spin-icon {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
