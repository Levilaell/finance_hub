import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { toast } from "sonner";
import { RegisterData } from "@/types";
import { tokenManager } from "./token-manager";
import { requestManager, createRequestKey } from "./request-manager";
import { retryManager } from "./retry-manager";
import { authStorage } from "./auth-storage";
import { requiresLocalStorageAuth } from "./browser-detection";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Helper para logs condicionais - TEMPORARIAMENTE HABILITADO EM PRODUÇÃO PARA DEBUG
const debugLog = (...args: any[]) => {
  // Temporariamente logando em produção para diagnosticar o problema dos relatórios
  console.log('[DEBUG]', ...args);
};

const debugWarn = (...args: any[]) => {
  // Temporariamente logando em produção para diagnosticar o problema dos relatórios
  console.warn('[WARN]', ...args);
};

const debugError = (...args: any[]) => {
  // Temporariamente logando em produção para diagnosticar o problema dos relatórios
  console.error('[ERROR]', ...args);
};

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    debugLog("API Client - NEXT_PUBLIC_API_URL:", process.env.NEXT_PUBLIC_API_URL);
    debugLog("API Client - Using API_BASE_URL:", API_BASE_URL);
    
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
      withCredentials: true,
      // Ensure cookies are sent on all requests
      xsrfCookieName: 'csrftoken',
      xsrfHeaderName: 'X-CSRFToken',
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor with enhanced security
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // Mobile Safari requires Authorization header instead of cookies
        if (requiresLocalStorageAuth()) {
          const accessToken = authStorage.getAccessToken();
          if (accessToken) {
            config.headers.Authorization = `Bearer ${accessToken}`;
            debugLog('[API Client] Using Authorization header for mobile Safari');
          }
          // Don't send credentials for localStorage auth to avoid CORS issues
          config.withCredentials = false;
        } else {
          // Use httpOnly cookies for other browsers
          config.withCredentials = true;
          debugLog('[API Client] Using cookie authentication');
        }
        
        // Add security headers
        config.headers['X-Requested-With'] = 'XMLHttpRequest'; // CSRF protection
        // Note: Cache-Control header removed to avoid CORS preflight issues
        // The backend already sets appropriate cache headers for API responses
        
        // Validate URL to prevent SSRF attacks
        if (config.url && !this.isValidUrl(config.url)) {
          debugError('Invalid URL detected:', config.url);
          return Promise.reject(new Error('Invalid request URL'));
        }
        
        // Add request timestamp for timeout detection
        (config as any).metadata = { startTime: Date.now() };
        
        return config;
      },
      (error) => {
        debugError('Request interceptor error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor with enhanced security validation
    this.client.interceptors.response.use(
      (response) => {
        // Log successful response for security monitoring
        this.logSecurityEvent('api_success', {
          url: response.config.url,
          status: response.status,
          method: response.config.method,
        });
        
        // Validate response headers for security
        this.validateResponseHeaders(response);
        
        return response;
      },
      async (error: AxiosError) => {
        // Log security event for failed requests
        this.logSecurityEvent('api_error', {
          url: error.config?.url,
          status: error.response?.status,
          method: error.config?.method,
          error: error.message,
        });
        
        const originalRequest = error.config as InternalAxiosRequestConfig & {
          _retry?: boolean;
        };

        if (error.response?.status === 401 && !originalRequest._retry) {
          // Don't try to refresh if we're on auth endpoints
          const isAuthEndpoint = originalRequest.url?.includes('/auth/login') || 
                                originalRequest.url?.includes('/auth/register') ||
                                originalRequest.url?.includes('/auth/refresh');
          
          if (!isAuthEndpoint && !tokenManager.isSessionExpiredFlag()) {
            originalRequest._retry = true;

            try {
              // Use token manager for coordinated refresh
              await tokenManager.refreshToken();

              // Retry the original request with credentials
              originalRequest.withCredentials = true;
              return this.client(originalRequest);
            } catch (refreshError) {
              debugError('Token refresh failed during retry:', refreshError);
              this.handleAuthError();
              return Promise.reject(refreshError);
            }
          } else if (tokenManager.isSessionExpiredFlag()) {
            // Session is expired, don't attempt refresh
            this.handleAuthError();
            return Promise.reject(new Error('Session expired'));
          }
        }

        
        // Handle other errors
        if (error.response?.status === 429) {
          // Handle rate limit / plan limit errors
          const data = error.response.data as any;
          
          // Handle both string and object error formats
          const errorMessage = typeof data.error === 'string' 
            ? data.error 
            : data.error?.message || 'Rate limit exceeded';
          
          const limitType = errorMessage.includes('transações') ? 'transações' :
                           errorMessage.includes('contas bancárias') ? 'contas bancárias' :
                           errorMessage.includes('IA') ? 'requisições de IA' : 'recursos';
          
          const message = data.upgrade_required 
            ? `Limite de ${limitType} atingido. Faça upgrade do seu plano para continuar.`
            : errorMessage;
          
          // Extract wait time if available
          const waitTime = data.error?.details?.wait_time || data.wait_time;
          const description = waitTime 
            ? `Tente novamente em ${Math.ceil(waitTime)} segundos`
            : data.usage_info || undefined;
          
          toast.error(message, {
            description,
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

  // Legacy token methods - now handled by authStorage
  private getAccessToken(): string | null {
    return authStorage.getAccessToken();
  }

  private getRefreshToken(): string | null {
    return authStorage.getRefreshToken();
  }

  private clearTokens() {
    authStorage.clearTokens();
  }

  private async refreshToken() {
    // Delegate to token manager for coordinated refresh
    return tokenManager.refreshToken();
  }


  // Authentication methods
  async login(email: string, password: string, two_fa_code?: string) {
    const loginData: any = { email, password };
    if (two_fa_code) {
      loginData.two_fa_code = two_fa_code;
    }
    
    const response = await this.client.post("/api/auth/login/", loginData);
    
    // Handle token storage based on browser capabilities
    if (requiresLocalStorageAuth() && response.data.tokens) {
      debugLog('[API Client] Storing tokens in localStorage for mobile Safari');
      authStorage.setTokens(response.data.tokens);
    } else {
      debugLog('[API Client] Using cookie authentication, tokens handled by backend');
      // Clear any legacy localStorage tokens
      authStorage.clearTokens();
    }
    
    return response.data;
  }

  async logout() {
    try {
      // Send refresh token if using localStorage auth
      if (requiresLocalStorageAuth()) {
        const refreshToken = authStorage.getRefreshToken();
        await this.client.post("/api/auth/logout/", { 
          refresh: refreshToken 
        });
      } else {
        // Cookie-based logout (refresh token in httpOnly cookie)
        await this.client.post("/api/auth/logout/", {});
      }
    } finally {
      // Clear tokens using appropriate method
      authStorage.clearTokens();
    }
  }

  async register(data: RegisterData) {
    const response = await this.client.post("/api/auth/register/", data);
    return response.data;
  }

  // Generic methods
  async get<T>(url: string, params?: any, options?: { skipCache?: boolean; priority?: boolean; useRetry?: boolean }): Promise<T> {
    const requestKey = createRequestKey(url, params);
    
    const executeRequest = async () => {
      return requestManager.executeRequest(
        requestKey,
        async () => {
          const response = await this.client.get<T>(url, { params });
          return response.data;
        },
        {
          cacheTTL: 5000, // Cache GET requests for 5 seconds
          skipCache: options?.skipCache,
          priority: options?.priority,
        }
      );
    };

    // Use retry manager for important endpoints
    if (options?.useRetry !== false && this.shouldUseRetry(url)) {
      return retryManager.executeWithRetry(executeRequest, {
        maxRetries: 3,
        shouldRetry: (error) => {
          // Don't retry on 4xx errors except 429
          if (error.response?.status && error.response.status >= 400 && error.response.status < 500) {
            return error.response.status === 429;
          }
          return true;
        },
        onRetry: (attempt, delay) => {
          debugLog(`Retrying ${url} - attempt ${attempt} after ${delay}ms`);
        }
      });
    }

    return executeRequest();
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

  // File upload with security validation
  async upload<T>(url: string, formData: FormData): Promise<T> {
    // Validate file upload for security
    this.validateFileUpload(formData);
    
    const response = await this.client.post<T>(url, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  }
  
  // Security validation methods
  
  /**
   * Validate URL to prevent SSRF attacks
   */
  private isValidUrl(url: string): boolean {
    if (!url) return false;
    
    // Allow relative URLs (starting with /)
    if (url.startsWith('/')) return true;
    
    try {
      const urlObj = new URL(url, API_BASE_URL);
      const baseUrl = new URL(API_BASE_URL);
      
      // Only allow requests to the same origin
      return urlObj.origin === baseUrl.origin;
    } catch {
      return false;
    }
  }
  
  /**
   * Validate response headers for security
   */
  private validateResponseHeaders(response: any) {
    const headers = response.headers;
    
    // Helper to get header case-insensitively
    const getHeader = (name: string) => {
      const lowerName = name.toLowerCase();
      return headers[lowerName] || headers[name] || 
             headers[name.replace(/-/g, '_')] || undefined;
    };
    
    // Debug logging in development
    if (process.env.NODE_ENV === 'development') {
      const availableHeaders = Object.keys(headers).join(', ');
      debugLog('Available response headers:', availableHeaders);
    }
    
    // Check for security headers (case-insensitive)
    if (!getHeader('x-content-type-options')) {
      debugWarn('Missing X-Content-Type-Options header');
    }
    
    if (!getHeader('x-frame-options') && !getHeader('content-security-policy')) {
      debugWarn('Missing X-Frame-Options or CSP header');
    }
    
    // Validate content type for JSON responses
    const contentType = getHeader('content-type');
    if (contentType && !contentType.includes('application/json') && response.config.url?.includes('/api/')) {
      debugWarn('Unexpected content type for API response:', contentType);
    }
  }
  
  /**
   * Validate file upload for security
   */
  private validateFileUpload(formData: FormData) {
    const allowedTypes = [
      'image/jpeg', 'image/png', 'image/gif', 'image/webp',
      'application/pdf', 'text/csv', 'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];
    
    const maxFileSize = 10 * 1024 * 1024; // 10MB
    
    for (const [key, value] of formData.entries()) {
      if (value instanceof File) {
        // Check file type
        if (!allowedTypes.includes(value.type)) {
          throw new Error(`Invalid file type: ${value.type}`);
        }
        
        // Check file size
        if (value.size > maxFileSize) {
          throw new Error(`File too large: ${value.size} bytes`);
        }
        
        // Check file name for suspicious patterns
        if (this.hasSuspiciousFileName(value.name)) {
          throw new Error(`Suspicious file name: ${value.name}`);
        }
      }
    }
  }
  
  /**
   * Check for suspicious file names
   */
  private hasSuspiciousFileName(fileName: string): boolean {
    const suspiciousPatterns = [
      /\.(exe|bat|cmd|scr|pif|com|vbs|js|jar|app|deb|rpm)$/i,
      /\.(php|asp|jsp|py|rb|pl)$/i,
      /\.\./,
      /[<>:"|?*]/,
      /^(con|prn|aux|nul|com[1-9]|lpt[1-9])$/i
    ];
    
    return suspiciousPatterns.some(pattern => pattern.test(fileName));
  }
  
  /**
   * Log security events for monitoring
   */
  private logSecurityEvent(eventType: string, data: any) {
    // In development, just log to console
    if (process.env.NODE_ENV === 'development') {
      debugLog(`Security Event [${eventType}]:`, data);
      return;
    }
    
    // In production, you could send to monitoring service
    // Example: send to Sentry, DataDog, or custom monitoring endpoint
    try {
      // Implement your monitoring logic here
      // In production, this would send to your monitoring service
      // For now, we don't log to console in production
    } catch (error) {
      // Even in production, we don't want to expose errors to console
    }
  }
  
  /**
   * Enhanced auth error handling with security logging
   */
  private handleAuthError() {
    this.logSecurityEvent('auth_error', {
      timestamp: Date.now(),
      path: typeof window !== 'undefined' ? window.location.pathname : 'unknown',
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
    });
    
    this.clearTokens();
    tokenManager.resetSessionExpiry();
    
    if (typeof window !== "undefined") {
      const currentPath = window.location.pathname;
      const isAuthPage = currentPath.includes('/login') || 
                        currentPath.includes('/register') || 
                        currentPath.includes('/forgot-password');
      
      if (!isAuthPage) {
        // Notify user before redirect
        const event = new CustomEvent('auth-error', {
          detail: { message: 'Your session has expired. Please log in again.' }
        });
        window.dispatchEvent(event);
        
        // Small delay to allow notification to be seen
        setTimeout(() => {
          window.location.href = "/login";
        }, 1000);
      }
    }
  }
  
  /**
   * Determine if an endpoint should use retry logic
   */
  private shouldUseRetry(url: string): boolean {
    // Critical endpoints that should retry on failure
    const retryEndpoints = [
      '/api/banking/dashboard',
      '/api/banking/accounts',
      '/api/banking/transactions',
      '/api/companies/usage-limits',
      '/api/companies/subscription-status',
      '/api/auth/refresh',
    ];
    
    return retryEndpoints.some(endpoint => url.includes(endpoint));
  }
}

export const apiClient = new ApiClient();
export default apiClient;
