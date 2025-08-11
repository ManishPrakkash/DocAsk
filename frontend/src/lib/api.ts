import axios, { AxiosResponse } from 'axios';
import { 
  User, UserCreate, UserLogin, AuthToken, Document, DocumentAnalysis, 
  UploadResponse, DocumentStatusUpdate, LegalPlaybook, LegalPlaybookCreate, 
  LegalPlaybookResponse, AnalysisRequest, JobStatus, AnalysisStatistics,
  APIError
} from '@/types';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000',
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token on 401 and redirect to login
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API calls
export const authAPI = {
  register: async (userData: UserCreate): Promise<User> => {
    const response: AxiosResponse<User> = await api.post('/api/auth/register', userData);
    return response.data;
  },

  login: async (credentials: UserLogin): Promise<AuthToken> => {
    const response: AxiosResponse<AuthToken> = await api.post('/api/auth/login', credentials);
    return response.data;
  },

  getProfile: async (): Promise<User> => {
    const response: AxiosResponse<User> = await api.get('/api/user/profile');
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/api/auth/logout');
  }
};

// Document API calls
export const documentAPI = {
  getDocuments: async (skip = 0, limit = 100): Promise<Document[]> => {
    const response: AxiosResponse<Document[]> = await api.get('/api/documents', {
      params: { skip, limit }
    });
    return response.data;
  },

  getDocument: async (id: string): Promise<Document> => {
    const response: AxiosResponse<Document> = await api.get(`/api/documents/${id}`);
    return response.data;
  },

  uploadDocument: async (file: File, onProgress?: (progress: number) => void): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response: AxiosResponse<UploadResponse> = await api.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded / progressEvent.total) * 100);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },

  getDocumentStatus: async (id: string): Promise<DocumentStatusUpdate> => {
    const response: AxiosResponse<DocumentStatusUpdate> = await api.get(`/api/documents/${id}/status`);
    return response.data;
  },

  getDocumentAnalysis: async (id: string): Promise<DocumentAnalysis> => {
    const response: AxiosResponse<DocumentAnalysis> = await api.get(`/api/documents/${id}/analysis`);
    return response.data;
  },

  deleteDocument: async (id: string): Promise<void> => {
    await api.delete(`/api/documents/${id}`);
  }
};

// Playbook API calls
export const playbookAPI = {
  getPlaybooks: async (skip = 0, limit = 100): Promise<LegalPlaybookResponse[]> => {
    const response: AxiosResponse<LegalPlaybookResponse[]> = await api.get('/api/analysis/playbooks', {
      params: { skip, limit }
    });
    return response.data;
  },

  getPlaybook: async (id: string): Promise<LegalPlaybook> => {
    const response: AxiosResponse<LegalPlaybook> = await api.get(`/api/analysis/playbooks/${id}`);
    return response.data;
  },

  createPlaybook: async (data: LegalPlaybookCreate): Promise<LegalPlaybookResponse> => {
    const response: AxiosResponse<LegalPlaybookResponse> = await api.post('/api/analysis/playbooks', data);
    return response.data;
  },

  updatePlaybook: async (id: string, data: Partial<LegalPlaybookCreate>): Promise<LegalPlaybookResponse> => {
    const response: AxiosResponse<LegalPlaybookResponse> = await api.put(`/api/analysis/playbooks/${id}`, data);
    return response.data;
  },

  deletePlaybook: async (id: string): Promise<void> => {
    await api.delete(`/api/analysis/playbooks/${id}`);
  }
};

// Analysis API calls
export const analysisAPI = {
  analyzeWithPlaybook: async (request: AnalysisRequest): Promise<{ job_id: string }> => {
    const response: AxiosResponse<{ job_id: string }> = await api.post('/api/analysis/analyze', request);
    return response.data;
  },

  getJobStatus: async (jobId: string): Promise<JobStatus> => {
    const response: AxiosResponse<JobStatus> = await api.get(`/api/analysis/job/${jobId}/status`);
    return response.data;
  },

  getStatistics: async (): Promise<AnalysisStatistics> => {
    const response: AxiosResponse<AnalysisStatistics> = await api.get('/api/analysis/statistics');
    return response.data;
  }
};

// Health check
export const healthAPI = {
  check: async (): Promise<{ status: string; service: string }> => {
    const response = await api.get('/api/health');
    return response.data;
  }
};

// Utility function to handle API errors
export const handleAPIError = (error: any): string => {
  if (error.response?.data?.detail) {
    // Handle both string and object detail responses
    const detail = error.response.data.detail;
    if (typeof detail === 'string') {
      return detail;
    } else if (Array.isArray(detail)) {
      // Handle validation errors array
      return detail.map((err: any) => err.msg || err.message).join(', ');
    } else if (typeof detail === 'object') {
      // Handle object error details
      return detail.message || detail.msg || JSON.stringify(detail);
    }
    return String(detail);
  }
  if (error.message) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

export default api;