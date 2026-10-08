import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  Activity, 
  PlusCircle, 
  FolderHeart, 
  FileText, 
  LogOut, 
  User, 
  Menu, 
  X,
  ShieldCheck,
  LayoutDashboard
} from 'lucide-react';

export const Navbar = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/');
    setMobileMenuOpen(false);
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header style={{
      height: 'var(--nav-height)',
      backgroundColor: 'var(--bg-surface)',
      borderBottom: '1px solid var(--border-light)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      <div className="container" style={{
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        {/* Brand */}
        <Link to={isAuthenticated ? "/dashboard" : "/"} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--primary)',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(13, 148, 136, 0.3)'
          }}>
            <Activity size={22} strokeWidth={2.5} />
          </div>
          <div>
            <span style={{ fontSize: '18px', fontWeight: '800', letterSpacing: '-0.02em', color: 'var(--text-main)' }}>
              VetVision<span style={{ color: 'var(--primary)' }}>.AI</span>
            </span>
            <span style={{ display: 'block', fontSize: '10px', fontWeight: '600', color: 'var(--text-muted)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              Clinical Triage Platform
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }} className="desktop-nav">
          {isAuthenticated ? (
            <>
              <Link 
                to="/dashboard" 
                className={`btn btn-sm ${isActive('/dashboard') ? 'btn-secondary' : ''}`}
                style={{ color: isActive('/dashboard') ? 'var(--primary)' : 'var(--text-muted)' }}
              >
                <LayoutDashboard size={16} />
                Dashboard
              </Link>
              <Link 
                to="/pets" 
                className={`btn btn-sm ${isActive('/pets') ? 'btn-secondary' : ''}`}
                style={{ color: isActive('/pets') ? 'var(--primary)' : 'var(--text-muted)' }}
              >
                <FolderHeart size={16} />
                My Pets
              </Link>
              <Link 
                to="/reports" 
                className={`btn btn-sm ${isActive('/reports') ? 'btn-secondary' : ''}`}
                style={{ color: isActive('/reports') ? 'var(--primary)' : 'var(--text-muted)' }}
              >
                <FileText size={16} />
                Reports
              </Link>
              
              <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--border-light)', margin: '0 4px' }} />

              <Link to="/assessments/new" className="btn btn-primary btn-sm">
                <PlusCircle size={16} />
                New Assessment
              </Link>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: '8px' }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-full)',
                  backgroundColor: 'var(--bg-muted)',
                  fontSize: '12px',
                  fontWeight: '600',
                  color: 'var(--text-main)',
                }}>
                  <User size={14} color="var(--primary)" />
                  <span>{user?.name?.split(' ')[0] || 'User'}</span>
                </div>

                <button 
                  onClick={handleLogout}
                  className="btn btn-secondary btn-sm"
                  title="Sign Out"
                  aria-label="Sign Out"
                >
                  <LogOut size={15} />
                </button>
              </div>
            </>
          ) : (
            <>
              <Link to="/" className="btn btn-sm" style={{ color: 'var(--text-muted)' }}>
                About & Safety
              </Link>
              <Link to="/login" className="btn btn-secondary btn-sm">
                Log In
              </Link>
              <Link to="/register" className="btn btn-primary btn-sm">
                Get Started
              </Link>
            </>
          )}
        </nav>

        {/* Mobile menu toggle */}
        <button 
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="mobile-toggle"
          aria-label="Toggle menu"
          style={{ display: 'none', padding: '6px', color: 'var(--text-main)' }}
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div style={{
          position: 'absolute',
          top: 'var(--nav-height)',
          left: 0,
          right: 0,
          backgroundColor: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border-light)',
          padding: '16px 24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          boxShadow: 'var(--shadow-lg)',
        }}>
          {isAuthenticated ? (
            <>
              <Link to="/dashboard" onClick={() => setMobileMenuOpen(false)} className="btn btn-secondary" style={{ justifyContent: 'flex-start' }}>
                <LayoutDashboard size={18} /> Dashboard
              </Link>
              <Link to="/pets" onClick={() => setMobileMenuOpen(false)} className="btn btn-secondary" style={{ justifyContent: 'flex-start' }}>
                <FolderHeart size={18} /> My Pets
              </Link>
              <Link to="/reports" onClick={() => setMobileMenuOpen(false)} className="btn btn-secondary" style={{ justifyContent: 'flex-start' }}>
                <FileText size={18} /> Clinical Reports
              </Link>
              <Link to="/assessments/new" onClick={() => setMobileMenuOpen(false)} className="btn btn-primary" style={{ justifyContent: 'flex-start' }}>
                <PlusCircle size={18} /> Start Assessment
              </Link>
              <button onClick={handleLogout} className="btn btn-danger" style={{ justifyContent: 'flex-start' }}>
                <LogOut size={18} /> Sign Out ({user?.email})
              </button>
            </>
          ) : (
            <>
              <Link to="/login" onClick={() => setMobileMenuOpen(false)} className="btn btn-secondary">
                Log In
              </Link>
              <Link to="/register" onClick={() => setMobileMenuOpen(false)} className="btn btn-primary">
                Get Started
              </Link>
            </>
          )}
        </div>
      )}

      <style>{`
        @media (max-width: 768px) {
          .desktop-nav { display: none !important; }
          .mobile-toggle { display: block !important; }
        }
      `}</style>
    </header>
  );
};

export default Navbar;
