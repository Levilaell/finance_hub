import { authStorage } from './auth-storage';
import { requiresLocalStorageAuth } from './browser-detection';

/**
 * Enhanced Token Manager for secure JWT token management with comprehensive validation
 * Now supports both cookie and localStorage authentication methods
 */
class TokenManager {
  private refreshPromise: Promise<any> | null = null;
  private refreshTimeoutId: NodeJS.Timeout | null = null;
  private readonly TOKEN_REFRESH_BUFFER = 5 * 60 * 1000; // 5 minutes before expiry
  private readonly MAX_RETRY_ATTEMPTS = 3;
  private retryCount = 0;
  private lastRefreshAttempt = 0;
  private readonly MIN_REFRESH_INTERVAL = 10 * 1000; // 10 seconds minimum between refreshes
  private sessionTimeoutId: NodeJS.Timeout | null = null;
  private readonly SESSION_TIMEOUT = 24 * 60 * 60 * 1000; // 24 hours
  private isSessionExpired = false;
  
  /**
   * Schedule automatic token refresh before expiry with enhanced validation
   */
  scheduleTokenRefresh(expiresIn: number) {
    // Clear any existing timeout
    if (this.refreshTimeoutId) {
      clearTimeout(this.refreshTimeoutId);
    }
    
    // Validate expiry time
    if (!expiresIn || expiresIn <= 0) {
      console.warn('Invalid token expiry time, cannot schedule refresh');
      return;
    }
    
    // Calculate when to refresh (5 minutes before expiry, minimum 30 seconds)
    const refreshTime = Math.max(30000, (expiresIn * 1000) - this.TOKEN_REFRESH_BUFFER);
    
    if (refreshTime > 0 && refreshTime <= 86400000) { // Max 24 hours
      this.refreshTimeoutId = setTimeout(() => {
        this.refreshToken();
      }, refreshTime);
      
      console.debug(`Token refresh scheduled in ${Math.round(refreshTime / 1000)} seconds`);
    }
    
    // Schedule session timeout warning
    this.scheduleSessionTimeout();
  }
  
  /**
   * Schedule session timeout warning and handling
   */
  private scheduleSessionTimeout() {
    if (this.sessionTimeoutId) {
      clearTimeout(this.sessionTimeoutId);
    }
    
    this.sessionTimeoutId = setTimeout(() => {
      this.handleSessionTimeout();
    }, this.SESSION_TIMEOUT);
  }
  
  /**
   * Clear scheduled refresh and session timeout
   */
  clearScheduledRefresh() {
    if (this.refreshTimeoutId) {
      clearTimeout(this.refreshTimeoutId);
      this.refreshTimeoutId = null;
    }
    
    if (this.sessionTimeoutId) {
      clearTimeout(this.sessionTimeoutId);
      this.sessionTimeoutId = null;
    }
  }
  
  /**
   * Handle session timeout with user notification
   */
  private handleSessionTimeout() {
    this.isSessionExpired = true;
    console.warn('Session timeout detected');
    
    // Notify user about session expiry
    if (typeof window !== 'undefined') {
      const event = new CustomEvent('session-timeout', {
        detail: { message: 'Your session has expired. Please log in again.' }
      });
      window.dispatchEvent(event);
    }
    
    this.clearScheduledRefresh();
  }
  
  /**
   * Check if session is expired
   */
  isSessionExpiredFlag(): boolean {
    return this.isSessionExpired;
  }
  
  /**
   * Reset session expiry flag
   */
  resetSessionExpiry() {
    this.isSessionExpired = false;
  }
  
  /**
   * Refresh token with enhanced security and race condition prevention
   */
  async refreshToken(): Promise<any> {
    // Check if session is expired
    if (this.isSessionExpired) {
      throw new Error('Session expired');
    }
    
    // If already refreshing, return the existing promise
    if (this.refreshPromise) {
      return this.refreshPromise;
    }
    
    // Check minimum refresh interval to prevent abuse
    const now = Date.now();
    if (now - this.lastRefreshAttempt < this.MIN_REFRESH_INTERVAL) {
      console.warn('Token refresh too frequent, throttling');
      await new Promise(resolve => setTimeout(resolve, this.MIN_REFRESH_INTERVAL));
    }
    
    this.lastRefreshAttempt = now;
    
    // Create new refresh promise
    this.refreshPromise = this._performRefresh()
      .finally(() => {
        // Clear the promise after completion
        this.refreshPromise = null;
      });
    
    return this.refreshPromise;
  }
  
  /**
   * Perform the actual token refresh with comprehensive security validation
   */
  private async _performRefresh(): Promise<any> {
    try {
      // Validate environment
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      if (!apiUrl.startsWith('http')) {
        throw new Error('Invalid API URL configuration');
      }
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      // Prepare request based on authentication method
      const requestInit: RequestInit = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest', // CSRF protection
        },
        signal: controller.signal,
      };

      if (requiresLocalStorageAuth()) {
        // Use localStorage refresh token in request body
        const refreshToken = authStorage.getRefreshToken();
        if (refreshToken) {
          requestInit.body = JSON.stringify({ refresh: refreshToken });
        }
        // Don't send credentials for localStorage auth
        requestInit.credentials = 'omit';
      } else {
        // Use httpOnly cookie (sent automatically)
        requestInit.credentials = 'include';
        requestInit.body = JSON.stringify({});
      }
      
      const response = await fetch(`${apiUrl}/api/auth/refresh/`, requestInit);
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        // Enhanced error handling based on status code
        switch (response.status) {
          case 401:
            this.isSessionExpired = true;
            throw new Error('Authentication failed - session expired');
          case 403:
            throw new Error('Refresh token invalid or revoked');
          case 429:
            throw new Error('Too many refresh attempts');
          case 500:
          case 502:
          case 503:
            throw new Error('Server error during token refresh');
          default:
            throw new Error(`Token refresh failed: ${response.status}`);
        }
      }
      
      // Validate response content type
      const contentType = response.headers.get('content-type');
      if (!contentType?.includes('application/json')) {
        throw new Error('Invalid response format');
      }
      
      const data = await response.json();
      
      // Validate response structure
      if (!this.validateRefreshResponse(data)) {
        throw new Error('Invalid refresh response format');
      }
      
      // Store new tokens if using localStorage auth
      if (requiresLocalStorageAuth() && data.tokens) {
        console.debug('Storing refreshed tokens in localStorage');
        authStorage.setTokens(data.tokens);
      }
      
      // Reset retry count on success
      this.retryCount = 0;
      
      // Schedule next refresh if we got a new access token lifetime
      if (data.access_token_lifetime) {
        this.scheduleTokenRefresh(data.access_token_lifetime);
      }
      
      console.debug('Token refresh successful');
      return data;
      
    } catch (error) {
      this.retryCount++;
      console.error(`Token refresh failed (attempt ${this.retryCount}):`, error);
      
      // Clear scheduled refresh on error
      this.clearScheduledRefresh();
      
      // If max retries exceeded, mark session as expired
      if (this.retryCount >= this.MAX_RETRY_ATTEMPTS) {
        this.isSessionExpired = true;
        console.error('Max token refresh attempts exceeded, session expired');
      }
      
      throw error;
    }
  }
  
  /**
   * Validate refresh response structure for security
   */
  private validateRefreshResponse(data: any): boolean {
    if (!data || typeof data !== 'object') {
      return false;
    }
    
    // Check if response has expected structure
    const hasValidTokens = (data.access && typeof data.access === 'string') ||
                          (data.tokens && typeof data.tokens === 'object');
    
    return hasValidTokens;
  }
  
  /**
   * Check if currently refreshing
   */
  isRefreshing(): boolean {
    return this.refreshPromise !== null;
  }
  
  /**
   * Wait for ongoing refresh
   */
  async waitForRefresh(): Promise<any> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }
    return null;
  }
  
  /**
   * Validate token format (basic JWT structure check)
   */
  private validateTokenFormat(token: string): boolean {
    if (!token || typeof token !== 'string') {
      return false;
    }
    
    // Basic JWT format check (three parts separated by dots)
    const parts = token.split('.');
    if (parts.length !== 3) {
      return false;
    }
    
    // Check if each part is base64url encoded
    try {
      parts.forEach(part => {
        if (!part) throw new Error('Empty JWT part');
        // Basic base64url pattern check
        if (!/^[A-Za-z0-9_-]+$/.test(part)) {
          throw new Error('Invalid base64url encoding');
        }
      });
      return true;
    } catch {
      return false;
    }
  }
  
  /**
   * Check if token is expired (client-side validation)
   */
  isTokenExpired(token: string): boolean {
    if (!this.validateTokenFormat(token)) {
      return true;
    }
    
    try {
      // Decode JWT payload (without verification)
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      
      return payload.exp && payload.exp < currentTime;
    } catch {
      return true; // If we can't decode, consider it expired
    }
  }
  
  /**
   * Get token expiry time
   */
  getTokenExpiry(token: string): number | null {
    if (!this.validateTokenFormat(token)) {
      return null;
    }
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp || null;
    } catch {
      return null;
    }
  }
  
  /**
   * Initialize token manager with session monitoring
   */
  initialize() {
    if (typeof window === 'undefined') {
      return;
    }
    
    // Listen for session timeout events
    window.addEventListener('session-timeout' as any, this.handleSessionTimeoutEvent.bind(this) as EventListener);
    
    // Listen for visibility change to handle tab switching
    document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
    
    // Listen for online/offline events
    window.addEventListener('online', this.handleOnline.bind(this));
    window.addEventListener('offline', this.handleOffline.bind(this));
    
    console.debug('Token manager initialized');
  }
  
  /**
   * Handle session timeout event
   */
  private handleSessionTimeoutEvent(event: CustomEvent) {
    console.warn('Session timeout event received:', event.detail);
    this.clearScheduledRefresh();
  }
  
  /**
   * Handle visibility change (tab switching)
   */
  private handleVisibilityChange() {
    if (document.hidden) {
      // Tab is hidden, user switched away
      console.debug('Tab hidden, pausing token refresh');
    } else {
      // Tab is visible again, check if we need to refresh
      console.debug('Tab visible, checking token status');
      this.checkTokenStatus();
    }
  }
  
  /**
   * Handle online event
   */
  private handleOnline() {
    console.debug('Connection restored, checking token status');
    this.checkTokenStatus();
  }
  
  /**
   * Handle offline event
   */
  private handleOffline() {
    console.debug('Connection lost, pausing token refresh');
    this.clearScheduledRefresh();
  }
  
  /**
   * Check current token status and refresh if needed
   */
  private async checkTokenStatus() {
    if (this.isSessionExpired) {
      return;
    }
    
    try {
      // Prepare request based on authentication method
      const requestInit: RequestInit = {
        method: 'GET',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        },
      };

      if (requiresLocalStorageAuth()) {
        // Add Authorization header for localStorage auth
        const accessToken = authStorage.getAccessToken();
        if (accessToken) {
          requestInit.headers = {
            ...requestInit.headers,
            'Authorization': `Bearer ${accessToken}`,
          };
        }
        requestInit.credentials = 'omit';
      } else {
        // Use cookie authentication
        requestInit.credentials = 'include';
      }

      // Try to make a simple authenticated request to check token validity
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/profile/`, requestInit);
      
      if (response.status === 401) {
        // Token is invalid, try to refresh
        console.debug('Token invalid, attempting refresh');
        await this.refreshToken();
      }
    } catch (error) {
      console.warn('Token status check failed:', error);
    }
  }
  
  /**
   * Clean up resources
   */
  cleanup() {
    this.clearScheduledRefresh();
    
    if (typeof window !== 'undefined') {
      window.removeEventListener('session-timeout' as any, this.handleSessionTimeoutEvent.bind(this) as EventListener);
      document.removeEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
      window.removeEventListener('online', this.handleOnline.bind(this));
      window.removeEventListener('offline', this.handleOffline.bind(this));
    }
    
    console.debug('Token manager cleaned up');
  }
  
  /**
   * Get current status for debugging
   */
  getStatus() {
    return {
      isRefreshing: this.isRefreshing(),
      isSessionExpired: this.isSessionExpired,
      retryCount: this.retryCount,
      lastRefreshAttempt: this.lastRefreshAttempt,
      hasRefreshScheduled: this.refreshTimeoutId !== null,
      hasSessionTimeout: this.sessionTimeoutId !== null,
    };
  }
}

// Export singleton instance
export const tokenManager = new TokenManager();

// Initialize on import if in browser
if (typeof window !== 'undefined') {
  tokenManager.initialize();
}