import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

// Common Layout Components
import Navbar from './components/common/Navbar';
import Footer from './components/common/Footer';
import LoadingSpinner from './components/common/LoadingSpinner';
import ErrorBoundary from './components/common/ErrorBoundary';

// Pages
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import PetsPage from './pages/PetsPage';
import PetDetailPage from './pages/PetDetailPage';
import AssessmentWizardPage from './pages/AssessmentWizardPage';
import ReportsListPage from './pages/ReportsListPage';
import ReportViewerPage from './pages/ReportViewerPage';

/**
 * ProtectedRoute component: verifies authentication session,
 * displays spinner while loading, redirects unauthenticated users to /login.
 */
function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading, accessToken } = useAuth();
  const location = useLocation();

  const token = accessToken || localStorage.getItem('vetvision_access_token');
  const hasValidToken = Boolean(token && token !== 'undefined' && token !== 'null');

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: '60vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <LoadingSpinner message="Verifying session..." />
      </div>
    );
  }

  if (!isAuthenticated && !hasValidToken) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

/**
 * PublicOnlyRoute component: redirects already authenticated users
 * away from login/register pages directly to /dashboard.
 */
function PublicOnlyRoute({ children }) {
  const { isAuthenticated, isLoading, accessToken } = useAuth();
  const token = accessToken || localStorage.getItem('vetvision_access_token');
  const hasValidToken = Boolean(token && token !== 'undefined' && token !== 'null');

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: '60vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <LoadingSpinner message="Checking authentication..." />
      </div>
    );
  }

  if (isAuthenticated || hasValidToken) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

function AppContent() {
  const location = useLocation();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Navbar />
      <main style={{ flex: 1 }}>
        <ErrorBoundary key={location.pathname} locationKey={location.key} pathname={location.pathname}>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<LandingPage />} />
            <Route
              path="/login"
              element={
                <PublicOnlyRoute>
                  <LoginPage />
                </PublicOnlyRoute>
              }
            />
            <Route
              path="/register"
              element={
                <PublicOnlyRoute>
                  <RegisterPage />
                </PublicOnlyRoute>
              }
            />

            {/* Protected Clinical Application Routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/pets"
              element={
                <ProtectedRoute>
                  <PetsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/pets/:id"
              element={
                <ProtectedRoute>
                  <PetDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/assessments/new"
              element={
                <ProtectedRoute>
                  <AssessmentWizardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/reports"
              element={
                <ProtectedRoute>
                  <ReportsListPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/reports/:id"
              element={
                <ProtectedRoute>
                  <ReportViewerPage />
                </ProtectedRoute>
              }
            />

            {/* 404 Catch-All */}
            <Route
              path="*"
              element={
                <div className="container" style={{ textAlign: 'center', padding: '5rem 1rem' }}>
                  <h1 style={{ fontSize: '3rem', fontWeight: 900, color: 'var(--color-primary)' }}>
                    404
                  </h1>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.75rem' }}>
                    Page Not Found
                  </h2>
                  <p style={{ color: 'var(--color-text-muted)', marginBottom: '1.5rem' }}>
                    The requested clinical page or document does not exist.
                  </p>
                  <Navigate to="/" replace />
                </div>
              }
            />
          </Routes>
        </ErrorBoundary>
      </main>
      <Footer />
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
