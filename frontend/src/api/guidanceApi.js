import { apiClient } from './client';

export const guidanceApi = {
  getQuickQuestions: async () => {
    const res = await apiClient.get('/guidance/quick-questions');
    return res;
  },

  ask: async ({ question, petId, assessmentId }) => {
    const res = await apiClient.post('/guidance/ask', {
      question,
      pet_id: petId || undefined,
      assessment_id: assessmentId || undefined,
    });
    return res;
  },
};
