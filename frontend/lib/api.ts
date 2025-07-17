// frontend/lib/api.ts

import axios from 'axios';
import { toast } from 'sonner';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    // Get token from localStorage or cookies
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Try to refresh token
        const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;
        
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken
          });
          
          const { access } = response.data;
          
          // Save new token
          if (typeof window !== 'undefined') {
            localStorage.setItem('access_token', access);
          }
          
          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    
    // Handle other errors
    if (error.response?.status === 403) {
      toast.error('Você não tem permissão para realizar esta ação');
    } else if (error.response?.status === 404) {
      toast.error('Recurso não encontrado');
    } else if (error.response?.status === 500) {
      toast.error('Erro interno do servidor. Tente novamente mais tarde');
    } else if (error.code === 'ECONNABORTED') {
      toast.error('Tempo de resposta excedido. Tente novamente');
    } else if (!error.response) {
      toast.error('Erro de conexão. Verifique sua internet');
    }
    
    return Promise.reject(error);
  }
);

// Helper functions
export const setAuthToken = (token: string) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', token);
  }
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
};

export const removeAuthToken = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
  delete api.defaults.headers.common['Authorization'];
};

export const isAuthenticated = (): boolean => {
  if (typeof window === 'undefined') return false;
  return !!localStorage.getItem('access_token');
};

// Export types for better TypeScript support
export type ApiError = {
  response?: {
    data?: {
      detail?: string;
      message?: string;
      error?: string;
      errors?: Record<string, string[]>;
    };
    status?: number;
  };
  message?: string;
};

export const getErrorMessage = (error: ApiError): string => {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  if (error.response?.data?.error) {
    return error.response.data.error;
  }
  if (error.response?.data?.errors) {
    // Handle field errors
    const errors = error.response.data.errors;
    const firstError = Object.values(errors)[0];
    return Array.isArray(firstError) ? firstError[0] : 'Erro de validação';
  }
  return error.message || 'Ocorreu um erro inesperado';
};