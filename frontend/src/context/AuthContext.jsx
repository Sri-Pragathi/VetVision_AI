import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi } from '../api/authApi';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('vetvision_user');
    try {
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [accessToken, setAccessToken] = useState(() => {
    return localStorage.getItem('vetvision_access_token') || null;
  });

  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore network errors on logout
    } finally {
      localStorage.removeItem('vetvision_access_token');
      localStorage.removeItem('vetvision_user');
      setUser(null);
      setAccessToken(null);
    }
  }, []);

  // Verify stored session on app load
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('vetvision_access_token');
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const userData = await authApi.getCurrentUser();
        setUser(userData);
        localStorage.setItem('vetvision_user', JSON.stringify(userData));
      } catch (err) {
        if (err.status === 401) {
          logout();
        }
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();

    // Listen for 401 expiration event from API client
    const handleExpired = () => {
      logout();
    };

    window.addEventListener('vetvision_auth_expired', handleExpired);
    return () => window.removeEventListener('vetvision_auth_expired', handleExpired);
  }, [logout]);

  const login = async (credentials) => {
    const data = await authApi.login(credentials);
    // Backend returns { user, tokens: { access_token, refresh_token } }
    const token = data.tokens?.access_token;
    const profile = data.user;

    localStorage.setItem('vetvision_access_token', token);
    localStorage.setItem('vetvision_user', JSON.stringify(profile));

    setAccessToken(token);
    setUser(profile);
    return profile;
  };

  const register = async (userData) => {
    const data = await authApi.register(userData);
    const token = data.tokens?.access_token;
    const profile = data.user;

    localStorage.setItem('vetvision_access_token', token);
    localStorage.setItem('vetvision_user', JSON.stringify(profile));

    setAccessToken(token);
    setUser(profile);
    return profile;
  };

  const value = {
    user,
    accessToken,
    isAuthenticated: Boolean(accessToken && user),
    isLoading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
