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
    // If token has expired or is unauthorized, notify auth handler
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('vetvision_access_token');
      localStorage.removeItem('vetvision_user');
      window.dispatchEvent(new Event('vetvision_auth_expired'));
    }

    const message =
      error.response?.data?.message ||
      error.response?.data?.error ||
      error.message ||
      'An unexpected error occurred. Please try again.';

    const customError = new Error(message);
    customError.status = error.response?.status;
    customError.details = error.response?.data;
    return Promise.reject(customError);
  }
);
