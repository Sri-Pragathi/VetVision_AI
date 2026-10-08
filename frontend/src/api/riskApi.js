import { apiClient } from './client';

export const riskApi = {
  runRiskAnalysis: async (assessmentId) => {
    const res = await apiClient.post(`/assessments/${assessmentId}/risk-analysis`);
    return res.data;
  },

  getRiskAnalysis: async (assessmentId) => {
    const res = await apiClient.get(`/assessments/${assessmentId}/risk-analysis`);
    return res.data;
  },
};
