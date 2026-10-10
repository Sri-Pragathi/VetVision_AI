import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Search,
  Filter,
  Calendar,
  Activity,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react';
import { petApi } from '../api/petApi';
import { reportApi } from '../api/reportApi';
import TriageBadge from '../components/common/TriageBadge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import EmptyState from '../components/common/EmptyState';
import { getSpeciesEmoji } from '../utils/petSpecies';

export default function ReportsListPage() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTriage, setSelectedTriage] = useState('all');

  useEffect(() => {
    fetchAllReports();
  }, []);

  const fetchAllReports = async () => {
    try {
      setLoading(true);
      setError(null);

      let reportItems = [];

      // Primary strategy: Fetch all user reports directly in one atomic call
      try {
        const userReports = await reportApi.getUserReports();
        const rawList = Array.isArray(userReports) ? userReports : (userReports?.data || []);
        if (Array.isArray(rawList) && rawList.length > 0) {
          reportItems = rawList.map((r) => ({
            id: r.id,
            assessment_id: r.assessment_id,
            pet: r.pet || {},
            created_at: r.generated_at || r.created_at,
            triage_level:
              r.summary?.risk_level ||
              r.report_data?.risk_analysis?.risk_level ||
              r.report_data?.risk_analysis?.overall_risk_level ||
              'routine',
            risk_score:
              r.summary?.risk_score ??
              r.report_data?.risk_analysis?.risk_score,
            symptoms_count:
              r.symptoms_count ??
              r.report_data?.symptoms?.length ??
              r.report_data?.reported_symptoms?.length ??
              0,
            is_emergency: Boolean(
              r.summary?.is_emergency ??
              r.report_data?.emergency?.is_emergency ??
              r.report_data?.emergency_evaluation?.is_emergency ??
              false
            ),
          }));
        }
      } catch (directErr) {
        console.warn('Direct user reports fetch unavailable, falling back to assessment inspection:', directErr);
      }

      // Secondary fallback strategy: Inspect per-pet assessments
      if (reportItems.length === 0) {
        const petsRes = await petApi.getPets();
        const petList = Array.isArray(petsRes) ? petsRes : (petsRes?.data || []);

        const reportAccumulator = [];

        await Promise.all(
          petList.map(async (pet) => {
            try {
              const assessRes = await petApi.getPetAssessments(pet.id);
              const assessments = Array.isArray(assessRes) ? assessRes : (assessRes?.data || []);

              for (const a of assessments) {
                try {
                  const repRes = await reportApi.getAssessmentReports(a.id);
                  const reps = Array.isArray(repRes) ? repRes : (repRes?.data || []);
                  for (const r of reps) {
                    reportAccumulator.push({
                      id: r.id,
                      assessment_id: a.id,
                      pet: pet,
                      created_at: r.generated_at || r.created_at || a.created_at,
                      triage_level:
                        r.summary?.risk_level ||
                        r.report_data?.risk_analysis?.risk_level ||
                        a.triage_level ||
                        'routine',
                      risk_score:
                        r.summary?.risk_score ??
                        r.report_data?.risk_analysis?.risk_score ??
                        a.risk_score,
                      symptoms_count:
                        r.symptoms_count ??
                        r.report_data?.symptoms?.length ??
                        r.report_data?.reported_symptoms?.length ??
                        (a.symptoms ? a.symptoms.length : 0),
                      is_emergency: Boolean(
                        r.summary?.is_emergency ??
                        r.report_data?.emergency?.is_emergency ??
                        r.report_data?.emergency_evaluation?.is_emergency ??
                        a.is_emergency
                      ),
                    });
                  }
                } catch {
                  // Assessment might not have a report yet
                }
              }
            } catch {
              // Assessment fetch error for single pet handled gracefully
            }
          })
        );
        reportItems = reportAccumulator;
      }

      // Deduplicate by report id
      const uniqueReportsMap = new Map();
      reportItems.forEach((r) => {
        if (r.id && !uniqueReportsMap.has(r.id)) {
          uniqueReportsMap.set(r.id, r);
        }
      });

      // Sort newest first
      const sorted = Array.from(uniqueReportsMap.values()).sort(
        (a, b) => new Date(b.created_at) - new Date(a.created_at)
      );

      setReports(sorted);
    } catch (err) {
      console.error('Failed to load reports:', err);
      setError(err.message || err.response?.data?.message || 'Failed to load veterinary reports.');
    } finally {
      setLoading(false);
    }
  };

  const filteredReports = reports.filter((r) => {
    const petName = (r.pet?.name || '').toLowerCase();
    const breed = (r.pet?.breed || '').toLowerCase();
    const reportId = (r.id ? String(r.id) : '').toLowerCase();
    const query = (searchQuery || '').toLowerCase();
    const matchesSearch =
      petName.includes(query) ||
      breed.includes(query) ||
      reportId.includes(query);

    const matchesTriage =
      selectedTriage === 'all' ||
      String(r.triage_level || '').toLowerCase() === selectedTriage.toLowerCase();

    return matchesSearch && matchesTriage;
  });

  return (
    <div style={{ backgroundColor: 'var(--color-bg)', minHeight: 'calc(100vh - 140px)', padding: '2rem 0 4rem' }}>
      <div className="container">
        {/* Page Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
          <div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0 0 0.25rem 0', color: 'var(--color-text-main)' }}>
              Veterinary Clinical Reports
            </h1>
            <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
              Historical triage summaries, risk analyses, and clinical handoff documents.
            </p>
          </div>

          <Link
            to="/assessments/new"
            className="btn btn-primary"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <Activity size={16} /> New Assessment
          </Link>
        </div>

        {/* Filter and Search Bar */}
        <div
          className="card"
          style={{
            padding: '1rem 1.25rem',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <div style={{ position: 'relative', flex: '1 1 260px' }}>
            <Search
              size={16}
              style={{
                position: 'absolute',
                left: '0.75rem',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--color-text-light)',
              }}
            />
            <input
              type="text"
              placeholder="Search by pet name or report ID..."
              className="form-input"
              style={{ paddingLeft: '2.25rem' }}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>Triage:</span>
            {['all', 'emergency', 'high', 'moderate', 'low'].map((level) => (
              <button
                key={level}
                onClick={() => setSelectedTriage(level)}
                className="btn btn-sm"
                style={{
                  borderRadius: 'var(--radius-full)',
                  backgroundColor: selectedTriage === level ? 'var(--color-primary)' : 'var(--color-surface)',
                  color: selectedTriage === level ? 'white' : 'var(--color-text-muted)',
                  border: '1px solid var(--color-border)',
                  textTransform: 'capitalize',
                  fontSize: '0.8rem',
                }}
              >
                {level}
              </button>
            ))}
          </div>
        </div>

        {/* Content Display */}
        {loading ? (
          <div style={{ padding: '3rem 0' }}>
            <LoadingSpinner message="Loading clinical reports repository..." />
          </div>
        ) : error ? (
          <ErrorMessage message={error} onRetry={fetchAllReports} />
        ) : filteredReports.length === 0 ? (
          <div className="card" style={{ padding: '3rem 1.5rem', textAlign: 'center' }}>
            <FileText size={48} color="var(--color-text-light)" style={{ marginBottom: '1rem' }} />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '0.5rem' }}>
              No Clinical Reports Found
            </h3>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', maxWidth: '420px', margin: '0 auto 1.5rem' }}>
              {reports.length === 0
                ? 'You have not generated any veterinary assessment reports yet. Complete an intake assessment to generate your first report.'
                : 'No reports matched your current search and triage filter.'}
            </p>
            {reports.length === 0 && (
              <Link to="/assessments/new" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                <Activity size={16} /> Start Assessment
              </Link>
            )}
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '1.25rem' }}>
            {filteredReports.map((rep) => {
              const petName = rep.pet?.name || 'Pet';
              const species = rep.pet?.species || 'dog';
              const speciesEmoji = getSpeciesEmoji(species);
              const dateStr = rep.created_at
                ? new Date(rep.created_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
                : 'Recent';

              return (
                <div
                  key={rep.id}
                  className="card"
                  style={{
                    padding: '1.5rem',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    border: rep.is_emergency ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid var(--color-border)',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.75rem', marginBottom: '1rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div
                          style={{
                            width: '44px',
                            height: '44px',
                            borderRadius: '12px',
                            backgroundColor: 'var(--color-surface)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '1.4rem',
                          }}
                        >
                          {speciesEmoji}
                        </div>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--color-text-main)' }}>
                            {petName}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                            {rep.pet?.breed || species}
                          </div>
                        </div>
                      </div>

                      <TriageBadge level={rep.triage_level} />
                    </div>

                    <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', display: 'flex', flexDirection: 'column', gap: '0.3rem', marginBottom: '1.25rem' }}>
                      <div>📅 <strong>Date:</strong> {dateStr}</div>
                      <div>
                        🎯 <strong>Risk Score:</strong>{' '}
                        {rep.risk_score != null ? `${rep.risk_score}/100` : 'Evaluated'}
                      </div>
                      <div>🩺 <strong>Symptoms logged:</strong> {rep.symptoms_count}</div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--color-border)', paddingTop: '1rem' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-light)', fontFamily: 'monospace' }}>
                      #{rep.id ? String(rep.id).slice(0, 8) : '--------'}
                    </span>
                    <Link
                      to={`/reports/${rep.id}`}
                      className="btn btn-outline btn-sm"
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
                    >
                      View Report <ArrowRight size={14} />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
