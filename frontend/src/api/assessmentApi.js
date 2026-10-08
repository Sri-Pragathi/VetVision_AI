import { apiClient } from './client';

export const assessmentApi = {
  startAssessment: async (petId) => {
    const res = await apiClient.post(`/pets/${petId}/assessments`);
    return res.data;
  },
  getAssessment: async (id) => {
    const res = await apiClient.get(`/assessments/${id}`);
    return res.data;
  },
  updateAssessmentStatus: async (id, status) => {
    const res = await apiClient.put(`/assessments/${id}`, { status });
    return res.data;
  },
  deleteAssessment: async (id) => {
    const res = await apiClient.delete(`/assessments/${id}`);
    return res.data;
  },
  addSymptom: async (assessmentId, symptomData) => {
    const res = await apiClient.post(`/assessments/${assessmentId}/symptoms`, symptomData);
    return res.data;
  },
  updateSymptom: async (assessmentId, symptomId, symptomData) => {
    const res = await apiClient.put(`/assessments/${assessmentId}/symptoms/${symptomId}`, symptomData);
    return res.data;
  },
  removeSymptom: async (assessmentId, symptomId) => {
    const res = await apiClient.delete(`/assessments/${assessmentId}/symptoms/${symptomId}`);
    return res.data;
  },
  upsertObservations: async (assessmentId, observations) => {
    const res = await apiClient.put(`/assessments/${assessmentId}/observations`, observations);
    return res.data;
  },
  addNote: async (assessmentId, note) => {
    const res = await apiClient.post(`/assessments/${assessmentId}/notes`, { note });
    return res.data;
  },
  getAiData: async (assessmentId) => {
    const res = await apiClient.get(`/assessments/${assessmentId}/ai-data`);
    return res.data;
  },
};
