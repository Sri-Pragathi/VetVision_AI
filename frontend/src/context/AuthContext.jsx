import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi } from '../api/authApi';

const AuthContext = createContext(null);

const cleanUserProfile = (profile) => {
  if (!profile || typeof profile !== 'object') return profile;
  if (profile.name && typeof profile.name === 'string') {
    const cleanName = profile.name.replace(/^dr\.?\s+/i, '').replace(/,\s*dvm/i, '').trim();
    return { ...profile, name: cleanName };
  }
  return profile;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('vetvision_user');
    try {
      return saved ? cleanUserProfile(JSON.parse(saved)) : null;
    } catch {
      return null;
    }
  });

  const [accessToken, setAccessToken] = useState(() => {
    return localStorage.getItem('vetvision_access_token') || null;
  });

  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(async () => {
    const token = localStorage.getItem('vetvision_access_token');
    localStorage.removeItem('vetvision_access_token');
    localStorage.removeItem('vetvision_user');
    setUser(null);
    setAccessToken(null);

    if (token && token !== 'undefined' && token !== 'null') {
      try {
        await authApi.logout();
      } catch {
        // Ignore network errors on logout
      }
    }
  }, []);

  // Verify stored session on app load
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('vetvision_access_token');
      if (!token || token === 'undefined' || token === 'null') {
        setIsLoading(false);
        return;
      }

      try {
        const userData = await authApi.getCurrentUser();
        const rawProfile = userData?.data || userData;
        const profile = cleanUserProfile(rawProfile);
        setUser(profile);
        localStorage.setItem('vetvision_user', JSON.stringify(profile));
      } catch (err) {
        if (err.status === 401) {
          localStorage.removeItem('vetvision_access_token');
          localStorage.removeItem('vetvision_user');
          setUser(null);
          setAccessToken(null);
        }
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();

    // Listen for 401 expiration event from API client
    const handleExpired = () => {
      localStorage.removeItem('vetvision_access_token');
      localStorage.removeItem('vetvision_user');
      setUser(null);
      setAccessToken(null);
    };

    window.addEventListener('vetvision_auth_expired', handleExpired);
    return () => window.removeEventListener('vetvision_auth_expired', handleExpired);
  }, []);

  const login = async (credentials) => {
    const res = await authApi.login(credentials);
    const data = res?.data || res;
    const token = data?.tokens?.access_token || res?.tokens?.access_token;
    const rawProfile = data?.user || res?.user;
    const profile = cleanUserProfile(rawProfile);

    if (!token) {
      throw new Error('Authentication succeeded but access token was missing.');
    }

    localStorage.setItem('vetvision_access_token', token);
    localStorage.setItem('vetvision_user', JSON.stringify(profile || {}));

    setAccessToken(token);
    setUser(profile);
    setIsLoading(false);
    return profile;
  };

  const register = async (userData) => {
    const res = await authApi.register(userData);
    const data = res?.data || res;
    const token = data?.tokens?.access_token || res?.tokens?.access_token;
    const rawProfile = data?.user || res?.user;
    const profile = cleanUserProfile(rawProfile);

    if (!token) {
      throw new Error('Registration succeeded but access token was missing.');
    }

    localStorage.setItem('vetvision_access_token', token);
    localStorage.setItem('vetvision_user', JSON.stringify(profile || {}));

    setAccessToken(token);
    setUser(profile);
    setIsLoading(false);
    return profile;
  };

  const storedToken = localStorage.getItem('vetvision_access_token');
  const isTokenValid = Boolean(storedToken && storedToken !== 'undefined' && storedToken !== 'null');
  const role = 'pet_owner';
  const isDoctor = false;
  const isOwner = true;

  const value = {
    user,
    accessToken,
    role,
    isDoctor: false,
    isOwner: true,
    isAuthenticated: Boolean((accessToken || isTokenValid) && (user || localStorage.getItem('vetvision_user'))),
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
