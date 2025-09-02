/**
 * Authentication Storage Manager - SIMPLIFIED
 * Always uses localStorage with Bearer tokens (no cookies)
 */

interface TokenData {
  access: string;
  refresh: string;
}

class AuthStorage {
  constructor() {
    if (typeof window !== 'undefined') {
      console.log(`[Auth Storage] Using simplified Bearer token authentication`);
    }
  }

  /**
   * Store authentication tokens in localStorage
   */
  setTokens(tokens: TokenData): void {
    this.setTokensInLocalStorage(tokens);
    console.log(`[Auth Storage] Tokens stored in localStorage`);
  }

  /**
   * Get access token for Authorization header
   */
  getAccessToken(): string | null {
    return this.getTokenFromLocalStorage('access_token');
  }

  /**
   * Get refresh token for refresh requests
   */
  getRefreshToken(): string | null {
    return this.getTokenFromLocalStorage('refresh_token');
  }

  /**
   * Clear all stored tokens
   */
  clearTokens(): void {
    this.clearTokensFromLocalStorage();
    // Also clear any legacy cookies
    this.clearLegacyCookies();
    console.log(`[Auth Storage] Tokens cleared`);
  }

  /**
   * Check if tokens are stored
   */
  hasTokens(): boolean {
    return !!this.getTokenFromLocalStorage('access_token');
  }

  // Private methods

  private setTokensInLocalStorage(tokens: TokenData): void {
    try {
      localStorage.setItem('access_token', tokens.access);
      localStorage.setItem('refresh_token', tokens.refresh);
      
      // Store timestamp for expiry tracking
      localStorage.setItem('tokens_timestamp', Date.now().toString());
    } catch (error) {
      console.error('[Auth Storage] Failed to store in localStorage:', error);
      throw new Error('Failed to store authentication tokens');
    }
  }

  private getTokenFromLocalStorage(key: string): string | null {
    try {
      return localStorage.getItem(key);
    } catch (error) {
      console.error(`[Auth Storage] Failed to read ${key} from localStorage:`, error);
      return null;
    }
  }

  private clearTokensFromLocalStorage(): void {
    try {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token'); 
      localStorage.removeItem('tokens_timestamp');
    } catch (error) {
      console.error('[Auth Storage] Failed to clear localStorage:', error);
    }
  }

  private clearLegacyCookies(): void {
    if (typeof document !== 'undefined') {
      try {
        // Clear any legacy cookies that might exist
        const cookiesToClear = ['access_token', 'refresh_token'];
        
        cookiesToClear.forEach(name => {
          // Clear for different path/domain combinations
          document.cookie = `${name}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
          document.cookie = `${name}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; domain=${window.location.hostname}`;
          document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
        });
      } catch (error) {
        console.warn('[Auth Storage] Failed to clear legacy cookies:', error);
      }
    }
  }

  /**
   * Validate stored tokens (basic format check)
   */
  validateTokens(): boolean {
    const accessToken = this.getAccessToken();
    if (!accessToken) {
      return false;
    }

    // Basic JWT format validation
    const parts = accessToken.split('.');
    if (parts.length !== 3) {
      console.warn('[Auth Storage] Invalid token format');
      return false;
    }

    return true;
  }

  /**
   * Get token expiry from stored access token
   */
  getTokenExpiry(): number | null {
    const accessToken = this.getAccessToken();
    if (!accessToken) {
      return null;
    }

    try {
      const payload = JSON.parse(atob(accessToken.split('.')[1]));
      return payload.exp ? payload.exp * 1000 : null; // Convert to milliseconds
    } catch (error) {
      console.warn('[Auth Storage] Failed to parse token expiry:', error);
      return null;
    }
  }

  /**
   * Check if access token is expired
   */
  isAccessTokenExpired(): boolean {
    const expiry = this.getTokenExpiry();
    if (!expiry) {
      return true;
    }

    return Date.now() >= expiry;
  }

  /**
   * Debug info for troubleshooting
   */
  getDebugInfo() {
    return {
      method: 'localStorage',
      hasAccessToken: !!this.getAccessToken(),
      hasRefreshToken: !!this.getRefreshToken(),
      isAccessTokenExpired: this.isAccessTokenExpired(),
      tokenExpiry: this.getTokenExpiry(),
      tokensValid: this.validateTokens()
    };
  }
}

// Export singleton instance
export const authStorage = new AuthStorage();