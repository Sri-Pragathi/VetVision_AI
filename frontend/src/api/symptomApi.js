import { apiClient } from './client';

export const symptomApi = {
  getSymptoms: async (params = {}) => {
    const res = await apiClient.get('/symptoms', { params });
    return res.data;
  },
};
