import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Heart,
  ArrowLeft,
  Calendar,
  Weight,
  AlertCircle,
  FileText,
  PlusCircle,
  Edit2,
  Trash2,
  Activity,
  CheckCircle2,
  Clock,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react';
import { petApi } from '../api/petApi';
import TriageBadge from '../components/common/TriageBadge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import Modal from '../components/common/Modal';
import { DAILY_LIFE_SPECIES, getSpeciesEmoji } from '../utils/petSpecies';

export default function PetDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [pet, setPet] = useState(null);
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Edit Modal State
  const [showEditModal, setShowEditModal] = useState(false);
  const [editFormData, setEditFormData] = useState({});
  const [savingEdit, setSavingEdit] = useState(false);
  const [editError, setEditError] = useState(null);

  // Delete Modal State
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetchPetData();
  }, [id]);

  const fetchPetData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [petRes, assessRes] = await Promise.all([
        petApi.getPet(id),
        petApi.getPetAssessments(id).catch(() => ({ data: [] })),
      ]);

      const petData = petRes.data || petRes;
      setPet(petData);
      setAssessments(assessRes.data || assessRes || []);
      setEditFormData({
        name: petData.name || '',
        species: petData.species || 'dog',
        breed: petData.breed || '',
        age_years: petData.age_years || '',
        weight_kg: petData.weight_kg || '',
        gender: petData.gender || 'unknown',
        is_neutered: Boolean(petData.is_neutered),
        known_allergies: petData.known_allergies || '',
        chronic_conditions: petData.chronic_conditions || '',
      });
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load pet details. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePet = async (e) => {
    e.preventDefault();
    try {
      setSavingEdit(true);
      setEditError(null);
      const finalSpecies =
        editFormData.species === 'Other' && editFormData.custom_species?.trim()
          ? editFormData.custom_species.trim()
          : (editFormData.species || 'Dog');

      const payload = {
        name: editFormData.name ? editFormData.name.trim() : '',
        species: finalSpecies,
        breed: editFormData.breed?.trim() ? editFormData.breed.trim() : null,
        sex: editFormData.sex || editFormData.gender || null,
        date_of_birth: editFormData.date_of_birth?.trim() ? editFormData.date_of_birth.trim() : null,
        weight: editFormData.weight && !isNaN(parseFloat(editFormData.weight))
          ? parseFloat(editFormData.weight)
          : (editFormData.weight_kg && !isNaN(parseFloat(editFormData.weight_kg)) ? parseFloat(editFormData.weight_kg) : null),
        allergies: editFormData.allergies?.trim() || editFormData.known_allergies?.trim() || null,
        existing_conditions: editFormData.existing_conditions?.trim() || editFormData.chronic_conditions?.trim() || null,
        current_medications: editFormData.current_medications?.trim() || null,
        vaccination_status: editFormData.vaccination_status?.trim() || null,
      };
      const res = await petApi.updatePet(id, payload);
      setPet(res.data || res);
      setShowEditModal(false);
    } catch (err) {
      setEditError(err.response?.data?.message || err.message || 'Failed to update pet.');
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDeletePet = async () => {
    try {
      setDeleting(true);
      await petApi.deletePet(id);
      navigate('/pets');
    } catch (err) {
      alert(err.response?.data?.message || err.message || 'Failed to delete pet.');
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="container" style={{ padding: '4rem 1rem' }}>
        <LoadingSpinner message="Loading pet profile..." />
      </div>
    );
  }

  if (error || !pet) {
    return (
      <div className="container" style={{ padding: '3rem 1rem' }}>
        <ErrorMessage message={error || 'Pet not found.'} onRetry={fetchPetData} />
        <button
          onClick={() => navigate('/pets')}
          className="btn btn-outline"
          style={{ marginTop: '1rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <ArrowLeft size={16} /> Back to Pets
        </button>
      </div>
    );
  }

  const speciesEmoji = getSpeciesEmoji(pet.species);

  return (
    <div style={{ backgroundColor: 'var(--color-bg)', minHeight: 'calc(100vh - 140px)', padding: '2rem 0 4rem' }}>
      <div className="container">
        {/* Navigation Breadcrumb */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
          <button
            onClick={() => navigate('/pets')}
            className="btn btn-outline btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <ArrowLeft size={16} /> All Pets
          </button>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => setShowEditModal(true)}
              className="btn btn-outline btn-sm"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <Edit2 size={15} /> Edit Profile
            </button>
            <button
              onClick={() => setShowDeleteModal(true)}
              className="btn btn-outline btn-sm"
              style={{ color: 'var(--color-danger)', borderColor: 'var(--color-border)', display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <Trash2 size={15} /> Delete
            </button>
          </div>
        </div>

        {/* Pet Profile Hero Card */}
        <div className="card" style={{ padding: '2rem', marginBottom: '2rem', background: 'linear-gradient(135deg, white, var(--color-surface))' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
              <div
                style={{
                  width: '80px',
                  height: '80px',
                  borderRadius: '20px',
                  backgroundColor: 'var(--color-primary-light)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '2.5rem',
                  boxShadow: 'var(--shadow-sm)',
                }}
              >
                {speciesEmoji}
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
                  <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--color-text-main)', margin: 0 }}>
                    {pet.name}
                  </h1>
                  <span
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      padding: '0.2rem 0.6rem',
                      borderRadius: 'var(--radius-full)',
                      backgroundColor: 'var(--color-surface-hover)',
                      color: 'var(--color-text-muted)',
                    }}
                  >
                    {pet.species}
                  </span>
                </div>
                <p style={{ color: 'var(--color-text-muted)', margin: 0, fontSize: '0.95rem' }}>
                  {pet.breed || 'Mixed Breed'} • {pet.gender ? pet.gender.toUpperCase() : 'UNKNOWN'} • {pet.is_neutered ? 'Neutered/Spayed' : 'Intact'}
                </p>
              </div>
            </div>

            <Link
              to={`/assessments/new?petId=${pet.id}`}
              className="btn btn-primary"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1.5rem' }}
            >
              <Activity size={18} />
              Start New Health Assessment
            </Link>
          </div>

          {/* Quick Metrics Bar */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '1rem',
              marginTop: '1.75rem',
              paddingTop: '1.5rem',
              borderTop: '1px solid var(--color-border)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ padding: '0.5rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-surface)' }}>
                <Calendar size={18} color="var(--color-primary)" />
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Age</div>
                <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                  {pet.age_years != null ? `${pet.age_years} yrs` : 'Not recorded'}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ padding: '0.5rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-surface)' }}>
                <Weight size={18} color="var(--color-primary)" />
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Weight</div>
                <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                  {pet.weight_kg != null ? `${pet.weight_kg} kg` : 'Not recorded'}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ padding: '0.5rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-surface)' }}>
                <AlertCircle size={18} color="var(--color-warning)" />
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Allergies</div>
                <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                  {pet.known_allergies || 'None recorded'}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ padding: '0.5rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-surface)' }}>
                <FileText size={18} color="var(--color-info)" />
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Assessments</div>
                <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                  {assessments.length} Completed / In-Progress
                </div>
              </div>
            </div>
          </div>

          {pet.chronic_conditions && (
            <div
              style={{
                marginTop: '1.25rem',
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'rgba(234, 88, 12, 0.08)',
                border: '1px solid rgba(234, 88, 12, 0.2)',
                fontSize: '0.875rem',
                color: 'var(--color-text-main)',
              }}
            >
              <strong>Chronic Conditions / Medical Notes:</strong> {pet.chronic_conditions}
            </div>
          )}
        </div>

        {/* Assessment History Section */}
        <div className="card" style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 0.25rem 0' }}>
                Health Assessment History
              </h2>
              <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', margin: 0 }}>
                Past triage evaluations, symptom records, and veterinary handoffs for {pet.name}.
              </p>
            </div>
            <Link
              to={`/assessments/new?petId=${pet.id}`}
              className="btn btn-outline btn-sm"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <PlusCircle size={15} /> New Intake
            </Link>
          </div>

          {assessments.length === 0 ? (
            <div
              style={{
                textAlign: 'center',
                padding: '3rem 1rem',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-surface)',
                border: '1px dashed var(--color-border)',
              }}
            >
              <Activity size={36} color="var(--color-text-light)" style={{ marginBottom: '0.75rem' }} />
              <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.25rem' }}>No assessments recorded yet</h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', maxWidth: '400px', margin: '0 auto 1.25rem' }}>
                Start a guided assessment to check {pet.name}&apos;s symptoms, run AI risk scoring, and generate a clinical veterinary report.
              </p>
              <Link
                to={`/assessments/new?petId=${pet.id}`}
                className="btn btn-primary btn-sm"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
              >
                <Activity size={15} /> Start First Assessment
              </Link>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {assessments.map((a) => {
                const dateStr = a.created_at
                  ? new Date(a.created_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
                  : 'Unknown date';
                const triageLevel = a.triage_level || a.risk_analysis?.triage_level || 'pending';
                const score = a.risk_score ?? a.risk_analysis?.risk_score;

                return (
                  <div
                    key={a.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '1rem 1.25rem',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--color-surface)',
                      border: '1px solid var(--color-border)',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <div
                        style={{
                          width: '40px',
                          height: '40px',
                          borderRadius: '10px',
                          backgroundColor: 'var(--color-surface-hover)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'var(--color-primary)',
                        }}
                      >
                        <FileText size={18} />
                      </div>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.2rem' }}>
                          <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                            Assessment #{a.id.slice(0, 8)}
                          </span>
                          <TriageBadge level={triageLevel} />
                          {a.status && (
                            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'capitalize' }}>
                              ({a.status})
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', display: 'flex', gap: '1rem' }}>
                          <span>📅 {dateStr}</span>
                          {score !== undefined && score !== null && (
                            <span>🎯 Risk Score: {score}/100</span>
                          )}
                          {a.symptoms_count !== undefined && (
                            <span>🩺 {a.symptoms_count} symptom(s)</span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      {a.report_id ? (
                        <Link to={`/reports/${a.report_id}`} className="btn btn-outline btn-sm">
                          View Report
                        </Link>
                      ) : (
                        <Link to={`/assessments/new?resumeId=${a.id}&petId=${pet.id}`} className="btn btn-primary btn-sm">
                          Continue Intake
                        </Link>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Edit Pet Modal */}
      <Modal isOpen={showEditModal} onClose={() => setShowEditModal(false)} title={`Edit ${pet.name}'s Profile`}>
        <form onSubmit={handleUpdatePet} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {editError && <div className="alert alert-danger">{editError}</div>}
          
          <div>
            <label className="form-label">Pet Name *</label>
            <input
              type="text"
              className="form-input"
              value={editFormData.name || ''}
              onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
              required
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label className="form-label">Species *</label>
              <select
                className="form-input"
                value={editFormData.species || 'Dog'}
                onChange={(e) => setEditFormData({ ...editFormData, species: e.target.value })}
              >
                {DAILY_LIFE_SPECIES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="form-label">Breed</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Mixed, Golden Retriever"
                value={editFormData.breed || ''}
                onChange={(e) => setEditFormData({ ...editFormData, breed: e.target.value })}
              />
            </div>
          </div>

          {editFormData.species === 'Other' && (
            <div style={{ marginTop: '0.75rem' }}>
              <label className="form-label">Specify Custom Species *</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Chinchilla, Hedgehog, Duck"
                value={editFormData.custom_species || ''}
                onChange={(e) => setEditFormData({ ...editFormData, custom_species: e.target.value })}
                required
              />
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label className="form-label">Age (Years)</label>
              <input
                type="number"
                step="0.1"
                className="form-input"
                value={editFormData.age_years || ''}
                onChange={(e) => setEditFormData({ ...editFormData, age_years: e.target.value })}
              />
            </div>
            <div>
              <label className="form-label">Weight (kg)</label>
              <input
                type="number"
                step="0.1"
                className="form-input"
                value={editFormData.weight_kg || ''}
                onChange={(e) => setEditFormData({ ...editFormData, weight_kg: e.target.value })}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label className="form-label">Gender</label>
              <select
                className="form-input"
                value={editFormData.gender || 'unknown'}
                onChange={(e) => setEditFormData({ ...editFormData, gender: e.target.value })}
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="unknown">Unknown</option>
              </select>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', marginTop: '1.75rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.9rem' }}>
                <input
                  type="checkbox"
                  checked={Boolean(editFormData.is_neutered)}
                  onChange={(e) => setEditFormData({ ...editFormData, is_neutered: e.target.checked })}
                />
                Neutered / Spayed
              </label>
            </div>
          </div>

          <div>
            <label className="form-label">Known Allergies</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g., Chicken, penicillin"
              value={editFormData.known_allergies || ''}
              onChange={(e) => setEditFormData({ ...editFormData, known_allergies: e.target.value })}
            />
          </div>

          <div>
            <label className="form-label">Chronic Conditions / History</label>
            <textarea
              className="form-input"
              rows={3}
              placeholder="e.g., Mild arthritis, previous ear infections"
              value={editFormData.chronic_conditions || ''}
              onChange={(e) => setEditFormData({ ...editFormData, chronic_conditions: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <button type="button" onClick={() => setShowEditModal(false)} className="btn btn-outline" disabled={savingEdit}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={savingEdit}>
              {savingEdit ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={showDeleteModal} onClose={() => setShowDeleteModal(false)} title={`Delete ${pet.name}?`}>
        <div style={{ padding: '0.5rem 0' }}>
          <p style={{ color: 'var(--color-text-main)', fontSize: '0.95rem', marginBottom: '1rem' }}>
            Are you sure you want to delete <strong>{pet.name}</strong>? This action cannot be undone and will permanently delete all associated assessment records and history.
          </p>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button onClick={() => setShowDeleteModal(false)} className="btn btn-outline" disabled={deleting}>
              Cancel
            </button>
            <button
              onClick={handleDeletePet}
              className="btn btn-danger"
              style={{ backgroundColor: 'var(--color-danger)', color: 'white' }}
              disabled={deleting}
            >
              {deleting ? 'Deleting...' : 'Permanently Delete'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
