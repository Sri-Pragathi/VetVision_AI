import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Send,
  HelpCircle,
  AlertTriangle,
  AlertOctagon,
  ShieldCheck,
  Clock,
  PhoneCall,
  ExternalLink,
  RefreshCw,
  Info,
  CheckCircle2,
  Trash2,
  Copy,
  Check,
  Plus,
  ArrowRight,
  Heart,
  Activity,
  User,
  Shield,
  Bot
} from 'lucide-react';
import { guidanceApi } from '../api/guidanceApi';
import { petApi } from '../api/petApi';
import { assessmentApi } from '../api/assessmentApi';

export default function AiAssistantPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const urlPetId = searchParams.get('petId') || null;
  const urlAssessmentId = searchParams.get('assessmentId') || null;
  const initialQuery = searchParams.get('q') || '';

  const [pets, setPets] = useState([]);
  const [selectedPetId, setSelectedPetId] = useState(urlPetId || 'all');
  const [selectedAssessmentId, setSelectedAssessmentId] = useState(urlAssessmentId);
  const [assessmentDetails, setAssessmentDetails] = useState(null);

  const [question, setQuestion] = useState(initialQuery);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversation, setConversation] = useState([]);
  const [quickQuestions, setQuickQuestions] = useState([]);
  const [copiedIndex, setCopiedIndex] = useState(null);

  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  // Load pets and quick questions on mount
  useEffect(() => {
    loadUserPets();
    loadQuickQuestions();
  }, []);

  // If assessmentId is present in URL, load its summary context
  useEffect(() => {
    if (selectedAssessmentId) {
      assessmentApi.getAssessment(selectedAssessmentId)
        .then((res) => {
          const ass = res?.data || res;
          setAssessmentDetails(ass);
          if (ass?.pet_id && selectedPetId === 'all') {
            setSelectedPetId(ass.pet_id);
          }
        })
        .catch(() => {});
    }
  }, [selectedAssessmentId]);

  // If an initial query was passed in URL params, auto-ask it
  useEffect(() => {
    if (initialQuery && initialQuery.trim() && conversation.length === 0) {
      handleAsk(initialQuery.trim());
    }
  }, [initialQuery]);

  const loadUserPets = async () => {
    try {
      const res = await petApi.getPets();
      const list = Array.isArray(res) ? res : (res?.data || []);
      setPets(list);
    } catch {
      setPets([]);
    }
  };

  const loadQuickQuestions = async () => {
    try {
      const res = await guidanceApi.getQuickQuestions();
      const qList = res?.data?.questions || res?.questions;
      if (Array.isArray(qList) && qList.length > 0) {
        setQuickQuestions(qList);
      }
    } catch {
      setQuickQuestions([
        { id: '1', category: 'After-Hours', question: 'It is midnight and my regular clinic is closed. What should I do first?' },
        { id: '2', category: 'Medications', question: 'Can I give my pet human pain relief or fever medicine like paracetamol or ibuprofen?' },
        { id: '3', category: 'Emergencies', question: 'What warning signs mean I should go to the emergency clinic immediately without waiting?' },
        { id: '4', category: 'Lethargy & Food', question: 'My pet is unusually lethargic and refuses food. What should I check at home?' },
        { id: '5', category: 'Respiratory', question: 'My pet is coughing or breathing faster than usual. How can I evaluate this safely?' },
        { id: '6', category: 'Digestive', question: 'My pet vomited once. What should I watch for over the next 2 hours?' },
      ]);
    }
  };

  const selectedPet = pets.find((p) => p.id === selectedPetId);

  const handleAsk = async (queryText) => {
    const textToSend = queryText || question;
    if (!textToSend || !textToSend.trim() || loading) return;

    setError(null);
    setLoading(true);

    const userMessage = {
      role: 'user',
      text: textToSend.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      petContextName: selectedPet?.name || 'General Care',
    };

    setConversation((prev) => [...prev, userMessage]);
    setQuestion('');

    try {
      const res = await guidanceApi.ask({
        question: textToSend.trim(),
        petId: selectedPetId !== 'all' ? selectedPetId : undefined,
        assessmentId: selectedAssessmentId || undefined,
      });

      const payload = (res?.data && res.data.answer !== undefined)
        ? res.data
        : (res?.answer !== undefined ? res : (res?.data || {}));

      const assistantReply = {
        role: 'assistant',
        data: payload,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        petContextName: selectedPet?.name || 'General Care',
      };

      setConversation((prev) => [...prev, assistantReply]);
      setTimeout(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      const errMsg =
        err?.message ||
        err?.details?.message ||
        err?.response?.data?.message ||
        'Failed to retrieve AI guidance. Please try again.';
      setError(errMsg);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleStartNewConsultation = () => {
    setConversation([]);
    setError(null);
    setQuestion('');
    inputRef.current?.focus();
  };

  const handleCopyMessage = (text, idx) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const getUrgencyBadge = (urgency) => {
    const u = (urgency || 'HOME_MONITORING').toUpperCase();
    if (u === 'EMERGENCY') {
      return { bg: '#fee2e2', text: '#b91c1c', border: '#fca5a5', label: 'EMERGENCY WARNING' };
    }
    if (u === 'URGENT') {
      return { bg: '#ffedd5', text: '#c2410c', border: '#fdba74', label: 'URGENT EVALUATION' };
    }
    if (u === 'APPOINTMENT') {
      return { bg: '#e0f2fe', text: '#0369a1', border: '#7dd3fc', label: 'APPOINTMENT RECOMMENDED' };
    }
    if (u === 'GENERAL_INFO' || u === 'INFO') {
      return { bg: '#f1f5f9', text: '#475569', border: '#cbd5e1', label: 'PET CARE SCOPE' };
    }
    return { bg: '#ecfdf5', text: '#047857', border: '#6ee7b7', label: 'HOME MONITORING' };
  };

  return (
    <div style={{
      display: 'flex',
      height: 'calc(100vh - var(--nav-height))',
      width: '100%',
      backgroundColor: '#f8fafc',
      overflow: 'hidden',
    }}>
      {/* ========================================================
          LEFT SIDEBAR: Patient Context, Prompts, Emergency Hotlines
          ======================================================== */}
      <aside style={{
        width: '340px',
        minWidth: '300px',
        maxWidth: '380px',
        height: '100%',
        backgroundColor: '#ffffff',
        borderRight: '1px solid var(--border-light)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        overflow: 'hidden',
        zIndex: 10,
        boxShadow: '1px 0 8px rgba(0, 0, 0, 0.02)',
      }}>
        {/* Sidebar Header: Brand & New Consultation Action */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-light)',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '30px',
                height: '30px',
                borderRadius: '8px',
                backgroundColor: 'rgba(13, 148, 136, 0.1)',
                color: 'var(--primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <Sparkles size={16} />
              </div>
              <span style={{ fontSize: '14px', fontWeight: 800, color: 'var(--text-main)' }}>
                VetVision AI
              </span>
            </div>
            <span style={{
              fontSize: '10px',
              fontWeight: 800,
              backgroundColor: '#ccfbf1',
              color: '#0f766e',
              padding: '2px 8px',
              borderRadius: '10px',
              letterSpacing: '0.04em',
            }}>
              PRO
            </span>
          </div>

          <button
            onClick={handleStartNewConsultation}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '10px 16px',
              backgroundColor: 'var(--primary)',
              color: '#ffffff',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              fontSize: '13px',
              fontWeight: 700,
              cursor: 'pointer',
              transition: 'background-color 0.15s ease',
              boxShadow: '0 2px 6px rgba(13, 148, 136, 0.25)',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--primary-hover)')}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'var(--primary)')}
          >
            <Plus size={16} />
            <span>New Consultation</span>
          </button>
        </div>

        {/* Scrollable Middle: Patient Context & Quick Prompts */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px 20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
        }}>
          {/* Patient Context Card */}
          <div style={{
            backgroundColor: '#f8fafc',
            border: '1px solid var(--border-light)',
            borderRadius: '12px',
            padding: '14px',
          }}>
            <div style={{
              fontSize: '11px',
              fontWeight: 800,
              textTransform: 'uppercase',
              color: 'var(--text-muted)',
              letterSpacing: '0.05em',
              marginBottom: '10px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}>
              <Heart size={13} color="var(--primary)" />
              <span>Patient Context</span>
            </div>

            <select
              value={selectedPetId}
              onChange={(e) => setSelectedPetId(e.target.value)}
              style={{
                width: '100%',
                borderRadius: '8px',
                padding: '8px 10px',
                fontSize: '12px',
                fontWeight: 600,
                border: '1px solid #cbd5e1',
                backgroundColor: '#ffffff',
                color: 'var(--text-main)',
                outline: 'none',
                cursor: 'pointer',
                marginBottom: '10px',
              }}
            >
              <option value="all">🐾 General Pet Consultation</option>
              {pets.map((p) => (
                <option key={p.id} value={p.id}>
                  🐾 {p.name} ({p.species} • {p.breed || 'Mixed'})
                </option>
              ))}
            </select>

            {selectedPet ? (
              <div style={{
                backgroundColor: '#ffffff',
                border: '1px solid #ccfbf1',
                borderRadius: '8px',
                padding: '10px',
                fontSize: '11px',
                color: '#0f766e',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
              }}>
                <div style={{ fontWeight: 800, fontSize: '12px', color: '#115e59' }}>
                  ✓ Context Grounded: {selectedPet.name}
                </div>
                <div>• Species: <strong>{selectedPet.species}</strong> ({selectedPet.breed || 'Mixed'})</div>
                <div>• Age: <strong>{selectedPet.age ? `${selectedPet.age} yrs` : 'Unrecorded'}</strong></div>
                <div>• Weight: <strong>{selectedPet.weight ? `${selectedPet.weight} ${selectedPet.weight_unit || 'kg'}` : 'Unrecorded'}</strong></div>
                {selectedPet.allergies && (
                  <div style={{ color: '#b91c1c', fontWeight: 600 }}>
                    ⚠️ Allergies: {selectedPet.allergies}
                  </div>
                )}
              </div>
            ) : (
              <div style={{ fontSize: '11px', color: '#64748b', lineHeight: 1.4 }}>
                Select a registered pet to ground all recommendations in their exact species, weight, and health history.
              </div>
            )}

            {/* Assessment linkage indicator if present */}
            {assessmentDetails && (
              <div style={{
                marginTop: '10px',
                paddingTop: '8px',
                borderTop: '1px solid #e2e8f0',
                fontSize: '11px',
                color: '#475569',
              }}>
                <div style={{ fontWeight: 700, color: '#0f172a' }}>
                  🔗 Linked Assessment #{assessmentDetails.id?.substring(0, 8)}
                </div>
                {assessmentDetails.risk_analysis && (
                  <div style={{ color: 'var(--primary)', fontWeight: 700, marginTop: '2px' }}>
                    Assessed: {assessmentDetails.risk_analysis.risk_level} Risk
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Quick Prompt Topics */}
          <div>
            <div style={{
              fontSize: '11px',
              fontWeight: 800,
              textTransform: 'uppercase',
              color: 'var(--text-muted)',
              letterSpacing: '0.05em',
              marginBottom: '10px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}>
              <HelpCircle size={13} color="var(--primary)" />
              <span>Quick Prompts</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {quickQuestions.map((q) => (
                <button
                  key={q.id || q.question}
                  onClick={() => handleAsk(q.question)}
                  disabled={loading}
                  style={{
                    textAlign: 'left',
                    fontSize: '12px',
                    padding: '10px 12px',
                    borderRadius: '10px',
                    backgroundColor: '#ffffff',
                    border: '1px solid #e2e8f0',
                    color: '#334155',
                    lineHeight: 1.4,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.02)',
                    whiteSpace: 'normal',
                    wordBreak: 'break-word',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'var(--primary)';
                    e.currentTarget.style.backgroundColor = '#f0fdfa';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = '#e2e8f0';
                    e.currentTarget.style.backgroundColor = '#ffffff';
                  }}
                >
                  {q.category && (
                    <span style={{
                      fontSize: '10px',
                      fontWeight: 800,
                      color: 'var(--primary)',
                      textTransform: 'uppercase',
                      marginBottom: '3px',
                      letterSpacing: '0.03em',
                    }}>
                      {q.category}
                    </span>
                  )}
                  <span style={{ fontWeight: 500 }}>{q.question}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Pinned Bottom: 24/7 Clinical Emergency Hotlines */}
        <div style={{
          padding: '14px 18px',
          borderTop: '1px solid #fecdd3',
          backgroundColor: '#fff1f2',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            color: '#be123c',
            fontWeight: 800,
            fontSize: '12px',
          }}>
            <PhoneCall size={14} />
            <span>24/7 Poison & Emergency</span>
          </div>

          <div style={{ fontSize: '11px', color: '#9f1239', lineHeight: 1.4 }}>
            <div>• ASPCA Poison Control: <strong>(888) 426-4435</strong></div>
            <div>• Pet Poison Helpline: <strong>(855) 764-7661</strong></div>
          </div>

          <a
            href="https://www.aaha.org/your-pet/find-a-hospital/"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              marginTop: '4px',
              backgroundColor: '#be123c',
              color: '#ffffff',
              fontSize: '11px',
              fontWeight: 700,
              padding: '6px 10px',
              borderRadius: '6px',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              textDecoration: 'none',
            }}
          >
            <span>AAHA 24/7 Hospital Finder</span>
            <ExternalLink size={12} />
          </a>
        </div>
      </aside>

      {/* ========================================================
          RIGHT MAIN WORKSPACE: Chat Stream & Pinned Input Bar
          ======================================================== */}
      <main style={{
        flex: 1,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        backgroundColor: '#f8fafc',
        position: 'relative',
      }}>
        {/* Chat Stream Header */}
        <header style={{
          height: '60px',
          backgroundColor: '#ffffff',
          borderBottom: '1px solid var(--border-light)',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: 'var(--radius-full)',
              backgroundColor: '#ecfdf5',
              border: '1px solid #a7f3d0',
              fontSize: '12px',
              fontWeight: 700,
              color: '#065f46',
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: '#10b981',
                boxShadow: '0 0 0 2px rgba(16, 185, 129, 0.25)',
              }} />
              <span>Live Clinical Stream</span>
            </div>

            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-muted)' }}>
              {selectedPet ? (
                <span>Patient: <strong style={{ color: 'var(--text-main)' }}>{selectedPet.name}</strong> ({selectedPet.species})</span>
              ) : (
                <span>General Pet Guidance</span>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--primary-hover)',
              backgroundColor: 'var(--primary-light)',
              padding: '4px 10px',
              borderRadius: '12px',
              border: '1px solid var(--primary-border)',
            }}>
              <ShieldCheck size={14} color="var(--primary)" />
              <span>Clinical Safety Guardrails Active</span>
            </div>

            {conversation.length > 0 && (
              <button
                onClick={handleStartNewConsultation}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  backgroundColor: 'transparent',
                  border: '1px solid #cbd5e1',
                  color: 'var(--text-muted)',
                  fontSize: '12px',
                  fontWeight: 600,
                  padding: '5px 10px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                }}
                title="Clear Consultation"
              >
                <Trash2 size={13} />
                <span>Clear</span>
              </button>
            )}
          </div>
        </header>

        {/* Scrollable Chat Messages Feed */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '28px 32px',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px',
        }}>
          {conversation.length === 0 ? (
            /* Empty State Hero Card */
            <div style={{
              margin: 'auto auto',
              maxWidth: '680px',
              width: '100%',
              textAlign: 'center',
              padding: '36px 24px',
            }}>
              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '20px',
                background: 'linear-gradient(135deg, rgba(13, 148, 136, 0.15) 0%, rgba(99, 102, 241, 0.15) 100%)',
                color: 'var(--primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 16px',
                boxShadow: '0 8px 20px rgba(13, 148, 136, 0.15)',
              }}>
                <Sparkles size={32} />
              </div>

              <h2 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text-main)', margin: '0 0 8px 0', letterSpacing: '-0.02em' }}>
                Welcome to VetVision AI Pro
              </h2>
              <p style={{ fontSize: '14px', color: 'var(--text-muted)', lineHeight: 1.6, margin: '0 0 28px 0' }}>
                Your dedicated 24/7 veterinary triage workspace. Ask about sudden symptoms, medications, home observation steps, or emergency clinic thresholds.
              </p>

              {/* 2x2 Starter Question Grid */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '12px',
                textAlign: 'left',
              }}>
                {[
                  {
                    tag: 'NIGHT CARE',
                    tagColor: '#0284c7',
                    title: 'What to do when my clinic is closed at night?',
                    prompt: 'It is midnight and my regular clinic is closed. What should I do first?',
                  },
                  {
                    tag: 'MED SAFETY',
                    tagColor: '#dc2626',
                    title: 'Can I give human paracetamol or ibuprofen?',
                    prompt: 'Can I give my pet human pain relief or fever medicine like paracetamol or ibuprofen?',
                  },
                  {
                    tag: 'ER TRIAGE',
                    tagColor: '#ea580c',
                    title: 'Red-flag warning signs that cannot wait',
                    prompt: 'What warning signs mean I should go to the emergency clinic immediately without waiting?',
                  },
                  {
                    tag: 'MONITORING',
                    tagColor: '#16a34a',
                    title: 'Single vomit episode & bland diet guide',
                    prompt: 'My pet vomited once. What should I watch for over the next 2 hours?',
                  },
                ].map((item, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleAsk(item.prompt)}
                    style={{
                      padding: '16px 18px',
                      backgroundColor: '#ffffff',
                      border: '1px solid #e2e8f0',
                      borderRadius: '14px',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.02)',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'var(--primary)';
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.boxShadow = '0 6px 16px rgba(13, 148, 136, 0.1)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = '#e2e8f0';
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.02)';
                    }}
                  >
                    <div style={{
                      fontSize: '11px',
                      fontWeight: 800,
                      color: item.tagColor,
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                      marginBottom: '4px',
                    }}>
                      {item.tag}
                    </div>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', lineHeight: 1.4 }}>
                      {item.title}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            /* Active Message List */
            conversation.map((msg, idx) => {
              if (msg.role === 'user') {
                return (
                  <div
                    key={idx}
                    style={{
                      alignSelf: 'flex-end',
                      maxWidth: '75%',
                      backgroundColor: 'var(--primary)',
                      color: '#ffffff',
                      padding: '14px 20px',
                      borderRadius: '18px 18px 4px 18px',
                      fontSize: '14px',
                      boxShadow: '0 4px 14px rgba(13, 148, 136, 0.25)',
                    }}
                  >
                    <div style={{ fontWeight: 500, lineHeight: 1.5 }}>{msg.text}</div>
                    <div style={{ fontSize: '11px', color: '#ccfbf1', textAlign: 'right', marginTop: '6px' }}>
                      {msg.petContextName && <span>[{msg.petContextName}] &bull; </span>}
                      {msg.timestamp}
                    </div>
                  </div>
                );
              }

              const data = msg.data || {};
              const badge = getUrgencyBadge(data.urgency_level);
              const cleanAnswer = String(data.answer || '').replace(/\*+/g, '');

              return (
                <div
                  key={idx}
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '85%',
                    backgroundColor: '#ffffff',
                    border: '1px solid #e2e8f0',
                    padding: '22px 26px',
                    borderRadius: '18px 18px 18px 4px',
                    fontSize: '14px',
                    boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
                  }}
                >
                  {/* Status header */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '8px',
                    marginBottom: '14px',
                    paddingBottom: '12px',
                    borderBottom: '1px solid #f1f5f9',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span style={{
                        fontSize: '11px',
                        fontWeight: 800,
                        backgroundColor: badge.bg,
                        color: badge.text,
                        border: `1px solid ${badge.border}`,
                        padding: '3px 10px',
                        borderRadius: '20px',
                        letterSpacing: '0.03em',
                      }}>
                        {badge.label}
                      </span>

                      {data.ai_engine && (
                        <span style={{
                          fontSize: '10px',
                          fontWeight: 700,
                          backgroundColor: '#f0fdf4',
                          color: '#166534',
                          border: '1px solid #bbf7d0',
                          padding: '2px 8px',
                          borderRadius: '12px',
                        }}>
                          ⚡ {data.ai_engine}
                        </span>
                      )}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <button
                        onClick={() => handleCopyMessage(cleanAnswer, idx)}
                        style={{
                          padding: '3px 9px',
                          fontSize: '11px',
                          color: '#64748b',
                          border: '1px solid #cbd5e1',
                          borderRadius: '6px',
                          backgroundColor: '#ffffff',
                          cursor: 'pointer',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                        }}
                      >
                        {copiedIndex === idx ? <Check size={12} color="#16a34a" /> : <Copy size={12} />}
                        {copiedIndex === idx ? 'Copied' : 'Copy'}
                      </button>
                      <span style={{ fontSize: '11px', color: '#94a3b8' }}>{msg.timestamp}</span>
                    </div>
                  </div>

                  {/* Main Plain-Text Body */}
                  <div style={{
                    whiteSpace: 'pre-line',
                    color: '#1e293b',
                    lineHeight: 1.65,
                    fontSize: '14px',
                    marginBottom: '14px',
                  }}>
                    {cleanAnswer}
                  </div>

                  {/* Key Safety Takeaways Box */}
                  {data.key_takeaways && data.key_takeaways.length > 0 && (
                    <div style={{
                      backgroundColor: '#f0fdf4',
                      borderLeft: '4px solid #16a34a',
                      padding: '12px 16px',
                      borderRadius: '8px',
                      marginBottom: '12px',
                      fontSize: '13px',
                    }}>
                      <div style={{ fontWeight: 800, color: '#166534', marginBottom: '6px' }}>
                        💡 Key Safety Takeaways:
                      </div>
                      <ul style={{ margin: 0, paddingLeft: '18px', color: '#15803d', lineHeight: 1.5 }}>
                        {data.key_takeaways.map((k, kIdx) => (
                          <li key={kIdx}>{String(k || '').replace(/\*+/g, '')}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Contraindications Warning Box */}
                  {data.contraindications && data.contraindications.length > 0 && (
                    <div style={{
                      backgroundColor: '#fef2f2',
                      borderLeft: '4px solid #dc2626',
                      padding: '12px 16px',
                      borderRadius: '8px',
                      marginBottom: '12px',
                      fontSize: '13px',
                    }}>
                      <div style={{ fontWeight: 800, color: '#991b1b', marginBottom: '6px' }}>
                        🚫 What NOT to Do:
                      </div>
                      <ul style={{ margin: 0, paddingLeft: '18px', color: '#7f1d1d', lineHeight: 1.5 }}>
                        {data.contraindications.map((c, cIdx) => (
                          <li key={cIdx}>{String(c || '').replace(/\*+/g, '')}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Disclaimer footer */}
                  <div style={{ fontSize: '11px', color: '#94a3b8', fontStyle: 'italic', marginTop: '10px' }}>
                    * {data.disclaimer || 'VetVision AI provides educational triage guidance and does not replace in-person veterinary care.'}
                  </div>
                </div>
              );
            })
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Error Alert if request failed */}
        {error && (
          <div style={{
            margin: '0 32px 12px',
            padding: '12px 18px',
            backgroundColor: '#fef2f2',
            border: '1px solid #fca5a5',
            borderRadius: '10px',
            color: '#991b1b',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}>
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* ========================================================
            PINNED BOTTOM INPUT BAR
            ======================================================== */}
        <div style={{
          padding: '16px 32px 20px',
          backgroundColor: '#ffffff',
          borderTop: '1px solid var(--border-light)',
          boxShadow: '0 -4px 16px rgba(0, 0, 0, 0.02)',
          flexShrink: 0,
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            backgroundColor: '#f8fafc',
            border: '1px solid #cbd5e1',
            borderRadius: 'var(--radius-full)',
            padding: '4px 6px 4px 18px',
            boxShadow: 'inset 0 1px 3px rgba(0, 0, 0, 0.03)',
            transition: 'border-color 0.15s ease',
          }}>
            <input
              ref={inputRef}
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleAsk();
                }
              }}
              placeholder={`Ask VetVision AI about symptoms, diet, or emergency triage${selectedPet ? ` for ${selectedPet.name}` : ''}...`}
              disabled={loading}
              style={{
                flex: 1,
                border: 'none',
                backgroundColor: 'transparent',
                outline: 'none',
                fontSize: '14px',
                color: 'var(--text-main)',
                padding: '8px 0',
              }}
            />

            <button
              onClick={() => handleAsk()}
              disabled={loading || !question.trim()}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '10px 20px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: question.trim() ? 'var(--primary)' : '#94a3b8',
                color: '#ffffff',
                border: 'none',
                fontSize: '13px',
                fontWeight: 700,
                cursor: question.trim() && !loading ? 'pointer' : 'default',
                transition: 'all 0.15s ease',
              }}
            >
              {loading ? <RefreshCw size={16} className="spin" /> : <Send size={16} />}
              <span>Ask AI</span>
            </button>
          </div>

          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: '8px',
            fontSize: '11px',
            color: '#94a3b8',
            padding: '0 6px',
          }}>
            <span>⚡ Groq clinical reasoning &bull; AAHA / ASPCA guardrails active &bull; Plain text output</span>
            <span>Press Enter to send</span>
          </div>
        </div>
      </main>
    </div>
  );
}
