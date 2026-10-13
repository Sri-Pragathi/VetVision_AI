import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { petApi } from '../api/petApi';
import { assessmentApi } from '../api/assessmentApi';
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
  Clock,
  AlertTriangle,
  PhoneCall,
  Sparkles,
  Bot,
  MessageSquare
} from 'lucide-react';

export const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [pets, setPets] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [activeDraft, setActiveDraft] = useState(null);
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

        // Fetch active in-progress draft if any
        try {
          const draftRes = await assessmentApi.getActiveDraft();
          const draftData = draftRes?.data || draftRes;
          if (draftData && draftData.id && draftData.status === 'in_progress') {
            setActiveDraft(draftData);
          }
        } catch {
          // Non-blocking
        }

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

  const hour = new Date().getHours();
  const greetingTime = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
  const ownerName = user?.name ? user.name.replace(/^dr\.?\s+/i, '').replace(/,\s*dvm/i, '').trim() : '';
  const greetingHeading = ownerName
    ? `${greetingTime}, ${ownerName}!`
    : `${greetingTime}! Welcome back.`;

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
            Pet Owner Portal &bull; AI Pet Care Assistant
          </span>
          <h1 style={{ fontSize: '26px', fontWeight: '800', color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
            {greetingHeading}
          </h1>
          <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginTop: '4px' }}>
            How can we help your pet today? Monitor health indicators, review AI care guides, and keep your pets safe.
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

      {/* Prominent Continue In-Progress Intake Card */}
      {activeDraft && (
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '2px solid var(--color-primary, #0d9488)',
            borderRadius: 'var(--radius-xl)',
            padding: '24px 28px',
            marginBottom: '32px',
            boxShadow: 'var(--shadow-sm)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '16px',
            background: 'linear-gradient(135deg, #f0fdfa 0%, #ecfeff 100%)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div
              style={{
                width: '52px',
                height: '52px',
                borderRadius: '16px',
                backgroundColor: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#0d9488',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <Clock size={28} />
            </div>
            <div>
              <span style={{ fontSize: '11px', fontWeight: 800, color: '#0d9488', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Active Intake Session
              </span>
              <h3 style={{ fontSize: '18px', fontWeight: 800, margin: '2px 0 4px', color: 'var(--text-main)' }}>
                Resume Assessment for {pets.find((p) => p.id === activeDraft.pet_id)?.name || 'Your Pet'}
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: 0 }}>
                Paused at <strong>Step {activeDraft.current_step || 2}</strong> &bull; All symptoms, responses, and observations were preserved
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={() => setActiveDraft(null)}
              className="btn btn-sm btn-secondary"
            >
              Dismiss
            </button>
            <button
              onClick={() => navigate(`/assessments/new?resumeId=${activeDraft.id}&petId=${activeDraft.pet_id}`)}
              className="btn btn-sm btn-primary"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '8px 18px', fontWeight: 700 }}
            >
              Continue {pets.find((p) => p.id === activeDraft.pet_id)?.name ? `${pets.find((p) => p.id === activeDraft.pet_id).name}'s ` : ''}Assessment <ArrowRight size={15} />
            </button>
          </div>
        </div>
      )}

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
              Your Pets
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Select a pet to launch an assessment or view profile history
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
                        {pet.name} — {pet.species}
                      </h3>
                      <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                        {pet.breed || 'Mixed Breed'}
                      </span>
                    </div>
                  </div>
                  <span className="badge badge-neutral">
                    {pet.spayed_neutered ? 'Spayed/Neutered' : (pet.sex || 'Unknown')}
                  </span>
                </div>

                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '18px', display: 'flex', gap: '16px' }}>
                  <span>Weight: <strong>{pet.weight ? `${pet.weight} ${pet.weight_unit || 'kg'}` : 'Unrecorded'}</strong></span>
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
                          onClick={() => {
                            if (isCompleted) {
                              navigate(a.report_id ? `/reports/${a.report_id}` : `/reports`);
                            } else {
                              navigate(`/assessments/new?resumeId=${a.id}&petId=${a.pet_id}`);
                            }
                          }}
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

      {/* Dedicated Premium AI Chatbot Studio Showcase */}
      <section style={{ marginTop: '40px' }}>
        <div style={{
          background: 'linear-gradient(135deg, #042f2e 0%, #115e59 45%, #0f766e 100%)',
          borderRadius: 'var(--radius-xl)',
          padding: '36px 32px',
          color: '#ffffff',
          boxShadow: '0 16px 36px -10px rgba(13, 148, 136, 0.35)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '28px',
          position: 'relative',
          overflow: 'hidden'
        }}>
          {/* Ambient background glow */}
          <div style={{
            position: 'absolute',
            top: '-60px',
            right: '-40px',
            width: '240px',
            height: '240px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(45, 212, 191, 0.25) 0%, transparent 70%)',
            pointerEvents: 'none'
          }} />

          <div style={{ maxWidth: '640px', zIndex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: '4px 10px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: 'rgba(255, 255, 255, 0.15)',
                backdropFilter: 'blur(8px)',
                fontSize: '11px',
                fontWeight: '800',
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                color: '#99f6e4'
              }}>
                <Sparkles size={13} color="#5eead4" /> Premium AI Chatbot Space
              </span>
              <span style={{
                fontSize: '11px',
                fontWeight: '700',
                backgroundColor: '#ccfbf1',
                color: '#0f766e',
                padding: '2px 8px',
                borderRadius: '8px'
              }}>
                PRO ACTIVE
              </span>
            </div>

            <h2 style={{ fontSize: '24px', fontWeight: '800', margin: '0 0 10px 0', letterSpacing: '-0.02em', color: '#ffffff' }}>
              VetVision AI Assistant &bull; Dedicated Chatroom
            </h2>

            <p style={{ fontSize: '14px', lineHeight: 1.6, color: '#ccfbf1', margin: '0 0 16px 0' }}>
              Switch patients on-the-fly, consult our fine-tuned veterinary reasoning model without asterisks, and review strict AAHA/ASPCA clinical safety alerts in a distraction-free environment.
            </p>

            {/* Quick Prompt Starters that jump right in */}
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {[
                'My dog ate chocolate or grapes',
                'Cat wheezing or persistent cough',
                'What normal puppy fever looks like',
                'Safe at-home hydration tricks'
              ].map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => navigate(`/assistant?q=${encodeURIComponent(prompt)}`)}
                  style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.12)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    color: '#ffffff',
                    padding: '6px 12px',
                    borderRadius: 'var(--radius-full)',
                    fontSize: '12px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.22)';
                    e.currentTarget.style.transform = 'translateY(-1px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.12)';
                    e.currentTarget.style.transform = 'translateY(0)';
                  }}
                >
                  <MessageSquare size={12} color="#5eead4" />
                  <span>{prompt}</span>
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', zIndex: 1, minWidth: '220px' }}>
            <Link
              to="/assistant"
              className="btn btn-lg"
              style={{
                backgroundColor: '#ffffff',
                color: '#0f766e',
                fontWeight: '800',
                boxShadow: '0 4px 14px rgba(0, 0, 0, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '14px 24px',
                borderRadius: 'var(--radius-lg)'
              }}
            >
              <Bot size={20} color="#0d9488" />
              <span>Launch AI Assistant</span>
              <ArrowRight size={18} />
            </Link>

            <span style={{ fontSize: '11px', textAlign: 'center', color: '#99f6e4', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
              ✓ Guardrails verified &bull; Plain text output
            </span>
          </div>
        </div>
      </section>

      {/* Emergency Clinical Advice & Safety Guidance */}
      <section style={{ marginTop: '40px' }}>
        <div
          style={{
            backgroundColor: '#fff1f2',
            border: '1px solid #fecdd3',
            borderRadius: 'var(--radius-xl)',
            padding: '24px 28px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '18px',
          }}
        >
          <div
            style={{
              width: '44px',
              height: '44px',
              borderRadius: '12px',
              backgroundColor: '#ffe4e6',
              color: '#e11d48',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <ShieldAlert size={24} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#9f1239', margin: 0 }}>
                Clinical Safety & Red-Flag Triage Notice
              </h3>
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  backgroundColor: '#e11d48',
                  color: 'white',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-full)',
                  textTransform: 'uppercase',
                }}
              >
                Immediate ER Care
              </span>
            </div>
            <p style={{ fontSize: '13px', color: '#881337', lineHeight: 1.5, margin: '0 0 12px' }}>
              VetVision AI assists in early symptom tracking and veterinary communication. If your pet exhibits any of the following critical indicators, <strong>do not wait for questionnaire results</strong> — transport them to an emergency veterinary clinic immediately:
            </p>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '8px',
                fontSize: '12px',
                color: '#4c0519',
              }}
            >
              <div>🚨 <strong>Severe respiratory distress</strong> or choking</div>
              <div>🚨 <strong>Pale, blue, or white gums</strong></div>
              <div>🚨 <strong>Loss of consciousness</strong> or acute collapse</div>
              <div>🚨 <strong>Continuous seizures</strong> lasting &gt;3 minutes</div>
              <div>🚨 <strong>Uncontrolled hemorrhage</strong> or major trauma</div>
              <div>🚨 <strong>Suspected lethal toxin ingestion</strong> (chocolate, lilies, xylitol)</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default DashboardPage;
