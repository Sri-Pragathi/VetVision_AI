import { apiClient } from './client';

export const petApi = {
  getPets: async () => {
    const res = await apiClient.get('/pets');
    return res.data;
  },
  getPet: async (id) => {
    const res = await apiClient.get(`/pets/${id}`);
    return res.data;
  },
  createPet: async (petData) => {
    const res = await apiClient.post('/pets', petData);
    return res.data;
  },
  updatePet: async (id, petData) => {
    const res = await apiClient.put(`/pets/${id}`, petData);
    return res.data;
  },
  deletePet: async (id) => {
    const res = await apiClient.delete(`/pets/${id}`);
    return res.data;
  },
  getPetAssessments: async (petId) => {
    const res = await apiClient.get(`/pets/${petId}/assessments`);
    return res.data;
  },
  uploadAvatar: async (petId, file) => {
    const formData = new FormData();
    formData.append('image', file);
    const res = await apiClient.post(`/pets/${petId}/avatar`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
};
