import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { petApi } from '../api/petApi';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { EmptyState } from '../components/common/EmptyState';
import { Modal } from '../components/common/Modal';
import { DAILY_LIFE_SPECIES, getSpeciesEmoji } from '../utils/petSpecies';
import { 
  FolderHeart, 
  PlusCircle, 
  Edit2, 
  Trash2, 
  Activity, 
  AlertTriangle,
  HeartPulse
} from 'lucide-react';

export const PetsPage = () => {
  const navigate = useNavigate();

  const [pets, setPets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingPet, setEditingPet] = useState(null);
  const [deletingPet, setDeletingPet] = useState(null);
  const [saving, setSaving] = useState(false);

  // Form fields
  const [formData, setFormData] = useState({
    name: '',
    species: 'Dog',
    custom_species: '',
    breed: '',
    sex: 'Male Neutered',
    date_of_birth: '',
    weight: '',
    allergies: '',
    existing_conditions: '',
    current_medications: '',
    vaccination_status: 'Up to date',
  });

  const fetchPets = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await petApi.getPets();
      setPets(data || []);
    } catch (err) {
      setError(err.message || 'Failed to load pets list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPets();
  }, []);

  const openAddModal = () => {
    setEditingPet(null);
    setFormData({
      name: '',
      species: 'Dog',
      custom_species: '',
      breed: '',
      sex: 'Male Neutered',
      date_of_birth: '',
      weight: '',
      allergies: '',
      existing_conditions: '',
      current_medications: '',
      vaccination_status: 'Up to date',
    });
    setIsModalOpen(true);
  };

  const openEditModal = (pet) => {
    setEditingPet(pet);
    const isStandardSpecies = DAILY_LIFE_SPECIES.some((s) => s.value.toLowerCase() === (pet.species || '').toLowerCase());
    setFormData({
      name: pet.name || '',
      species: isStandardSpecies ? pet.species : 'Other',
      custom_species: isStandardSpecies ? '' : (pet.species || ''),
      breed: pet.breed || '',
      sex: pet.sex || 'Male Neutered',
      date_of_birth: pet.date_of_birth || '',
      weight: pet.weight ? String(pet.weight) : '',
      allergies: pet.allergies || '',
      existing_conditions: pet.existing_conditions || '',
      current_medications: pet.current_medications || '',
      vaccination_status: pet.vaccination_status || 'Up to date',
    });
    setIsModalOpen(true);
  };

  const handleSavePet = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    const finalSpecies =
      formData.species === 'Other' && formData.custom_species?.trim()
        ? formData.custom_species.trim()
        : (formData.species || 'Dog');

    const payload = {
      name: formData.name ? formData.name.trim() : '',
      species: finalSpecies,
      breed: formData.breed?.trim() ? formData.breed.trim() : null,
      sex: formData.sex || null,
      date_of_birth: formData.date_of_birth && formData.date_of_birth.trim() ? formData.date_of_birth.trim() : null,
      weight: formData.weight && !isNaN(parseFloat(formData.weight)) ? parseFloat(formData.weight) : null,
      allergies: formData.allergies?.trim() ? formData.allergies.trim() : null,
      existing_conditions: formData.existing_conditions?.trim() ? formData.existing_conditions.trim() : null,
      current_medications: formData.current_medications?.trim() ? formData.current_medications.trim() : null,
      vaccination_status: formData.vaccination_status?.trim() ? formData.vaccination_status.trim() : null,
    };

    try {
      if (editingPet) {
        await petApi.updatePet(editingPet.id, payload);
      } else {
        await petApi.createPet(payload);
      }
      setIsModalOpen(false);
      fetchPets();
    } catch (err) {
      const errData = err.response?.data;
      let errMsg = errData?.message || err.message || 'Failed to save pet profile.';
      if (errData?.errors) {
        const fieldErrors = Object.entries(errData.errors)
          .map(([f, msgs]) => `${f}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
          .join(' | ');
        errMsg = `${errMsg} (${fieldErrors})`;
      }
      setError(errMsg);
    } finally {
      setSaving(false);
    }
  };

  const handleDeletePet = async () => {
    if (!deletingPet) return;
    setSaving(true);
    try {
      await petApi.deletePet(deletingPet.id);
      setDeletingPet(null);
      fetchPets();
    } catch (err) {
      setError(err.message || 'Failed to delete pet profile.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="container" style={{ padding: '36px 24px 60px' }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">Pet Health Profiles</h1>
          <p className="page-subtitle">
            Manage demographics, medical background, and chronic conditions
          </p>
        </div>
        <button onClick={openAddModal} className="btn btn-primary">
          <PlusCircle size={18} /> Add New Pet
        </button>
      </div>

      {error && <ErrorMessage message={error} onRetry={fetchPets} />}

      {loading ? (
        <LoadingSpinner fullScreen label="Loading pet profiles..." />
      ) : pets.length === 0 ? (
        <EmptyState
          icon={FolderHeart}
          title="No registered pets"
          description="Register your pet to record symptoms, calculate health risk indicators, and prepare veterinary handoff reports."
          actionLabel="+ Add Your First Pet"
          onAction={openAddModal}
        />
      ) : (
        <div className="grid-3">
          {pets.map((pet) => (
            <div key={pet.id} className="card" style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div
                    style={{
                      width: '44px',
                      height: '44px',
                      borderRadius: '12px',
                      backgroundColor: 'var(--bg-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '22px',
                    }}
                  >
                    {getSpeciesEmoji(pet.species)}
                  </div>
                  <div>
                    <h3 style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-main)', margin: 0 }}>
                      {pet.name}
                    </h3>
                    <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                      {pet.species} • {pet.breed || 'Mixed Breed'}
                    </span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button 
                    onClick={() => openEditModal(pet)} 
                    className="btn btn-sm btn-secondary" 
                    title="Edit profile"
                  >
                    <Edit2 size={13} />
                  </button>
                  <button 
                    onClick={() => setDeletingPet(pet)} 
                    className="btn btn-sm btn-danger" 
                    title="Delete pet"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>

              <div style={{
                backgroundColor: 'var(--bg-muted)',
                borderRadius: 'var(--radius-md)',
                padding: '12px 14px',
                fontSize: '12px',
                color: 'var(--text-main)',
                marginBottom: '16px',
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '8px',
              }}>
                <div><span style={{ color: 'var(--text-muted)' }}>Sex:</span> <strong>{pet.sex || 'Unknown'}</strong></div>
                <div><span style={{ color: 'var(--text-muted)' }}>Weight:</span> <strong>{pet.weight ? `${pet.weight} kg` : 'Unrecorded'}</strong></div>
                <div><span style={{ color: 'var(--text-muted)' }}>Age:</span> <strong>{pet.age ? `${pet.age} years` : 'Unknown'}</strong></div>
                <div><span style={{ color: 'var(--text-muted)' }}>Vaccines:</span> <strong>{pet.vaccination_status || 'Unrecorded'}</strong></div>
              </div>

              {(pet.allergies || pet.existing_conditions) && (
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
                  {pet.allergies && <div>Allergies: <span style={{ color: '#b45309' }}>{pet.allergies}</span></div>}
                  {pet.existing_conditions && <div>Conditions: <span style={{ color: 'var(--text-main)' }}>{pet.existing_conditions}</span></div>}
                </div>
              )}

              <div style={{ marginTop: 'auto', display: 'flex', gap: '8px', paddingTop: '12px' }}>
                <button
                  onClick={() => navigate(`/assessments/new?pet_id=${pet.id}`)}
                  className="btn btn-sm btn-primary"
                  style={{ flex: 1 }}
                >
                  <HeartPulse size={14} /> Start Assessment
                </button>
                <button
                  onClick={() => navigate(`/pets/${pet.id}`)}
                  className="btn btn-sm btn-secondary"
                >
                  History
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add / Edit Pet Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingPet ? `Edit Profile: ${editingPet.name}` : 'Register New Pet Profile'}
        maxWidth="600px"
      >
        <form onSubmit={handleSavePet}>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label" htmlFor="pet-name">Pet Name *</label>
              <input
                id="pet-name"
                type="text"
                className="form-input"
                placeholder="e.g. Max, Bella"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="pet-species">Species *</label>
              <select
                id="pet-species"
                className="form-select"
                value={formData.species}
                onChange={(e) => setFormData({ ...formData, species: e.target.value })}
                required
              >
                {DAILY_LIFE_SPECIES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {formData.species === 'Other' && (
            <div className="form-group" style={{ marginBottom: '16px' }}>
              <label className="form-label" htmlFor="pet-custom-species">Specify Pet Species *</label>
              <input
                id="pet-custom-species"
                type="text"
                className="form-input"
                placeholder="e.g. Chinchilla, Duck, Hedgehog, Pigeon"
                value={formData.custom_species || ''}
                onChange={(e) => setFormData({ ...formData, custom_species: e.target.value })}
                required
              />
            </div>
          )}

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label" htmlFor="pet-breed">Breed</label>
              <input
                id="pet-breed"
                type="text"
                className="form-input"
                placeholder="e.g. Golden Retriever, Holland Lop, Cockatiel"
                value={formData.breed}
                onChange={(e) => setFormData({ ...formData, breed: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="pet-sex">Sex / Reproductive Status</label>
              <select
                id="pet-sex"
                className="form-select"
                value={formData.sex}
                onChange={(e) => setFormData({ ...formData, sex: e.target.value })}
              >
                <option value="Male Neutered">Male (Neutered)</option>
                <option value="Male Intact">Male (Intact)</option>
                <option value="Female Spayed">Female (Spayed)</option>
                <option value="Female Intact">Female (Intact)</option>
                <option value="Unknown">Unknown / Unspecified</option>
              </select>
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label" htmlFor="pet-dob">Date of Birth</label>
              <input
                id="pet-dob"
                type="date"
                className="form-input"
                value={formData.date_of_birth}
                onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="pet-weight">Weight (kg)</label>
              <input
                id="pet-weight"
                type="number"
                step="0.1"
                min="0.1"
                className="form-input"
                placeholder="e.g. 14.5"
                value={formData.weight}
                onChange={(e) => setFormData({ ...formData, weight: e.target.value })}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="pet-allergies">Known Allergies</label>
            <input
              id="pet-allergies"
              type="text"
              className="form-input"
              placeholder="e.g. Chicken, Penicillin, Fleas (or None)"
              value={formData.allergies}
              onChange={(e) => setFormData({ ...formData, allergies: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="pet-conditions">Pre-existing Clinical Conditions</label>
            <input
              id="pet-conditions"
              type="text"
              className="form-input"
              placeholder="e.g. Hip dysplasia, Diabetes, Cardiac murmur"
              value={formData.existing_conditions}
              onChange={(e) => setFormData({ ...formData, existing_conditions: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="pet-meds">Current Medications & Dosages</label>
            <input
              id="pet-meds"
              type="text"
              className="form-input"
              placeholder="e.g. Glucosamine daily, Apoquel 16mg"
              value={formData.current_medications}
              onChange={(e) => setFormData({ ...formData, current_medications: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '24px' }}>
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={saving}
            >
              {saving ? 'Saving...' : (editingPet ? 'Update Profile' : 'Save Pet Profile')}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={Boolean(deletingPet)}
        onClose={() => setDeletingPet(null)}
        title="Confirm Deletion"
        maxWidth="440px"
      >
        <div style={{ display: 'flex', gap: '14px', alignItems: 'flex-start', marginBottom: '20px' }}>
          <AlertTriangle size={24} color="#dc2626" style={{ flexShrink: 0 }} />
          <div>
            <p style={{ fontSize: '14px', color: 'var(--text-main)', lineHeight: 1.5 }}>
              Are you sure you want to delete <strong>{deletingPet?.name}</strong>?
            </p>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
              All attached health assessments, uploaded photographs, and generated reports for this pet will be permanently removed.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button onClick={() => setDeletingPet(null)} className="btn btn-secondary">
            Cancel
          </button>
          <button onClick={handleDeletePet} className="btn btn-danger" disabled={saving}>
            {saving ? 'Deleting...' : 'Delete Pet Permanently'}
          </button>
        </div>
      </Modal>
    </div>
  );
};

export default PetsPage;
