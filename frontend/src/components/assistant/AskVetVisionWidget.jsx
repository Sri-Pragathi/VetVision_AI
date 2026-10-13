import React, { useState, useEffect, useRef } from 'react';
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
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Info,
  CheckCircle2,
  XCircle,
  MessageSquare,
} from 'lucide-react';
import { guidanceApi } from '../../api/guidanceApi';

export default function AskVetVisionWidget({
  petId = null,
  petName = null,
  assessmentId = null,
  compact = false,
}) {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversation, setConversation] = useState([]);
  const [quickQuestions, setQuickQuestions] = useState([]);
  const [expandedHotlines, setExpandedHotlines] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    loadQuickQuestions();
  }, []);

  const loadQuickQuestions = async () => {
    try {
      const res = await guidanceApi.getQuickQuestions();
      const qList = res?.data?.questions || res?.questions;
      if (Array.isArray(qList) && qList.length > 0) {
        setQuickQuestions(qList);
      }
    } catch {
      // Fallback local quick questions
      setQuickQuestions([
        { id: '1', question: 'It is midnight and my regular clinic is closed. What should I do first?' },
        { id: '2', question: 'Can I give my pet human pain relief or fever medicine like paracetamol or ibuprofen?' },
        { id: '3', question: 'What warning signs mean I should go to the emergency clinic immediately without waiting?' },
        { id: '4', question: 'My pet is unusually lethargic and refuses food. What should I check at home?' },
        { id: '5', question: 'My pet is coughing or breathing faster than usual. How can I evaluate this safely?' },
        { id: '6', question: 'My pet vomited once. What should I watch for over the next 2 hours?' },
      ]);
    }
  };

  const handleAsk = async (queryText) => {
    const textToSend = queryText || question;
    if (!textToSend || !textToSend.trim() || loading) return;

    setError(null);
    setLoading(true);

    const userMessage = {
      role: 'user',
      text: textToSend.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setConversation((prev) => [...prev, userMessage]);
    setQuestion('');

    try {
      const res = await guidanceApi.ask({
        question: textToSend.trim(),
        petId: petId || undefined,
        assessmentId: assessmentId || undefined,
      });

      // Defensively extract guidance payload from either { status, data: { answer } } or { answer }
      const payload = (res?.data && res.data.answer !== undefined)
        ? res.data
        : (res?.answer !== undefined ? res : (res?.data || {}));

      const assistantReply = {
        role: 'assistant',
        data: payload,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
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
    }
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
    <div
      style={{
        borderRadius: '16px',
        backgroundColor: '#ffffff',
        border: '1px solid #e2e8f0',
        boxShadow: '0 4px 20px -2px rgba(0, 0, 0, 0.05)',
        overflow: 'hidden',
        marginBottom: compact ? '1.5rem' : '2.5rem',
      }}
    >
      {/* Header */}
      <div
        style={{
          background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
          color: '#ffffff',
          padding: '1.25rem 1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.75rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Sparkles size={22} color="#ffffff" />
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: '#ffffff' }}>
              Ask VetVision AI
            </h3>
            <p style={{ margin: '0.15rem 0 0', fontSize: '0.8rem', color: '#e0f2fe' }}>
              Instant supportive care, first-aid precautions & after-hours guidance{petName ? ` for ${petName}` : ''}.
            </p>
          </div>
        </div>

        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            padding: '0.25rem 0.65rem',
            borderRadius: '20px',
            color: '#ffffff',
          }}
        >
          24/7 Safety Assistant
        </span>
      </div>

      <div style={{ padding: '1.25rem 1.5rem' }}>
        {/* Quick Suggestion Chips */}
        <div style={{ marginBottom: '1.25rem' }}>
          <div
            style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              color: '#64748b',
              marginBottom: '0.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
            }}
          >
            <HelpCircle size={14} /> Quick Inquiries & Triage Scenarios
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.45rem' }}>
            {quickQuestions.map((q) => (
              <button
                key={q.id || q.question}
                onClick={() => handleAsk(q.question)}
                disabled={loading}
                className="btn btn-outline btn-sm"
                style={{
                  fontSize: '0.775rem',
                  padding: '0.35rem 0.75rem',
                  borderRadius: '20px',
                  borderColor: '#cbd5e1',
                  color: '#334155',
                  backgroundColor: '#f8fafc',
                  textAlign: 'left',
                }}
              >
                {q.question}
              </button>
            ))}
          </div>
        </div>

        {/* Conversation Stream */}
        {conversation.length > 0 && (
          <div
            style={{
              maxHeight: '420px',
              overflowY: 'auto',
              padding: '0.75rem 0',
              marginBottom: '1rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}
          >
            {conversation.map((msg, idx) => {
              if (msg.role === 'user') {
                return (
                  <div
                    key={idx}
                    style={{
                      alignSelf: 'flex-end',
                      maxWidth: '85%',
                      backgroundColor: '#0284c7',
                      color: '#ffffff',
                      padding: '0.75rem 1rem',
                      borderRadius: '14px 14px 2px 14px',
                      fontSize: '0.875rem',
                      boxShadow: '0 2px 6px rgba(2, 132, 199, 0.2)',
                    }}
                  >
                    <div style={{ fontWeight: 600 }}>{msg.text}</div>
                    <div style={{ fontSize: '0.675rem', color: '#bae6fd', textAlign: 'right', marginTop: '0.25rem' }}>
                      {msg.timestamp}
                    </div>
                  </div>
                );
              }

              const data = msg.data || {};
              const badge = getUrgencyBadge(data.urgency_level);

              return (
                <div
                  key={idx}
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '92%',
                    backgroundColor: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    padding: '1.15rem',
                    borderRadius: '14px 14px 14px 2px',
                    fontSize: '0.875rem',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                  }}
                >
                  {/* Status header */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.65rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                      <span
                        style={{
                          fontSize: '0.7rem',
                          fontWeight: 800,
                          backgroundColor: badge.bg,
                          color: badge.text,
                          border: `1px solid ${badge.border}`,
                          padding: '0.2rem 0.55rem',
                          borderRadius: '12px',
                        }}
                      >
                        {badge.label}
                      </span>
                      {data.ai_engine && (
                        <span
                          style={{
                            fontSize: '0.65rem',
                            fontWeight: 700,
                            backgroundColor: '#e0f2fe',
                            color: '#0369a1',
                            padding: '0.15rem 0.45rem',
                            borderRadius: '10px',
                          }}
                        >
                          ⚡ {data.ai_engine}
                        </span>
                      )}
                    </div>
                    <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>{msg.timestamp}</span>
                  </div>

                  {/* Body text with preserved line breaks and clean plain formatting */}
                  <div
                    style={{
                      whiteSpace: 'pre-line',
                      color: '#1e293b',
                      lineHeight: 1.6,
                      fontSize: '0.875rem',
                      marginBottom: '0.85rem',
                    }}
                  >
                    {(data.answer || '').replace(/\*+/g, '')}
                  </div>

                  {/* Key Takeaways */}
                  {data.key_takeaways && data.key_takeaways.length > 0 && (
                    <div
                      style={{
                        backgroundColor: '#f0fdf4',
                        borderLeft: '3px solid #16a34a',
                        padding: '0.65rem 0.85rem',
                        borderRadius: '6px',
                        marginBottom: '0.75rem',
                        fontSize: '0.8rem',
                      }}
                    >
                      <div style={{ fontWeight: 700, color: '#166534', marginBottom: '0.25rem' }}>
                        Key Safety Takeaways:
                      </div>
                      <ul style={{ margin: 0, paddingLeft: '1.15rem', color: '#15803d' }}>
                        {data.key_takeaways.map((k, kIdx) => (
                          <li key={kIdx}>{String(k || '').replace(/\*+/g, '')}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Contraindications Warning Box */}
                  {data.contraindications && data.contraindications.length > 0 && (
                    <div
                      style={{
                        backgroundColor: '#fef2f2',
                        borderLeft: '3px solid #dc2626',
                        padding: '0.65rem 0.85rem',
                        borderRadius: '6px',
                        marginBottom: '0.75rem',
                        fontSize: '0.8rem',
                      }}
                    >
                      <div style={{ fontWeight: 700, color: '#991b1b', marginBottom: '0.25rem' }}>
                        🚫 What NOT to Do:
                      </div>
                      <ul style={{ margin: 0, paddingLeft: '1.15rem', color: '#7f1d1d' }}>
                        {data.contraindications.map((c, cIdx) => (
                          <li key={cIdx}>{String(c || '').replace(/\*+/g, '')}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Disclaimer note */}
                  <div style={{ fontSize: '0.7rem', color: '#64748b', fontStyle: 'italic', marginTop: '0.4rem' }}>
                    * {data.disclaimer}
                  </div>
                </div>
              );
            })}
            <div ref={chatEndRef} />
          </div>
        )}

        {/* Input Bar */}
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <input
            type="text"
            className="input-field"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleAsk();
              }
            }}
            placeholder={`Ask about first-aid, monitoring, or precautions${petName ? ` for ${petName}` : ''}...`}
            disabled={loading}
            style={{
              flex: 1,
              borderRadius: '24px',
              padding: '0.65rem 1.15rem',
              fontSize: '0.875rem',
              border: '1px solid #cbd5e1',
            }}
          />

          <button
            onClick={() => handleAsk()}
            disabled={loading || !question.trim()}
            className="btn btn-primary"
            style={{
              borderRadius: '24px',
              padding: '0.65rem 1.25rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
              fontSize: '0.875rem',
              fontWeight: 700,
            }}
          >
            {loading ? <RefreshCw size={16} className="spin" /> : <Send size={16} />}
            <span>Ask</span>
          </button>
        </div>

        {error && (
          <div style={{ color: '#dc2626', fontSize: '0.8rem', marginTop: '0.5rem' }}>
            ⚠️ {error}
          </div>
        )}

        {/* 24/7 Helpline Drawer Toggle */}
        <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
            🚨 Need immediate poisoning or hospital help?
          </span>
          <button
            onClick={() => setExpandedHotlines(!expandedHotlines)}
            className="btn btn-outline btn-sm"
            style={{
              fontSize: '0.725rem',
              padding: '0.2rem 0.55rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.3rem',
              color: '#1d4ed8',
              borderColor: '#bfdbfe',
            }}
          >
            <PhoneCall size={13} /> {expandedHotlines ? 'Hide Hotlines' : 'Emergency Hotlines'}
          </button>
        </div>

        {expandedHotlines && (
          <div
            style={{
              marginTop: '0.75rem',
              backgroundColor: '#eff6ff',
              border: '1px solid #bfdbfe',
              borderRadius: '8px',
              padding: '0.85rem 1rem',
              fontSize: '0.775rem',
              color: '#1e3a8a',
            }}
          >
            <div>• <strong>ASPCA Poison Control:</strong> (888) 426-4435 (24/7)</div>
            <div style={{ marginTop: '0.2rem' }}>• <strong>Pet Poison Helpline:</strong> (855) 764-7661 (24/7)</div>
            <div style={{ marginTop: '0.2rem' }}>
              • <strong>AAHA 24/7 Hospital Locator:</strong>{' '}
              <a href="https://www.aaha.org/your-pet/find-a-hospital/" target="_blank" rel="noopener noreferrer" style={{ color: '#2563eb', fontWeight: 600 }}>
                Find Hospital <ExternalLink size={12} style={{ display: 'inline' }} />
              </a>
            </div>
            <div style={{ marginTop: '0.35rem', color: '#1e40af', fontStyle: 'italic' }}>
              Tip: Call while in transit so emergency staff can prepare an intake stretcher before you arrive.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
