import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { petApi } from '../api/petApi';
import { apiClient } from '../api/client';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { EmptyState } from '../components/common/EmptyState';
import { TriageBadge } from '../components/common/TriageBadge';
import { getSpeciesEmoji } from '../utils/petSpecies';
import { 
  PlusCircle, 
  FolderHeart, 
  FileText, 
  Activity, 
  ArrowRight, 
  Calendar, 
  ShieldAlert,
  ChevronRight,
  Clock
} from 'lucide-react';

export const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [pets, setPets] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch pets
        const petsData = await petApi.getPets();
        const petsList = Array.isArray(petsData) ? petsData : (petsData?.data || []);
        setPets(petsList);

        // Fetch recent assessments across pets
        const allAssessments = [];
        for (const pet of petsList.slice(0, 5)) {
          try {
            const petAsmts = await petApi.getPetAssessments(pet.id);
            const asmtList = Array.isArray(petAsmts) ? petAsmts : (petAsmts?.data || []);
            asmtList.forEach((a) => {
              allAssessments.push({ ...a, pet_name: pet.name, pet_species: pet.species });
            });
          } catch {
            // Ignore single pet failure
          }
        }

        // Sort latest first
        allAssessments.sort((a, b) => {
          const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
          const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
          return dateB - dateA;
        });
        setAssessments(allAssessments.slice(0, 6));

      } catch (err) {
        console.error('Failed to load dashboard data:', err);
        setError(err.message || 'Failed to load dashboard data.');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) return <LoadingSpinner fullScreen label="Loading clinical overview..." />;

  return (
    <div className="container" style={{ padding: '36px 24px 60px' }}>
      {/* Welcome Banner */}
      <div style={{
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-light)',
        borderRadius: 'var(--radius-xl)',
        padding: '32px',
        marginBottom: '32px',
        boxShadow: 'var(--shadow-sm)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '20px',
        background: 'linear-gradient(135deg, #ffffff 0%, #f0fdfa 100%)',
      }}>
        <div>
          <span style={{
            fontSize: '12px',
            fontWeight: '700',
            color: 'var(--primary)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            display: 'block',
            marginBottom: '4px',
          }}>
            Clinical Health Portal
          </span>
          <h1 style={{ fontSize: '26px', fontWeight: '800', color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
            Welcome back, {user?.name || 'Pet Caregiver'}
          </h1>
          <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Monitor vital indicators, conduct early triage screenings, and manage veterinary handoff reports.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <Link to="/assessments/new" className="btn btn-primary btn-lg">
            <PlusCircle size={18} />
            New Assessment
          </Link>
          <Link to="/pets" className="btn btn-secondary btn-lg">
            <FolderHeart size={18} />
            Manage Pets
          </Link>
        </div>
      </div>

      {error && <ErrorMessage message={error} />}

      {/* Metrics Grid */}
      <div className="grid-3" style={{ marginBottom: '36px' }}>
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '18px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--primary-light)',
            color: 'var(--primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <FolderHeart size={24} />
          </div>
          <div>
            <div style={{ fontSize: '28px', fontWeight: '800', color: 'var(--text-main)', lineHeight: 1.1 }}>
              {pets.length}
            </div>
            <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-muted)' }}>
              Registered Pets
            </div>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '18px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--secondary-light)',
            color: 'var(--secondary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Activity size={24} />
          </div>
          <div>
            <div style={{ fontSize: '28px', fontWeight: '800', color: 'var(--text-main)', lineHeight: 1.1 }}>
              {assessments.length}
            </div>
            <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-muted)' }}>
              Total Assessments
            </div>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '18px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: '#f5f3ff',
            color: '#7c3aed',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <FileText size={24} />
          </div>
          <div>
            <div style={{ fontSize: '28px', fontWeight: '800', color: 'var(--text-main)', lineHeight: 1.1 }}>
              {(Array.isArray(assessments) ? assessments : []).filter(a => a.status === 'completed').length}
            </div>
            <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-muted)' }}>
              Completed Clinical Sessions
            </div>
          </div>
        </div>
      </div>

      {/* Pets Section */}
      <section style={{ marginBottom: '40px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '700', color: 'var(--text-main)' }}>
              Your Pet Profiles
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Select a pet to launch an assessment or view history
            </p>
          </div>
          <Link to="/pets" className="btn btn-sm btn-outline-primary">
            View All ({Array.isArray(pets) ? pets.length : 0})
          </Link>
        </div>

        {(!Array.isArray(pets) || pets.length === 0) ? (
          <EmptyState
            icon={FolderHeart}
            title="No pets added yet"
            description="Register your pet to begin monitoring symptoms, vital observations, and health indicators."
            actionLabel="+ Register First Pet"
            onAction={() => navigate('/pets')}
          />
        ) : (
          <div className="grid-3">
            {pets.slice(0, 3).map((pet) => (
              <div key={pet.id} className="card card-interactive" onClick={() => navigate(`/pets/${pet.id}`)}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div
                      style={{
                        width: '38px',
                        height: '38px',
                        borderRadius: '10px',
                        backgroundColor: 'var(--bg-muted)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '20px',
                      }}
                    >
                      {getSpeciesEmoji(pet.species)}
                    </div>
                    <div>
                      <h3 style={{ fontSize: '17px', fontWeight: '700', color: 'var(--text-main)', margin: 0 }}>
                        {pet.name}
                      </h3>
                      <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                        {pet.species} • {pet.breed || 'Mixed'}
                      </span>
                    </div>
                  </div>
                  <span className="badge badge-neutral">
                    {pet.sex || 'Unknown'}
                  </span>
                </div>

                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '18px', display: 'flex', gap: '16px' }}>
                  <span>Weight: <strong>{pet.weight ? `${pet.weight} kg` : 'N/A'}</strong></span>
                  <span>Age: <strong>{pet.age ? `${pet.age} yrs` : 'Unknown'}</strong></span>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/assessments/new?pet_id=${pet.id}`);
                    }}
                    className="btn btn-sm btn-primary"
                    style={{ flex: 1 }}
                  >
                    <PlusCircle size={14} /> Start Assessment
                  </button>
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/pets/${pet.id}`);
                    }}
                    className="btn btn-sm btn-secondary"
                  >
                    Profile
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Recent Assessments Section */}
      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '700', color: 'var(--text-main)' }}>
              Recent Health Assessments
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Review active intakes and generated veterinary summaries
            </p>
          </div>
          <Link to="/reports" className="btn btn-sm btn-secondary">
            View All Reports
          </Link>
        </div>

        {(!Array.isArray(assessments) || assessments.length === 0) ? (
          <EmptyState
            icon={Activity}
            title="No assessments recorded yet"
            description="Start your first AI-assisted clinical health intake to receive explainable triage analysis."
            actionLabel="Start First Assessment"
            onAction={() => navigate('/assessments/new')}
          />
        ) : (
          <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--bg-muted)', borderBottom: '1px solid var(--border-light)' }}>
                  <th style={{ padding: '14px 20px', fontWeight: '600', color: 'var(--text-muted)' }}>Pet</th>
                  <th style={{ padding: '14px 20px', fontWeight: '600', color: 'var(--text-muted)' }}>Date</th>
                  <th style={{ padding: '14px 20px', fontWeight: '600', color: 'var(--text-muted)' }}>Status</th>
                  <th style={{ padding: '14px 20px', fontWeight: '600', color: 'var(--text-muted)' }}>Symptoms</th>
                  <th style={{ padding: '14px 20px', fontWeight: '600', color: 'var(--text-muted)' }}>Triage Risk</th>
                  <th style={{ padding: '14px 20px', fontWeight: '600', color: 'var(--text-muted)', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {(Array.isArray(assessments) ? assessments : []).map((a) => {
                  const dateStr = a.created_at ? new Date(a.created_at).toLocaleDateString() : 'Recent';
                  const symCount = Array.isArray(a.symptoms) ? a.symptoms.length : 0;
                  const isCompleted = a.status === 'completed';

                  return (
                    <tr key={a.id} style={{ borderBottom: '1px solid var(--border-subtle)', transition: 'background 0.15s ease' }}>
                      <td style={{ padding: '14px 20px', fontWeight: '600', color: 'var(--text-main)' }}>
                        {a.pet_name || 'Pet'}
                      </td>
                      <td style={{ padding: '14px 20px', color: 'var(--text-muted)' }}>
                        {dateStr}
                      </td>
                      <td style={{ padding: '14px 20px' }}>
                        <span className={`badge ${isCompleted ? 'badge-low' : 'badge-neutral'}`}>
                          {a.status || 'in_progress'}
                        </span>
                      </td>
                      <td style={{ padding: '14px 20px', color: 'var(--text-muted)' }}>
                        {symCount} reported
                      </td>
                      <td style={{ padding: '14px 20px' }}>
                        {a.risk_analysis ? (
                          <TriageBadge level={a.risk_analysis.risk_level} size="sm" />
                        ) : (
                          <span style={{ fontSize: '12px', color: 'var(--text-subtle)' }}>Pending analysis</span>
                        )}
                      </td>
                      <td style={{ padding: '14px 20px', textAlign: 'right' }}>
                        <button
                          onClick={() => navigate(`/assessments/new?resume_id=${a.id}`)}
                          className="btn btn-sm btn-outline-primary"
                        >
                          {isCompleted ? 'View Report' : 'Continue Intake'}
                          <ChevronRight size={14} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
};

export default DashboardPage;
