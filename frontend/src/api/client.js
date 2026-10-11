import axios from 'axios';

function resolveApiBaseUrl(raw) {
  if (!raw || !raw.trim()) {
    return '/api/v1';
  }
  let val = raw.trim().replace(/\/+$/, '');
  if (val.startsWith('http') && !val.includes('/api/v1')) {
    val = `${val}/api/v1`;
  }
  return val;
}

// In local dev, defaults to '/api/v1' (proxied by Vite to http://127.0.0.1:5000).
// In production, can be set via build-time env var VITE_API_BASE_URL.
export const API_BASE_URL = resolveApiBaseUrl(import.meta.env.VITE_API_BASE_URL);

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT access token to outbound requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('vetvision_access_token');
    if (token && token !== 'undefined' && token !== 'null') {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Intercept responses for consistent error formatting and 401 management
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const url = error.config?.url || '';
    const isAuthRoute = url.includes('/auth/logout') || url.includes('/auth/login') || url.includes('/auth/register');

    // If token has expired or is unauthorized on a protected route, notify auth handler once
    if (error.response && error.response.status === 401 && !isAuthRoute) {
      localStorage.removeItem('vetvision_access_token');
      localStorage.removeItem('vetvision_user');
      window.dispatchEvent(new Event('vetvision_auth_expired'));
    }

    let message =
      error.response?.data?.message ||
      (typeof error.response?.data?.error === 'string'
        ? error.response?.data?.error
        : error.response?.data?.error?.message) ||
      error.message ||
      'An unexpected error occurred. Please try again.';

    if (typeof message === 'object') {
      try {
        message = JSON.stringify(message);
      } catch {
        message = 'An unexpected server error occurred.';
      }
    }

    if (error.response?.status === 404 && (url.includes('/api/') || String(url).startsWith('/'))) {
      message = 'Backend API is unreachable. Please verify that the backend server is deployed and VITE_API_BASE_URL is configured.';
    }

    const customError = new Error(message);
    customError.status = error.response?.status;
    customError.details = error.response?.data;
    return Promise.reject(customError);
  }
);
