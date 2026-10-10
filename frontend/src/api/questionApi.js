import { apiClient } from './client';

export const questionApi = {
  getNextQuestions: async (assessmentId, batchSize = 5) => {
    const res = await apiClient.get(`/assessments/${assessmentId}/next-questions`, {
      params: { batch_size: batchSize },
    });
    return res.data;
  },
  submitAnswer: async (assessmentId, answerPayload) => {
    const payload = {
      question_id: answerPayload.question_id,
      selected_option_id: answerPayload.selected_option_id || answerPayload.option_id || null,
      answer_text: answerPayload.answer_text || (typeof answerPayload.answer_value === 'string' ? answerPayload.answer_value : null),
      numeric_value: answerPayload.numeric_value ?? null,
      boolean_value: answerPayload.boolean_value ?? null,
    };
    try {
      const res = await apiClient.post(`/assessments/${assessmentId}/answers`, payload);
      return res.data;
    } catch (err) {
      // If answer already exists, update gracefully via PUT
      if (err.status === 409 || err.details?.message?.includes('already been submitted') || err.message?.includes('already been submitted')) {
        const res = await apiClient.put(`/assessments/${assessmentId}/answers`, payload);
        return res.data;
      }
      throw err;
    }
  },
  updateAnswer: async (assessmentId, answerPayload) => {
    const payload = {
      question_id: answerPayload.question_id,
      selected_option_id: answerPayload.selected_option_id || answerPayload.option_id || null,
      answer_text: answerPayload.answer_text || (typeof answerPayload.answer_value === 'string' ? answerPayload.answer_value : null),
      numeric_value: answerPayload.numeric_value ?? null,
      boolean_value: answerPayload.boolean_value ?? null,
    };
    const res = await apiClient.put(`/assessments/${assessmentId}/answers`, payload);
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
