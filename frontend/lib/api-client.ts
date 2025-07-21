import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { toast } from "sonner";
import { RegisterData } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private client: AxiosInstance;
  private refreshPromise: Promise<any> | null = null;

  constructor() {
    console.log("API Client - NEXT_PUBLIC_API_URL:", process.env.NEXT_PUBLIC_API_URL);
    console.log("API Client - Using API_BASE_URL:", API_BASE_URL);
    
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
      withCredentials: true,
    });
    
    // API Client initialized

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = this.getAccessToken();
        const isAuthEndpoint = config.url?.includes('/auth/login') || 
                              config.url?.includes('/auth/register') ||
                              config.url?.includes('/auth/refresh');
        
        
        // Only add auth header if it's NOT an auth endpoint and we have a token
        if (token && config.headers && !isAuthEndpoint) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & {
          _retry?: boolean;
        };

        if (error.response?.status === 401 && !originalRequest._retry) {
          // Don't try to refresh if we're on auth endpoints
          const isAuthEndpoint = originalRequest.url?.includes('/auth/login') || 
                                originalRequest.url?.includes('/auth/register') ||
                                originalRequest.url?.includes('/auth/refresh');
          
          if (!isAuthEndpoint && this.getRefreshToken()) {
            originalRequest._retry = true;

            try {
              if (!this.refreshPromise) {
                this.refreshPromise = this.refreshToken();
              }
              await this.refreshPromise;
              this.refreshPromise = null;

              const token = this.getAccessToken();
              if (token && originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${token}`;
              }
              return this.client(originalRequest);
            } catch (refreshError) {
              this.handleAuthError();
              return Promise.reject(refreshError);
            }
          }
        }

        
        // Handle other errors
        if (error.response?.status === 429) {
          // Handle rate limit / plan limit errors
          const data = error.response.data as any;
          const limitType = data.error?.includes('transações') ? 'transações' :
                           data.error?.includes('contas bancárias') ? 'contas bancárias' :
                           data.error?.includes('IA') ? 'requisições de IA' : 'recursos';
          
          const message = data.upgrade_required 
            ? `Limite de ${limitType} atingido. Faça upgrade do seu plano para continuar.`
            : data.error || 'Limite de uso atingido';
          
          toast.error(message, {
            description: data.usage_info || undefined,
            action: data.upgrade_required ? {
              label: 'Fazer Upgrade',
              onClick: () => window.location.href = '/settings?tab=billing'
            } : undefined,
            duration: 8000
          });
        } else if (error.response?.status === 403) {
          const data = error.response.data as any;
          
          // Check if it's a plan feature restriction
          if (data.upgrade_required) {
            const message = data.feature_required 
              ? `${data.feature_required} disponível apenas em planos superiores`
              : data.error || 'Recurso não disponível no seu plano atual';
            
            toast.error(message, {
              description: `Plano atual: ${data.current_plan || 'Nenhum'}`,
              action: {
                label: 'Ver Planos',
                onClick: () => window.location.href = '/pricing'
              },
              duration: 8000
            });
          } else {
            toast.error("You don't have permission to perform this action");
          }
        } else if (error.response?.status === 404) {
          // Don't show toast for 404 during development
        } else if (error.response?.status === 500) {
          toast.error("Server error. Please try again later");
        } else if (error.message === "Network Error") {
          toast.error("Network error. Please check your connection");
        }

        return Promise.reject(error);
      }
    );
  }

  private getAccessToken(): string | null {
    if (typeof window !== "undefined") {
      return localStorage.getItem("access_token");
    }
    return null;
  }

  private setAccessToken(token: string) {
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", token);
    }
  }

  private getRefreshToken(): string | null {
    if (typeof window !== "undefined") {
      return localStorage.getItem("refresh_token");
    }
    return null;
  }

  private setRefreshToken(token: string) {
    if (typeof window !== "undefined") {
      localStorage.setItem("refresh_token", token);
    }
  }

  private clearTokens() {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
  }

  private async refreshToken() {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error("No refresh token available");
    }

    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/refresh/`, {
        refresh: refreshToken,
      });

      const { access, refresh } = response.data;
      this.setAccessToken(access);
      if (refresh) {
        this.setRefreshToken(refresh);
      }
      return response.data;
    } catch (error) {
      this.clearTokens();
      throw error;
    }
  }

  private handleAuthError() {
    this.clearTokens();
    if (typeof window !== "undefined") {
      const currentPath = window.location.pathname;
      const isAuthPage = currentPath.includes('/login') || 
                        currentPath.includes('/register') || 
                        currentPath.includes('/forgot-password');
      
      if (!isAuthPage) {
        window.location.href = "/login";
      }
    }
  }

  // Authentication methods
  async login(email: string, password: string, two_fa_code?: string) {
    const loginData: any = { email, password };
    if (two_fa_code) {
      loginData.two_fa_code = two_fa_code;
    }
    
    const response = await this.client.post("/api/auth/login/", loginData);
    const { tokens } = response.data;
    if (tokens) {
      this.setAccessToken(tokens.access);
      this.setRefreshToken(tokens.refresh);
    }
    return response.data;
  }

  async logout() {
    const refreshToken = this.getRefreshToken();
    try {
      await this.client.post("/api/auth/logout/", { refresh: refreshToken });
    } finally {
      this.clearTokens();
    }
  }

  async register(data: RegisterData) {
    const response = await this.client.post("/api/auth/register/", data);
    return response.data;
  }

  // Generic methods
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

  // File upload
  async upload<T>(url: string, formData: FormData): Promise<T> {
    const response = await this.client.post<T>(url, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;
