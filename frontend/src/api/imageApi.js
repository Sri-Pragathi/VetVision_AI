import { apiClient } from './client';

export const imageApi = {
  uploadImage: async (assessmentId, file, imageType = 'symptom_area', bodyPart = '', caption = '') => {
    const formData = new FormData();
    formData.append('image', file);
    if (imageType) formData.append('image_type', imageType);
    if (bodyPart) formData.append('body_part', bodyPart);
    if (caption) formData.append('caption', caption);

    const res = await apiClient.post(`/assessments/${assessmentId}/images`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  listImages: async (assessmentId) => {
    const res = await apiClient.get(`/assessments/${assessmentId}/images`);
    return res.data;
  },

  getImageDetails: async (imageId) => {
    const res = await apiClient.get(`/assessment-images/${imageId}`);
    return res.data;
  },

  analyzeImage: async (imageId) => {
    const res = await apiClient.post(`/assessment-images/${imageId}/analyze`);
    return res.data;
  },

  getImageAnalysis: async (imageId) => {
    const res = await apiClient.get(`/assessment-images/${imageId}/analysis`);
    return res.data;
  },

  deleteImage: async (imageId) => {
    const res = await apiClient.delete(`/assessment-images/${imageId}`);
    return res.data;
  },
};
