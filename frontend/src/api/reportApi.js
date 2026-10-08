import { apiClient } from './client';

export const reportApi = {
  generateReport: async (assessmentId) => {
    const res = await apiClient.post(`/assessments/${assessmentId}/reports`);
    return res.data;
  },

  getAssessmentReports: async (assessmentId) => {
    const res = await apiClient.get(`/assessments/${assessmentId}/reports`);
    return res.data;
  },

  getReport: async (reportId) => {
    const res = await apiClient.get(`/reports/${reportId}`);
    return res.data;
  },

  getReportHtml: async (reportId) => {
    const res = await apiClient.get(`/reports/${reportId}/html`, {
      responseType: 'text',
      headers: {
        Accept: 'text/html',
      },
    });
    return res;
  },
};
