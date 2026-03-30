import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, null, {
            params: { refresh_token: refreshToken }
          });
          localStorage.setItem('access_token', res.data.access_token);
          error.config.headers.Authorization = `Bearer ${res.data.access_token}`;
          return apiClient(error.config);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      } else {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// API functions
export const authApi = {
  login: (email: string, password: string, totp_code?: string) =>
    apiClient.post('/auth/login', { email, password, totp_code }),
  register: (data: any) => apiClient.post('/auth/register', data),
  verifyEmail: (email: string, code: string) =>
    apiClient.post('/auth/verify-email', { email, code }),
  resendVerification: (email: string) =>
    apiClient.post('/auth/resend-verification', { email }),
  forgotPassword: (email: string) =>
    apiClient.post('/auth/forgot-password', { email }),
  resetPassword: (token: string, new_password: string) =>
    apiClient.post('/auth/reset-password', { token, new_password }),
  getMe: () => apiClient.get('/auth/me'),
  updateMe: (data: any) => apiClient.put('/auth/me', data),
  changePassword: (current: string, next: string) =>
    apiClient.post('/auth/change-password', { current_password: current, new_password: next }),
  setupTOTP: () => apiClient.post('/auth/setup-totp'),
  verifyTOTP: (code: string) => apiClient.post('/auth/verify-totp', { code }),
  disableTOTP: (code: string) => apiClient.post('/auth/disable-totp', { code }),
};

export const dashboardApi = {
  getSummary: () => apiClient.get('/dashboard/summary'),
  getRecentActivities: () => apiClient.get('/dashboard/recent-activities'),
  getSecurityEvents: () => apiClient.get('/dashboard/security-events'),
  getExpiringCertificates: (days?: number) => apiClient.get('/dashboard/expiring-certificates', { params: { days } }),
  getPCActivityChart: (days?: number) => apiClient.get('/dashboard/pc-activity-chart', { params: { days } }),
  getSecurityScoreDistribution: () => apiClient.get('/dashboard/security-score-distribution'),
  getAIInsights: () => apiClient.get('/dashboard/ai-insights'),
};

export const employeeApi = {
  getList: (params?: any) => apiClient.get('/employees', { params }),
  getOne: (id: number) => apiClient.get(`/employees/${id}`),
  create: (data: any) => apiClient.post('/employees', data),
  update: (id: number, data: any) => apiClient.put(`/employees/${id}`, data),
  delete: (id: number) => apiClient.delete(`/employees/${id}`),
  getStats: () => apiClient.get('/employees/stats/summary'),
  getDepartments: () => apiClient.get('/employees/departments'),
  createDepartment: (data: any) => apiClient.post('/employees/departments', data),
  updateDepartment: (id: number, data: any) => apiClient.put(`/employees/departments/${id}`, data),
  deleteDepartment: (id: number) => apiClient.delete(`/employees/departments/${id}`),
};

export const certificateApi = {
  getList: (params?: any) => apiClient.get('/certificates', { params }),
  getOne: (id: number) => apiClient.get(`/certificates/${id}`),
  create: (data: any) => apiClient.post('/certificates', data),
  update: (id: number, data: any) => apiClient.put(`/certificates/${id}`, data),
  delete: (id: number) => apiClient.delete(`/certificates/${id}`),
  getStats: () => apiClient.get('/certificates/stats/summary'),
  getVendors: () => apiClient.get('/certificates/vendors'),
  createVendor: (data: any) => apiClient.post('/certificates/vendors', data),
  getRenewalPredictions: () => apiClient.get('/certificates/ai/renewal-predictions'),
};

export const pcApi = {
  getList: (params?: any) => apiClient.get('/pcs', { params }),
  getOne: (id: number) => apiClient.get(`/pcs/${id}`),
  create: (data: any) => apiClient.post('/pcs', data),
  update: (id: number, data: any) => apiClient.put(`/pcs/${id}`, data),
  getActivities: (id: number, params?: any) => apiClient.get(`/pcs/${id}/activities`, { params }),
  getApplications: (id: number, params?: any) => apiClient.get(`/pcs/${id}/applications`, { params }),
  getSecurityEvents: (id: number, params?: any) => apiClient.get(`/pcs/${id}/security-events`, { params }),
  resolveEvent: (pcId: number, eventId: number) => apiClient.post(`/pcs/${pcId}/security-events/${eventId}/resolve`),
  getAIAnalysis: (id: number) => apiClient.get(`/pcs/${id}/ai-analysis`),
  getStats: () => apiClient.get('/pcs/stats/summary'),
};

export const userApi = {
  getList: (params?: any) => apiClient.get('/users', { params }),
  getOne: (id: number) => apiClient.get(`/users/${id}`),
  create: (data: any) => apiClient.post('/users', data),
  update: (id: number, data: any) => apiClient.put(`/users/${id}`, data),
  delete: (id: number) => apiClient.delete(`/users/${id}`),
  unlock: (id: number) => apiClient.post(`/users/${id}/unlock`),
  getAuditLogs: (id: number) => apiClient.get(`/users/${id}/audit-logs`),
};

export const notificationApi = {
  getList: (params?: any) => apiClient.get('/notifications', { params }),
  markRead: (id: number) => apiClient.post(`/notifications/${id}/read`),
  markAllRead: () => apiClient.post('/notifications/read-all'),
  delete: (id: number) => apiClient.delete(`/notifications/${id}`),
};

export const aiSettingsApi = {
  getList: () => apiClient.get('/ai-settings/'),
  getOne: (id: number) => apiClient.get(`/ai-settings/${id}`),
  create: (data: any) => apiClient.post('/ai-settings/', data),
  update: (id: number, data: any) => apiClient.put(`/ai-settings/${id}`, data),
  delete: (id: number) => apiClient.delete(`/ai-settings/${id}`),
  test: (id: number) => apiClient.post(`/ai-settings/${id}/test`),
  setDefault: (id: number) => apiClient.post(`/ai-settings/${id}/set-default`),
  getProviders: () => apiClient.get('/ai-settings/providers'),
  getStats: () => apiClient.get('/ai-settings/stats/summary'),
};
