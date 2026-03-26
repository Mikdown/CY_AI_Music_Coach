import axios, { AxiosInstance } from 'axios';

// Use relative paths in development (Vite proxy), absolute in production
const API_BASE_URL = import.meta.env.DEV ? '/api' : 'http://localhost:8000/api';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 120 second timeout for long-running plan generation
});

// Add request/response logging for debugging
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response [${response.status}]:`, response.config.method?.toUpperCase(), response.config.url);
    return response;
  },
  (error) => {
    if (error.response) {
      console.error(
        `❌ API Error [${error.response.status}]:`,
        error.response.config.method?.toUpperCase(),
        error.response.config.url,
        error.response.data
      );
    } else if (error.request) {
      console.error('❌ API Error: No response from server', error.request.url);
    } else {
      console.error('❌ API Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export interface AssessmentData {
  guitar_type: string;
  skill_level: string;
  genre: string;
  session_focus: string;
  mood: string;
}

export interface RefinementMessage {
  message: string;
  session_id: string;
}

export const coachAPI = {
  // Initialize a new session
  initializeSession: async () => {
    const response = await apiClient.post('/initialize');
    return response.data;
  },

  // Submit assessment answers and get practice plan
  submitAssessment: async (assessment: AssessmentData) => {
    const response = await apiClient.post('/assess', assessment);
    return response.data;
  },

  // Refine the practice plan via chat
  refinePlan: async (refinement: RefinementMessage) => {
    const response = await apiClient.post('/refine', refinement);
    return response.data;
  },

  // Reset a session
  resetSession: async (sessionId: string) => {
    const response = await apiClient.post('/session/reset', null, {
      params: { session_id: sessionId },
    });
    return response.data;
  },

  // Health check (root endpoint, not under /api)
  healthCheck: async () => {
    const response = await axios.get(
      import.meta.env.DEV ? 'http://localhost:8000/health' : '/health'
    );
    return response.data;
  },
};

export default apiClient;
