import axios, { AxiosInstance, AxiosError } from "axios";
import { toast } from "sonner";
import { RegisterData } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor - Add Bearer token
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      
      // Skip auth header for auth endpoints
      const isAuthEndpoint = config.url?.includes('/auth/login') || 
                           config.url?.includes('/auth/register') ||
                           config.url?.includes('/auth/refresh');

      if (!isAuthEndpoint && token) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      return config;
    });

    // Response interceptor - Handle auth errors and auto-refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as any;

        // Handle 401 errors (token expired)
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          // Don't refresh on auth endpoints
          const isAuthEndpoint = originalRequest.url?.includes('/auth/login') || 
                               originalRequest.url?.includes('/auth/register') ||
                               originalRequest.url?.includes('/auth/refresh');

          if (!isAuthEndpoint) {
            try {
              await this.refreshToken();
              
              // Retry with new token
              const newToken = localStorage.getItem('access_token');
              if (newToken) {
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
              }
              
              return this.client(originalRequest);
            } catch (refreshError) {
              this.handleAuthError();
              return Promise.reject(refreshError);
            }
          }
        }

        // Handle other errors
        return Promise.reject(error);
      }
    );
  }

  private async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token');
    }

    const response = await this.client.post('/api/auth/refresh/', {
      refresh: refreshToken
    });

    const { access, refresh } = response.data.tokens || response.data;
    
    localStorage.setItem('access_token', access);
    if (refresh) {
      localStorage.setItem('refresh_token', refresh);
    }

    return response.data;
  }

  private handleAuthError() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    // Redirect to login if not already there
    if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
      window.location.href = '/login';
    }
  }

  private handleError(error: AxiosError) {
    const status = error.response?.status;
    
    if (status === 500) {
      toast.error("Erro interno do servidor");
    } else if (status === 403) {
      toast.error("Você não tem permissão para esta ação");
    } else if (status === 404) {
      // Silent 404s in development
    } else if (error.message === "Network Error") {
      toast.error("Erro de rede. Verifique sua conexão");
    }
  }

  // Auth methods
  async login(email: string, password: string) {
    const response = await this.client.post("/api/auth/login/", { email, password });
    
    if (response.data.tokens) {
      localStorage.setItem('access_token', response.data.tokens.access);
      localStorage.setItem('refresh_token', response.data.tokens.refresh);
    }
    
    return response.data;
  }

  async register(data: RegisterData) {
    const response = await this.client.post("/api/auth/register/", data);
    
    if (response.data.tokens) {
      localStorage.setItem('access_token', response.data.tokens.access);
      localStorage.setItem('refresh_token', response.data.tokens.refresh);
    }
    
    return response.data;
  }

async logout() {

  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

  // Generic HTTP methods
  async get<T>(url: string, params?: any): Promise<T> {
    const response = await this.client.get<T>(url, { params });
    return response.data;
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post<T>(url, data);
    return response.data;
  }

  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.put<T>(url, data);
    return response.data;
  }

  async patch<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.patch<T>(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<T>(url);
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;