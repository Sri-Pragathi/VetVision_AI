import { apiClient } from './client';

export const questionApi = {
  getNextQuestions: async (assessmentId, batchSize = 5) => {
    const res = await apiClient.get(`/assessments/${assessmentId}/next-questions`, {
      params: { batch_size: batchSize },
    });
    return res.data;
  },
  submitAnswer: async (assessmentId, answerPayload) => {
    const res = await apiClient.post(`/assessments/${assessmentId}/answers`, answerPayload);
    return res.data;
  },
  getAnswers: async (assessmentId) => {
    const res = await apiClient.get(`/assessments/${assessmentId}/answers`);
    return res.data;
  },
  getQuestionState: async (assessmentId) => {
    const res = await apiClient.get(`/assessments/${assessmentId}/question-state`);
    return res.data;
  },
};
