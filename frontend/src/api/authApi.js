import { apiClient } from './client';

export const authApi = {
  login: async (credentials) => {
    const res = await apiClient.post('/auth/login', credentials);
    return res.data;
  },
  register: async (userData) => {
    const res = await apiClient.post('/auth/register', userData);
    return res.data;
  },
  logout: async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch {
      // Ignore network errors on logout
    }
  },
  getCurrentUser: async () => {
    const res = await apiClient.get('/users/me');
    return res.data;
  },
  updateProfile: async (data) => {
    const res = await apiClient.put('/users/me', data);
    return res.data;
  },
};
