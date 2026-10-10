import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Activity,
  Lock,
  Mail,
  Eye,
  EyeOff,
  AlertCircle,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  HeartPulse,
  FileText,
  Stethoscope,
  ArrowRight,
} from 'lucide-react';

export const LoginPage = () => {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const from = location.state?.from?.pathname && location.state.from.pathname !== '/login'
    ? location.state.from.pathname
    : '/dashboard';

  React.useEffect(() => {
    const token = localStorage.getItem('vetvision_access_token');
    if (isAuthenticated || (token && token !== 'undefined' && token !== 'null')) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login({ email, password });
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err.message || 'Login failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemo = () => {
    setEmail('john.doe@vetvision.ai');
    setPassword('Password123!');
  };

  return (
    <div
      style={{
        minHeight: 'calc(100vh - var(--nav-height) - 70px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '32px 20px',
        backgroundColor: 'var(--bg-app)',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '1060px',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: 'var(--radius-xl)',
          border: '1px solid var(--border-light)',
          boxShadow: 'var(--shadow-xl)',
          overflow: 'hidden',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
        }}
      >
        {/* Left Side: Project Showcase & Mission Overview */}
        <div
          style={{
            background: 'linear-gradient(145deg, #0f172a 0%, #134e4a 55%, #0d9488 100%)',
            color: '#ffffff',
            padding: '48px 40px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            position: 'relative',
          }}
        >
          {/* Subtle Ambient Glow */}
          <div
            style={{
              position: 'absolute',
              top: '-60px',
              right: '-60px',
              width: '220px',
              height: '220px',
              borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(20, 184, 166, 0.25) 0%, rgba(20, 184, 166, 0) 70%)',
              pointerEvents: 'none',
            }}
          />

          <div>
            {/* Brand Pill */}
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 14px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: 'rgba(255, 255, 255, 0.12)',
                backdropFilter: 'blur(8px)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                fontSize: '12px',
                fontWeight: '700',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                marginBottom: '24px',
              }}
            >
              <Activity size={15} color="#5eead4" strokeWidth={2.5} />
              <span>Clinical Triage Platform</span>
            </div>

            {/* Main Headline */}
            <h1
              style={{
                fontSize: '28px',
                fontWeight: '800',
                lineHeight: 1.25,
                letterSpacing: '-0.02em',
                marginBottom: '16px',
                color: '#ffffff',
              }}
            >
              Intelligent Veterinary Triage & Health Intelligence
            </h1>

            {/* Project Description */}
            <p
              style={{
                fontSize: '14px',
                lineHeight: 1.65,
                color: '#ccfbf1',
                marginBottom: '32px',
                maxWidth: '460px',
              }}
            >
              VetVision AI bridges pet parents and veterinary practices with calibrated
              clinical risk scoring, multi-symptom Bayesian triage, and structured
              13-point veterinary clinic handoff records.
            </p>

            {/* Feature Pillars */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(255, 255, 255, 0.12)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    marginTop: '2px',
                  }}
                >
                  <HeartPulse size={18} color="#5eead4" />
                </div>
                <div>
                  <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#ffffff', margin: 0 }}>
                    Adaptive Symptom Intake
                  </h4>
                  <p style={{ fontSize: '12px', color: '#99f6e4', margin: '2px 0 0 0', lineHeight: 1.45 }}>
                    Dynamic inquiries tailored to canines and felines, evaluating severity, duration, and co-occurring signs.
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(255, 255, 255, 0.12)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    marginTop: '2px',
                  }}
                >
                  <ShieldCheck size={18} color="#5eead4" />
                </div>
                <div>
                  <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#ffffff', margin: 0 }}>
                    Emergency Override Logic
                  </h4>
                  <p style={{ fontSize: '12px', color: '#99f6e4', margin: '2px 0 0 0', lineHeight: 1.45 }}>
                    Immediate heuristic detection of life-threatening indicators with urgent ER clinic protocols.
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(255, 255, 255, 0.12)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    marginTop: '2px',
                  }}
                >
                  <FileText size={18} color="#5eead4" />
                </div>
                <div>
                  <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#ffffff', margin: 0 }}>
                    Official Clinical Handoffs
                  </h4>
                  <p style={{ fontSize: '12px', color: '#99f6e4', margin: '2px 0 0 0', lineHeight: 1.45 }}>
                    Auditable, versioned reports ready for export, clinic consultation, and owner peace of mind.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Clinical Protocol Badge Footer */}
          <div
            style={{
              marginTop: '40px',
              paddingTop: '20px',
              borderTop: '1px solid rgba(255, 255, 255, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '11px',
              color: '#99f6e4',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Stethoscope size={14} color="#5eead4" />
              <span>Canine & Feline Clinical Standards</span>
            </div>
            <span>v1.0 Ready</span>
          </div>
        </div>

        {/* Right Side: Authentication Form Card */}
        <div
          style={{
            padding: '48px 40px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            backgroundColor: 'var(--bg-surface)',
          }}
        >
          <div style={{ marginBottom: '28px' }}>
            <h2
              style={{
                fontSize: '24px',
                fontWeight: '800',
                color: 'var(--text-main)',
                letterSpacing: '-0.02em',
                marginBottom: '6px',
              }}
            >
              Sign In to Your Account
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Enter your credentials to access patient charts, vitals, and reports.
            </p>
          </div>

          {error && (
            <div
              style={{
                backgroundColor: '#fef2f2',
                border: '1px solid #fecaca',
                borderRadius: 'var(--radius-md)',
                padding: '12px 14px',
                marginBottom: '20px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                color: '#b91c1c',
                fontSize: '13px',
              }}
            >
              <AlertCircle size={18} style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group" style={{ marginBottom: '18px' }}>
              <label
                className="form-label"
                htmlFor="email"
                style={{ fontSize: '13px', fontWeight: '600', marginBottom: '6px', display: 'block' }}
              >
                Email Address
              </label>
              <div style={{ position: 'relative' }}>
                <Mail
                  size={16}
                  style={{
                    position: 'absolute',
                    left: '12px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text-subtle)',
                    pointerEvents: 'none',
                  }}
                />
                <input
                  id="email"
                  type="email"
                  className="form-input"
                  placeholder="name@vetvision.ai"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{ paddingLeft: '38px', height: '42px' }}
                  required
                />
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: '22px' }}>
              <label
                className="form-label"
                htmlFor="password"
                style={{ fontSize: '13px', fontWeight: '600', marginBottom: '6px', display: 'block' }}
              >
                Password
              </label>
              <div style={{ position: 'relative' }}>
                <Lock
                  size={16}
                  style={{
                    position: 'absolute',
                    left: '12px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text-subtle)',
                    pointerEvents: 'none',
                  }}
                />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  className="form-input"
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{ paddingLeft: '38px', paddingRight: '40px', height: '42px' }}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: 'absolute',
                    right: '10px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-subtle)',
                    cursor: 'pointer',
                    padding: '4px',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                  title={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{
                width: '100%',
                height: '44px',
                fontSize: '14px',
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                boxShadow: '0 4px 12px rgba(13, 148, 136, 0.25)',
              }}
              disabled={loading}
            >
              {loading ? (
                'Authenticating Session...'
              ) : (
                <>
                  Sign In <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          {/* Quick-Fill Sample Demo Account */}
          <div
            style={{
              marginTop: '22px',
              padding: '16px',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'var(--bg-muted)',
              border: '1px dashed var(--border-light)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>
              Want to test pre-configured clinical pet records?
            </div>
            <button
              type="button"
              onClick={handleQuickDemo}
              className="btn btn-sm"
              style={{
                width: '100%',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-light)',
                color: 'var(--primary)',
                fontWeight: '700',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-xs)',
              }}
            >
              <Sparkles size={14} color="var(--primary)" />
              Quick-Fill Demo Account (john.doe@vetvision.ai)
            </button>
          </div>

          <p
            style={{
              textAlign: 'center',
              fontSize: '13px',
              color: 'var(--text-muted)',
              marginTop: '24px',
            }}
          >
            New to VetVision AI?{' '}
            <Link
              to="/register"
              style={{ color: 'var(--primary)', fontWeight: '700', textDecoration: 'none' }}
            >
              Create Account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
