import axiosInstance from './axiosInterceptor';

// API service functions
const apiService = {
  getBaseMessage: async () => {
    const response = await axiosInstance.get('/');
    return response.data;
  },



  getOutput: async (formData) => {
    const response = await axiosInstance.post('/api/guides/generate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    // Spring Boot returns ApiResponse<GuideDTO> — normalize to match existing usage
    return { study_guide: response.data.data.content };
  },
};

export default apiService;