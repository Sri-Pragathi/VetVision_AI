import { apiClient } from './client';

export const doctorApi = {
  /**
   * Fetch paginated list of clinical cases with triage filter and review status.
   * @param {Object} params - { triage_level, review_status, search, page, per_page }
   */
  getCases: async (params = {}) => {
    const res = await apiClient.get('/doctor/cases', { params });
    return res.data;
  },

  /**
   * Fetch complete clinical case records, symptoms, images, and AI findings.
   * @param {string} assessmentId
   */
  getCaseDetail: async (assessmentId) => {
    const res = await apiClient.get(`/doctor/cases/${assessmentId}`);
    return res.data;
  },

  /**
   * Submit or update veterinary clinical review, triage override, and prescriptions.
   * @param {string} assessmentId
   * @param {Object} reviewData - { override_triage_level, doctor_notes, recommendations, prescriptions, status }
   */
  submitReview: async (assessmentId, reviewData) => {
    const res = await apiClient.post(`/doctor/cases/${assessmentId}/review`, reviewData);
    return res.data;
  },
};
