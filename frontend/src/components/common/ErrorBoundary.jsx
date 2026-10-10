import React from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an unhandled rendering error:', error, errorInfo);
  }

  componentDidUpdate(prevProps) {
    if (this.state.hasError && (prevProps.locationKey !== this.props.locationKey || prevProps.pathname !== this.props.pathname)) {
      this.setState({ hasError: false, error: null });
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="container" style={{ padding: '3rem 1rem', maxWidth: '640px', margin: '0 auto' }}>
          <div
            className="card"
            style={{
              padding: '2rem',
              backgroundColor: 'white',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid #fecaca',
              boxShadow: 'var(--shadow-md)',
              textAlign: 'center',
            }}
          >
            <div
              style={{
                width: '56px',
                height: '56px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: '#fee2e2',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1.25rem',
              }}
            >
              <AlertTriangle size={28} color="#dc2626" />
            </div>

            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#991b1b', marginBottom: '0.5rem' }}>
              Unexpected View Error
            </h2>
            <p style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)', marginBottom: '1.25rem', lineHeight: 1.5 }}>
              A rendering issue occurred while displaying this section. Your recorded data has been preserved.
            </p>

            {this.state.error?.message && (
              <div
                style={{
                  padding: '0.75rem 1rem',
                  backgroundColor: '#fef2f2',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid #fecaca',
                  fontSize: '0.8rem',
                  fontFamily: 'monospace',
                  color: '#b91c1c',
                  marginBottom: '1.5rem',
                  textAlign: 'left',
                  overflowX: 'auto',
                }}
              >
                {this.state.error.message}
              </div>
            )}

            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
              <button
                onClick={this.handleReset}
                className="btn btn-primary btn-sm"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
              >
                <RefreshCw size={14} /> Try Again
              </button>
              <a
                href="/dashboard"
                className="btn btn-outline btn-sm"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', textDecoration: 'none' }}
              >
                <Home size={14} /> Dashboard
              </a>
              <a
                href="/pets"
                className="btn btn-outline btn-sm"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', textDecoration: 'none' }}
              >
                My Pets
              </a>
              <a
                href="/reports"
                className="btn btn-outline btn-sm"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', textDecoration: 'none' }}
              >
                Reports
              </a>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
