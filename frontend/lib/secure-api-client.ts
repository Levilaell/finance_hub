import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { toast } from "sonner";
import { RegisterData } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Secure API client with httpOnly cookie-based authentication
 * Removes localStorage token storage for enhanced security
 */
class SecureApiClient {
  private client: AxiosInstance;
  private refreshPromise: Promise<any> | null = null;
  private refreshMutex: boolean = false;

  constructor() {
    console.log("Secure API Client - Using API_BASE_URL:", API_BASE_URL);
    
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
      withCredentials: true, // Essential for httpOnly cookies
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor - no longer adds Authorization header
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // Add CSRF token for state-changing operations
        if (['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase() || '')) {
          const csrfToken = this.getCSRFToken();
          if (csrfToken && config.headers) {
            config.headers['X-CSRFToken'] = csrfToken;
          }
        }

        // Add request signing for critical operations
        if (this.isCriticalOperation(config.url || '')) {
          this.addRequestSignature(config);
        }
        
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor with improved refresh logic
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & {
          _retry?: boolean;
        };

        // Handle 401 errors with secure token refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          const isAuthEndpoint = this.isAuthEndpoint(originalRequest.url || '');
          
          if (!isAuthEndpoint) {
            originalRequest._retry = true;

            try {
              // Use mutex to prevent concurrent refresh attempts
              if (!this.refreshMutex) {
                this.refreshMutex = true;
                
                if (!this.refreshPromise) {
                  this.refreshPromise = this.refreshToken();
                }
                
                await this.refreshPromise;
                this.refreshPromise = null;
                this.refreshMutex = false;

                // Retry original request (cookies are automatically included)
                return this.client(originalRequest);
              } else {
                // Wait for ongoing refresh to complete
                if (this.refreshPromise) {
                  await this.refreshPromise;
                  return this.client(originalRequest);
                }
              }
            } catch (refreshError) {
              this.refreshMutex = false;
              this.handleAuthError();
              return Promise.reject(refreshError);
            }
          }
        }

        // Handle other error responses
        this.handleErrorResponse(error);
        return Promise.reject(error);
      }
    );
  }

  private getCSRFToken(): string | null {
    // Extract CSRF token from cookie
    if (typeof document !== 'undefined') {
      const name = 'csrftoken';
      const cookies = document.cookie.split(';');
      
      for (let cookie of cookies) {
        const [cookieName, cookieValue] = cookie.trim().split('=');
        if (cookieName === name) {
          return decodeURIComponent(cookieValue);
        }
      }
    }
    return null;
  }

  private isCriticalOperation(url: string): boolean {
    const criticalEndpoints = [
      '/api/auth/change-password/',
      '/api/auth/delete-account/',
      '/api/auth/2fa/enable/',
      '/api/auth/2fa/disable/',
    ];
    
    return criticalEndpoints.some(endpoint => url.includes(endpoint));
  }

  private addRequestSignature(config: InternalAxiosRequestConfig) {
    if (typeof window === 'undefined') return;

    const timestamp = Math.floor(Date.now() / 1000).toString();
    const nonce = this.generateNonce();
    const requestData = config.data ? JSON.stringify(config.data) : '';
    
    // Generate signature (client-side implementation)
    const signature = this.generateSignature(requestData, timestamp, nonce);
    
    if (config.headers) {
      config.headers['X-Request-Signature'] = signature;
      config.headers['X-Request-Timestamp'] = timestamp;
      config.headers['X-Request-Nonce'] = nonce;
    }
  }

  private generateNonce(): string {
    return Math.random().toString(36).substring(2, 15) + 
           Math.random().toString(36).substring(2, 15);
  }

  private generateSignature(data: string, timestamp: string, nonce: string): string {
    // Simple client-side signature (in production, use proper crypto library)
    const payload = `${data}|${timestamp}|${nonce}`;
    return btoa(payload); // Base64 encode for now - use proper HMAC in production
  }

  private isAuthEndpoint(url: string): boolean {
    const authEndpoints = [
      '/api/auth/login/',
      '/api/auth/register/',
      '/api/auth/refresh/',
      '/api/auth/logout/'
    ];
    return authEndpoints.some(endpoint => url.includes(endpoint));
  }

  private async refreshToken(): Promise<void> {
    try {
      // Call refresh endpoint - cookies are automatically included
      const response = await axios.post(`${API_BASE_URL}/api/auth/refresh/`, {}, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
        }
      });

      // Success - new tokens are set as httpOnly cookies by the server
      console.log('Token refreshed successfully');
      
      // Dispatch event for auth state updates
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('auth-token-refreshed', {
          detail: { user: response.data.user }
        }));
      }
      
    } catch (error) {
      console.error('Token refresh failed:', error);
      throw error;
    }
  }

  private handleAuthError() {
    console.log('Authentication failed - redirecting to login');
    
    // Dispatch event for auth state cleanup
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('auth-error'));
      
      const currentPath = window.location.pathname;
      const isAuthPage = ['/login', '/register', '/forgot-password'].some(
        page => currentPath.includes(page)
      );
      
      if (!isAuthPage) {
        window.location.href = "/login";
      }
    }
  }

  private handleErrorResponse(error: AxiosError) {
    if (error.response?.status === 429) {
      // Handle rate limit errors
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
        toast.error("Você não tem permissão para realizar esta ação");
      }
    } else if (error.response?.status === 500) {
      toast.error("Erro do servidor. Tente novamente mais tarde");
    } else if (error.message === "Network Error") {
      toast.error("Erro de rede. Verifique sua conexão");
    }
  }

  // Authentication methods
  async login(email: string, password: string, two_fa_code?: string) {
    const loginData: any = { email, password };
    if (two_fa_code) {
      loginData.two_fa_code = two_fa_code;
    }
    
    const response = await this.client.post("/api/auth/login/", loginData);
    
    // Tokens are now set as httpOnly cookies by the server
    // No need to handle tokens in the frontend
    return response.data;
  }

  async logout() {
    try {
      await this.client.post("/api/auth/logout/", {});
    } finally {
      // Cookies are cleared by the server
      // Dispatch cleanup event
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('auth-logout'));
      }
    }
  }

  async register(data: RegisterData) {
    const response = await this.client.post("/api/auth/register/", data);
    // Registration automatically logs user in with httpOnly cookies
    return response.data;
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

  // File upload
  async upload<T>(url: string, formData: FormData): Promise<T> {
    const response = await this.client.post<T>(url, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  }

  // Health check method
  async checkAuth(): Promise<boolean> {
    try {
      await this.get('/api/auth/profile/');
      return true;
    } catch (error) {
      return false;
    }
  }
}

export const secureApiClient = new SecureApiClient();
export default secureApiClient;