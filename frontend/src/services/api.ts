import axios from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api';

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 - 토큰 추가
axiosInstance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ============================================
// api 객체 (서비스들에서 사용)
// ============================================
export const api = {
  // 토큰 관련
  getToken: (): string | null => {
    return localStorage.getItem('token');
  },
  
  setToken: (token: string): void => {
    localStorage.setItem('token', token);
  },
  
  removeToken: (): void => {
    localStorage.removeItem('token');
  },

  // HTTP 요청 메서드
  fetch: async (url: string, options?: RequestInit) => {
    const token = localStorage.getItem('token');
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    };

    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers,
    });

    return response;
  },

  get: async (url: string) => {
    return axiosInstance.get(url);
  },

  post: async (url: string, data?: any) => {
    return axiosInstance.post(url, data);
  },

  put: async (url: string, data?: any) => {
    return axiosInstance.put(url, data);
  },

  delete: async (url: string) => {
    return axiosInstance.delete(url);
  },
};

// ============================================
// 개별 함수 export (기존 호환)
// ============================================
export const getToken = api.getToken;
export const setToken = api.setToken;
export const removeToken = api.removeToken;

// ============================================
// Dashboard API
// ============================================
export const dashboardApi = {
  async getStats(period: 'week' | 'month' | 'all' = 'week') {
    const response = await axiosInstance.get(`/dashboard/stats?period=${period}`);
    return response.data.data;
  },

  async getHistory(period: 'week' | 'month' | 'all' = 'week') {
    const response = await axiosInstance.get(`/dashboard/history?period=${period}`);
    return response.data.data;
  },
};

// ============================================
// 인증 관련
// ============================================
export const login = async (email: string, password: string) => {
  const response = await axiosInstance.post('/auth/login', { email, password });
  return response.data;
};

export const signup = async (email: string, password: string, name: string) => {
  const response = await axiosInstance.post('/auth/signup', { email, password, name });
  return response.data;
};

export const logout = async () => {
  const response = await axiosInstance.post('/auth/logout');
  return response.data;
};

// ============================================
// 알레르기 관련
// ============================================
export const getAllAllergies = async (): Promise<any[]> => {
  const response = await axiosInstance.get('/allergies');
  return response.data.data;
};

// ============================================
// 질병 관련
// ============================================
export const getAllDiseases = async (): Promise<any[]> => {
  const response = await axiosInstance.get('/users/diseases/all');
  return response.data.data;
};

export const getUserDiseases = async (): Promise<any[]> => {
  const response = await axiosInstance.get('/users/diseases');
  return response.data.data;
};

export const updateUserDiseases = async (diseaseIds: number[]): Promise<any> => {
  const response = await axiosInstance.put('/users/diseases', { disease_ids: diseaseIds });
  return response.data;
};

// ============================================
// 특수 상태 관련
// ============================================
export const getAllSpecialConditions = async (): Promise<any[]> => {
  const response = await axiosInstance.get('/users/conditions/all');
  return response.data.data;
};

export const getUserSpecialConditions = async (): Promise<any[]> => {
  const response = await axiosInstance.get('/users/conditions');
  return response.data.data;
};

export const updateUserSpecialConditions = async (conditionIds: number[]): Promise<any> => {
  const response = await axiosInstance.put('/users/conditions', { condition_ids: conditionIds });
  return response.data;
};

// ============================================
// 프로필 관련
// ============================================
export const getUserFullProfile = async (): Promise<any> => {
  const response = await axiosInstance.get('/users/profile/full');
  return response.data.data;
};

export const getUserProfile = async (): Promise<any> => {
  const response = await axiosInstance.get('/users/profile');
  return response.data.data;
};

export const updateUserProfile = async (data: {
  name?: string;
  diet_type?: string | null;
  allergy_ids?: number[];
}): Promise<any> => {
  const response = await axiosInstance.put('/users/profile', data);
  return response.data;
};

export const updateUserHealthProfile = async (data: {
  height?: number;
  weight?: number;
  age_range?: string;
  gender?: string;
}): Promise<any> => {
  const response = await axiosInstance.put('/users/profile/health', data);
  return response.data;
};

// ============================================
// 이미지 업로드
// ============================================
export const uploadImage = async (file: File): Promise<any> => {
  const formData = new FormData();
  formData.append('image', file);

  const response = await axiosInstance.post('/images/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// ============================================
// 스캔 히스토리
// ============================================
export const getScanHistory = async (): Promise<any[]> => {
  const response = await axiosInstance.get('/history');
  return response.data.data;
};

export default api;
