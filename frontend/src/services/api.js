import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

// Configurar axios
const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Interceptor para manejo de errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ====================== USUARIO ======================
export const userAPI = {
  create: (userData) => api.post('/user', userData),
  get: (userId) => api.get(`/user/${userId}`),
  update: (userId, userData) => api.put(`/user/${userId}`, userData),
};

// ====================== CV ======================
export const cvAPI = {
  create: (userId, cvData) => api.post(`/user/${userId}/cv`, cvData),
  getAll: (userId) => api.get(`/user/${userId}/cvs`),
  get: (cvId) => api.get(`/cv/${cvId}`),
  update: (cvId, cvData) => api.put(`/cv/${cvId}`, cvData),
  delete: (cvId) => api.delete(`/cv/${cvId}`),
};

// ====================== FILTROS ======================
export const filtersAPI = {
  create: (userId, filtersData) => api.post(`/user/${userId}/search-filters`, filtersData),
  getAll: (userId) => api.get(`/user/${userId}/search-filters`),
  update: (filterId, filtersData) => api.put(`/search-filters/${filterId}`, filtersData),
};

// ====================== TRABAJOS ======================
export const jobsAPI = {
  getAll: (userId, params = {}) => api.get(`/user/${userId}/jobs`, { params }),
  get: (jobId) => api.get(`/job/${jobId}`),
};

// ====================== POSTULACIONES ======================
export const applicationsAPI = {
  getAll: (userId, params = {}) => api.get(`/user/${userId}/applications`, { params }),
  apply: (userId, jobId, data = {}) => api.post(`/user/${userId}/apply/${jobId}`, data),
  startSearch: (userId) => api.post(`/user/${userId}/start-search`),
  stopSearch: (userId) => api.post(`/user/${userId}/stop-search`),
};

// ====================== IA ======================
export const aiAPI = {
  createConfig: (userId, configData) => api.post(`/user/${userId}/ai-config`, configData),
  getConfig: (userId) => api.get(`/user/${userId}/ai-config`),
};

// ====================== ESTADÍSTICAS ======================
export const statsAPI = {
  get: (userId, days = 30) => api.get(`/user/${userId}/stats`, { params: { days } }),
};

// ====================== HEALTH ======================
export const healthAPI = {
  check: () => api.get('/health'),
  root: () => api.get('/'),
};

export default api;