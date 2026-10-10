import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Activity, 
  ArrowRight, 
  ShieldCheck, 
  Sparkles, 
  Camera, 
  HelpCircle, 
  FileText, 
  Clock, 
  CheckCircle,
  AlertOctagon,
  HeartPulse,
  Layers,
  ChevronRight
} from 'lucide-react';

export const LandingPage = () => {
  const { isAuthenticated } = useAuth();

  const workflowSteps = [
    { title: 'Pet Profile', desc: 'Species, breed & baseline health factors', icon: HeartPulse },
    { title: 'Symptoms', desc: 'Structured clinical signs & duration tracking', icon: Activity },
    { title: 'Smart Questions', desc: 'Dynamic adaptive follow-up inquiry', icon: HelpCircle },
    { title: 'Image Analysis', desc: 'Computer vision visual observations', icon: Camera },
    { title: 'Risk Assessment', desc: 'Explainable heuristic scoring & emergency rules', icon: Sparkles },
    { title: 'Veterinary Report', desc: 'Immutable snapshot & clinical handoff brief', icon: FileText },
  ];

  const highlights = [
    {
      title: 'Early Warning Triage',
      desc: 'Computational health risk identification to catch progressive illness before severe complications arise.',
      icon: Clock,
      color: '#0d9488',
    },
    {
      title: 'Adaptive Questions',
      desc: 'Contextual follow-up engine that prioritizes condition-specific and life-safety questions dynamically.',
      icon: HelpCircle,
      color: '#0284c7',
    },
    {
      title: 'AI Risk Engine',
      desc: 'Transparent scoring evaluating symptoms, chronicity, vitals, and pet demographic vulnerabilities.',
      icon: Sparkles,
      color: '#8b5cf6',
    },
    {
      title: 'Computer Vision',
      desc: 'Quality-gated photographic analysis providing objective visual feature observations without disease overclaims.',
      icon: Camera,
      color: '#059669',
    },
    {
      title: 'Emergency Hard-Stop',
      desc: 'Acute life-safety guarantee ensuring critical respiratory, pain, or neurological signs are never downgraded.',
      icon: AlertOctagon,
      color: '#dc2626',
    },
    {
      title: 'Veterinary Handoff',
      desc: 'Instant, professional summary ready to copy or print for attending veterinarians during clinical consultation.',
      icon: FileText,
      color: '#d97706',
    },
  ];

  return (
    <div style={{ backgroundColor: 'var(--bg-app)' }}>
      {/* Hero Section */}
      <section style={{
        padding: '70px 0 60px',
        background: 'linear-gradient(180deg, #f0fdfa 0%, #f8fafc 100%)',
        borderBottom: '1px solid var(--border-light)',
      }}>
        <div className="container" style={{ textAlign: 'center', maxWidth: '880px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: '#ffffff',
            border: '1px solid var(--primary-border)',
            padding: '6px 14px',
            borderRadius: 'var(--radius-full)',
            fontSize: '13px',
            fontWeight: '600',
            color: 'var(--primary)',
            boxShadow: 'var(--shadow-xs)',
            marginBottom: '24px',
          }}>
            <Sparkles size={16} />
            <span>AI-Assisted Clinical Triage & Early Warning Platform</span>
          </div>

          <h1 style={{
            fontSize: '48px',
            fontWeight: '800',
            letterSpacing: '-0.03em',
            lineHeight: 1.15,
            color: 'var(--text-main)',
            marginBottom: '20px',
          }}>
            Smarter Pet Health <br />
            <span style={{ color: 'var(--primary)' }}>Starts Earlier.</span>
          </h1>

          <p style={{
            fontSize: '18px',
            color: 'var(--text-muted)',
            lineHeight: 1.6,
            marginBottom: '36px',
            maxWidth: '720px',
            margin: '0 auto 36px',
          }}>
            VetVision AI helps pet owners organize symptoms, answer adaptive clinical follow-up questions, 
            capture photograph observations through computer vision, and understand risk levels with explainable triage summaries.
          </p>

          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '14px',
            flexWrap: 'wrap',
          }}>
            <Link to={isAuthenticated ? "/assessments/new" : "/register"} className="btn btn-primary btn-lg">
              Start Health Assessment
              <ArrowRight size={18} />
            </Link>
            <a href="#workflow" className="btn btn-secondary btn-lg">
              Explore VetVision AI
            </a>
          </div>

          <p style={{ fontSize: '13px', color: 'var(--text-subtle)', marginTop: '16px' }}>
            Empowers clinical consultations • Non-diagnostic triage support • Free & immediate
          </p>
        </div>
      </section>

      {/* Workflow Section */}
      <section id="workflow" style={{ padding: '64px 0', borderBottom: '1px solid var(--border-light)' }}>
        <div className="container">
          <div style={{ textAlign: 'center', marginBottom: '40px' }}>
            <h2 style={{ fontSize: '28px', fontWeight: '800', color: 'var(--text-main)', marginBottom: '8px' }}>
              Structured Clinical Workflow
            </h2>
            <p style={{ fontSize: '15px', color: 'var(--text-muted)' }}>
              From initial symptom intake to a verified veterinary handoff report in 6 cohesive steps.
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
            gap: '16px',
            alignItems: 'stretch',
          }}>
            {workflowSteps.map((step, idx) => {
              const Icon = step.icon;
              return (
                <div key={idx} className="card" style={{
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  position: 'relative',
                  borderTop: '3px solid var(--primary)',
                }}>
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: 'var(--primary-light)',
                    color: 'var(--primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '12px',
                  }}>
                    <Icon size={18} />
                  </div>
                  <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-subtle)', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Step {idx + 1}
                  </div>
                  <h4 style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-main)', marginBottom: '6px' }}>
                    {step.title}
                  </h4>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.45, marginTop: 'auto' }}>
                    {step.desc}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Feature Highlights */}
      <section style={{ padding: '64px 0', borderBottom: '1px solid var(--border-light)' }}>
        <div className="container">
          <div style={{ textAlign: 'center', marginBottom: '48px' }}>
            <h2 style={{ fontSize: '28px', fontWeight: '800', color: 'var(--text-main)', marginBottom: '8px' }}>
              Engineered for Responsible Healthcare
            </h2>
            <p style={{ fontSize: '15px', color: 'var(--text-muted)', maxWidth: '600px', margin: '0 auto' }}>
              Built with evidence-informed triage principles rather than hallucinated medical claims.
            </p>
          </div>

          <div className="grid-3">
            {highlights.map((h, i) => {
              const Icon = h.icon;
              return (
                <div key={i} className="card" style={{ padding: '24px' }}>
                  <div style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: `${h.color}15`,
                    color: h.color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '16px',
                  }}>
                    <Icon size={22} />
                  </div>
                  <h3 style={{ fontSize: '17px', fontWeight: '700', color: 'var(--text-main)', marginBottom: '8px' }}>
                    {h.title}
                  </h3>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: 1.55 }}>
                    {h.desc}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Platform Callout */}
      <section style={{ padding: '60px 0', backgroundColor: 'var(--bg-surface)' }}>
        <div className="container" style={{ textAlign: 'center', maxWidth: '720px' }}>
          <h2 style={{ fontSize: '26px', fontWeight: '800', color: 'var(--text-main)', marginBottom: '14px' }}>
            Ready to Experience VetVision AI?
          </h2>
          <p style={{ fontSize: '15px', color: 'var(--text-muted)', marginBottom: '28px', lineHeight: 1.6 }}>
            Experience the complete intake journey: from dynamic symptom selection to computer-vision photo inspection, explainable factor attribution, and print-ready veterinary handoff summaries.
          </p>
          <Link to="/register" className="btn btn-primary btn-lg">
            Get Started with a Free Account
            <ChevronRight size={18} />
          </Link>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
