import axios from 'axios';

// Resolve base URL from environment or default to local FastAPI proxy
const baseURL = import.meta.env.VITE_API_BASE_URL 
  ? `${import.meta.env.VITE_API_BASE_URL}/api`
  : '/api';

// Create API Client with base URL and timeout
const API = axios.create({
  baseURL,
  timeout: 60000, // 60s for video/AI processing
});

// Response interceptor for clean error handling
API.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred while communicating with the server.';
    return Promise.reject(new Error(message));
  }
);

export const apiService = {
  // Health check
  healthCheck: () => API.get('/health'),

  // Auth endpoints (stub — no auth backend in this MVP)
  login: (credentials) => API.post('/auth/login', credentials),
  register: (userData) => API.post('/auth/register', userData),

  // Image analysis
  analyzeImage: (formData) =>
    API.post('/image/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  // Video analysis
  analyzeVideo: (formData) =>
    API.post('/video/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  // Synthetic audio analysis
  analyzeAudio: (formData) =>
    API.post('/audio/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  // Digital Identity Verification (ID Document + Selfie)
  verifyIdentity: (formData) =>
    API.post('/identity/verify', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  // Verification history — supports verification_type and risk_level query params
  getHistory: (params = {}) => API.get('/history', { params }),

  // Dashboard aggregate statistics (per-type counts + risk level breakdown)
  getStats: () => API.get('/stats'),

  // Single verification result details
  getVerificationDetails: (id) => API.get(`/history/${id}`),

  // PDF report download URL
  getReportPdfUrl: (id) => `${baseURL}/report/${id}/download`,
};

export default apiService;
