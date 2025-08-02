/**
 * Tests for token manager
 */

import { tokenManager } from '@/lib/token-manager';

// Mock fetch
global.fetch = jest.fn();

describe('Token Manager', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
    jest.useFakeTimers();
    
    // Reset token manager state
    tokenManager.clearScheduledRefresh();
    tokenManager.resetSessionExpiry();
  });

  afterEach(() => {
    jest.useRealTimers();
    tokenManager.cleanup();
  });

  describe('Token Refresh Scheduling', () => {
    it('should schedule token refresh', () => {
      const setTimeoutSpy = jest.spyOn(global, 'setTimeout');
      
      // Schedule refresh for 60 seconds (1 minute)
      tokenManager.scheduleTokenRefresh(60);
      
      // Should schedule refresh 5 minutes before expiry (but minimum 30 seconds)
      // Since expiry is 60 seconds, it should schedule for 30 seconds (minimum)
      expect(setTimeoutSpy).toHaveBeenCalledWith(
        expect.any(Function),
        30000 // 30 seconds in milliseconds
      );
    });

    it('should not schedule refresh for invalid expiry times', () => {
      const setTimeoutSpy = jest.spyOn(global, 'setTimeout');
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
      
      tokenManager.scheduleTokenRefresh(0);
      tokenManager.scheduleTokenRefresh(-1);
      
      expect(setTimeoutSpy).not.toHaveBeenCalled();
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'Invalid token expiry time, cannot schedule refresh'
      );
      
      consoleWarnSpy.mockRestore();
    });

    it('should clear existing timeout when scheduling new refresh', () => {
      const clearTimeoutSpy = jest.spyOn(global, 'clearTimeout');
      
      tokenManager.scheduleTokenRefresh(60);
      tokenManager.scheduleTokenRefresh(120);
      
      expect(clearTimeoutSpy).toHaveBeenCalled();
    });

    it('should schedule session timeout', () => {
      const setTimeoutSpy = jest.spyOn(global, 'setTimeout');
      
      tokenManager.scheduleTokenRefresh(60);
      
      // Should schedule both token refresh and session timeout
      expect(setTimeoutSpy).toHaveBeenCalledTimes(2);
    });

    it('should clear scheduled refresh and session timeout', () => {
      const clearTimeoutSpy = jest.spyOn(global, 'clearTimeout');
      
      tokenManager.scheduleTokenRefresh(60);
      tokenManager.clearScheduledRefresh();
      
      expect(clearTimeoutSpy).toHaveBeenCalledTimes(2); // Refresh + session timeout
    });
  });

  describe('Session Management', () => {
    it('should track session expiry state', () => {
      expect(tokenManager.isSessionExpiredFlag()).toBe(false);
      
      // Simulate session timeout
      tokenManager['handleSessionTimeout']();
      
      expect(tokenManager.isSessionExpiredFlag()).toBe(true);
    });

    it('should reset session expiry', () => {
      tokenManager['handleSessionTimeout']();
      expect(tokenManager.isSessionExpiredFlag()).toBe(true);
      
      tokenManager.resetSessionExpiry();
      expect(tokenManager.isSessionExpiredFlag()).toBe(false);
    });

    it('should dispatch session timeout event', () => {
      const dispatchEventSpy = jest.spyOn(window, 'dispatchEvent');
      
      tokenManager['handleSessionTimeout']();
      
      expect(dispatchEventSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'session-timeout',
          detail: { message: 'Your session has expired. Please log in again.' },
        })
      );
    });
  });

  describe('Token Refresh', () => {
    it('should refresh token successfully', async () => {
      const mockResponse = {
        access: 'new-access-token',
        refresh: 'new-refresh-token',
        access_token_lifetime: 3600,
      };

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockResponse),
        headers: new Headers({
          'content-type': 'application/json',
        }),
      });

      const result = await tokenManager.refreshToken();

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/auth/refresh/',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    it('should handle refresh token failure', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ error: 'Invalid refresh token' }),
        headers: new Headers(),
      });

      const refreshPromise = tokenManager.refreshToken();
      
      // Fast-forward any timers that might be set (like throttling or fetch timeout)
      jest.runAllTimers();
      
      await expect(refreshPromise).rejects.toThrow(
        'Authentication failed - session expired'
      );

      expect(tokenManager.isSessionExpiredFlag()).toBe(true);
    });

    it('should handle different error status codes', async () => {
      const testCases = [
        { status: 403, expectedError: 'Refresh token invalid or revoked' },
        { status: 429, expectedError: 'Too many refresh attempts' },
        { status: 500, expectedError: 'Server error during token refresh' },
        { status: 404, expectedError: 'Token refresh failed: 404' },
      ];

      for (const testCase of testCases) {
        (fetch as jest.Mock).mockResolvedValue({
          ok: false,
          status: testCase.status,
          json: () => Promise.resolve({ error: 'Error' }),
          headers: new Headers(),
        });

        await expect(tokenManager.refreshToken()).rejects.toThrow(testCase.expectedError);

        jest.clearAllMocks();
      }
    });

    it('should validate response content type', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
        headers: new Headers({
          'content-type': 'text/html', // Wrong content type
        }),
      });

      await expect(tokenManager.refreshToken()).rejects.toThrow('Invalid response format');
    });

    it('should validate response structure', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ invalid: 'response' }), // Missing tokens
        headers: new Headers({
          'content-type': 'application/json',
        }),
      });

      await expect(tokenManager.refreshToken()).rejects.toThrow('Invalid refresh response format');
    });

    it('should prevent concurrent refresh requests', async () => {
      let resolveRefresh: any;
      const refreshPromise = new Promise((resolve) => {
        resolveRefresh = resolve;
      });

      (fetch as jest.Mock).mockReturnValue(
        refreshPromise.then(() => ({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ access: 'token' }),
          headers: new Headers({ 'content-type': 'application/json' }),
        }))
      );

      // Start two refresh operations
      const promise1 = tokenManager.refreshToken();
      const promise2 = tokenManager.refreshToken();

      expect(tokenManager.isRefreshing()).toBe(true);

      // Resolve the mock
      resolveRefresh();
      
      const [result1, result2] = await Promise.all([promise1, promise2]);

      // Both should get the same result
      expect(result1).toEqual(result2);
      expect(fetch).toHaveBeenCalledTimes(1); // Only one actual request
    });

    it('should throttle rapid refresh attempts', async () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ access: 'token' }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      // Make first refresh attempt
      const promise1 = tokenManager.refreshToken();
      jest.runAllTimers(); // Process any timers from first call
      await promise1;
      
      // Make second rapid refresh attempt (should be throttled)
      const promise2 = tokenManager.refreshToken();
      
      // Advance timers to handle throttling delay
      jest.advanceTimersByTime(10000); // 10 seconds for MIN_REFRESH_INTERVAL
      
      await promise2;
      
      expect(consoleSpy).toHaveBeenCalledWith(
        'Token refresh too frequent, throttling'
      );
      
      consoleSpy.mockRestore();
    });

    it('should handle network timeouts', async () => {
      (fetch as jest.Mock).mockImplementation(() => 
        new Promise((resolve) => {
          // Never resolve to simulate timeout
        })
      );

      const refreshPromise = tokenManager.refreshToken();
      
      // Fast forward past the timeout
      jest.advanceTimersByTime(10000);
      
      await expect(refreshPromise).rejects.toThrow();
    });

    it('should retry on failure up to max attempts', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ error: 'Server error' }),
        headers: new Headers(),
      });

      // Make multiple refresh attempts to trigger max retries
      for (let i = 0; i < 3; i++) {
        try {
          await tokenManager.refreshToken();
        } catch (error) {
          // Expected to fail
        }
      }

      // After max retries, session should be expired
      expect(tokenManager.isSessionExpiredFlag()).toBe(true);
    });

    it('should schedule next refresh on successful refresh', async () => {
      const scheduleRefreshSpy = jest.spyOn(tokenManager, 'scheduleTokenRefresh');
      
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          access: 'token',
          access_token_lifetime: 3600,
        }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      await tokenManager.refreshToken();

      expect(scheduleRefreshSpy).toHaveBeenCalledWith(3600);
    });
  });

  describe('Token Validation', () => {
    it('should validate JWT token format', () => {
      const validToken = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ';
      const invalidTokens = [
        'invalid-token',
        'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid',
        'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9',
        '',
        'a.b',
      ];

      expect(tokenManager['validateTokenFormat'](validToken)).toBe(true);

      invalidTokens.forEach(token => {
        expect(tokenManager['validateTokenFormat'](token)).toBe(false);
      });
    });

    it('should check token expiration', () => {
      const now = Math.floor(Date.now() / 1000);
      
      // Create a token that expires in 1 hour
      const futurePayload = { exp: now + 3600 };
      const futureToken = `header.${btoa(JSON.stringify(futurePayload))}.signature`;
      
      // Create a token that expired 1 hour ago
      const pastPayload = { exp: now - 3600 };
      const pastToken = `header.${btoa(JSON.stringify(pastPayload))}.signature`;
      
      expect(tokenManager.isTokenExpired(futureToken)).toBe(false);
      expect(tokenManager.isTokenExpired(pastToken)).toBe(true);
    });

    it('should get token expiry time', () => {
      const exp = Math.floor(Date.now() / 1000) + 3600;
      const payload = { exp };
      const token = `header.${btoa(JSON.stringify(payload))}.signature`;
      
      expect(tokenManager.getTokenExpiry(token)).toBe(exp);
    });

    it('should handle invalid tokens in expiry check', () => {
      expect(tokenManager.isTokenExpired('invalid-token')).toBe(true);
      expect(tokenManager.getTokenExpiry('invalid-token')).toBeNull();
    });
  });

  describe('Event Handling', () => {
    it('should initialize event listeners', () => {
      const addEventListenerSpy = jest.spyOn(window, 'addEventListener');
      const documentAddEventListenerSpy = jest.spyOn(document, 'addEventListener');
      
      tokenManager.initialize();
      
      expect(addEventListenerSpy).toHaveBeenCalledWith('session-timeout', expect.any(Function));
      expect(addEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function));
      expect(addEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function));
      expect(documentAddEventListenerSpy).toHaveBeenCalledWith('visibilitychange', expect.any(Function));
    });

    it('should handle online/offline events', () => {
      const checkTokenStatusSpy = jest.spyOn(tokenManager, 'checkTokenStatus' as any);
      const clearScheduledRefreshSpy = jest.spyOn(tokenManager, 'clearScheduledRefresh');
      
      // Simulate going offline
      tokenManager['handleOffline']();
      expect(clearScheduledRefreshSpy).toHaveBeenCalled();
      
      // Simulate coming back online
      tokenManager['handleOnline']();
      expect(checkTokenStatusSpy).toHaveBeenCalled();
    });

    it('should handle visibility change events', () => {
      const checkTokenStatusSpy = jest.spyOn(tokenManager, 'checkTokenStatus' as any);
      
      // Simulate tab becoming visible
      Object.defineProperty(document, 'hidden', { value: false, writable: true });
      tokenManager['handleVisibilityChange']();
      
      expect(checkTokenStatusSpy).toHaveBeenCalled();
    });

    it('should cleanup event listeners', () => {
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');
      const documentRemoveEventListenerSpy = jest.spyOn(document, 'removeEventListener');
      
      tokenManager.cleanup();
      
      expect(removeEventListenerSpy).toHaveBeenCalled();
      expect(documentRemoveEventListenerSpy).toHaveBeenCalled();
    });
  });

  describe('Token Status Checking', () => {
    it('should check token status when not expired', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ user: 'data' }),
        headers: new Headers(),
      });

      await tokenManager['checkTokenStatus']();

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/auth/profile/',
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      );
    });

    it('should refresh token on 401 status check', async () => {
      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: () => Promise.resolve({ error: 'Unauthorized' }),
          headers: new Headers(),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ access: 'new-token' }),
          headers: new Headers({ 'content-type': 'application/json' }),
        });

      const refreshTokenSpy = jest.spyOn(tokenManager, 'refreshToken');

      await tokenManager['checkTokenStatus']();

      expect(refreshTokenSpy).toHaveBeenCalled();
    });

    it('should not check status when session expired', async () => {
      tokenManager['isSessionExpired'] = true;

      await tokenManager['checkTokenStatus']();

      expect(fetch).not.toHaveBeenCalled();
    });
  });

  describe('Status and Debugging', () => {
    it('should return current status', () => {
      const status = tokenManager.getStatus();

      expect(status).toHaveProperty('isRefreshing');
      expect(status).toHaveProperty('isSessionExpired');
      expect(status).toHaveProperty('retryCount');
      expect(status).toHaveProperty('lastRefreshAttempt');
      expect(status).toHaveProperty('hasRefreshScheduled');
      expect(status).toHaveProperty('hasSessionTimeout');

      expect(typeof status.isRefreshing).toBe('boolean');
      expect(typeof status.isSessionExpired).toBe('boolean');
      expect(typeof status.retryCount).toBe('number');
    });

    it('should track refreshing state', async () => {
      let resolveRefresh: any;
      const refreshPromise = new Promise((resolve) => {
        resolveRefresh = resolve;
      });

      (fetch as jest.Mock).mockReturnValue(
        refreshPromise.then(() => ({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ access: 'token' }),
          headers: new Headers({ 'content-type': 'application/json' }),
        }))
      );

      expect(tokenManager.isRefreshing()).toBe(false);

      const refreshTask = tokenManager.refreshToken();
      expect(tokenManager.isRefreshing()).toBe(true);

      resolveRefresh();
      await refreshTask;
      expect(tokenManager.isRefreshing()).toBe(false);
    });

    it('should allow waiting for ongoing refresh', async () => {
      let resolveRefresh: any;
      const refreshPromise = new Promise((resolve) => {
        resolveRefresh = resolve;
      });

      (fetch as jest.Mock).mockReturnValue(
        refreshPromise.then(() => ({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ access: 'token' }),
          headers: new Headers({ 'content-type': 'application/json' }),
        }))
      );

      const refreshTask = tokenManager.refreshToken();
      const waitTask = tokenManager.waitForRefresh();

      expect(waitTask).toBe(refreshTask);

      resolveRefresh();
      const [refreshResult, waitResult] = await Promise.all([refreshTask, waitTask]);
      expect(refreshResult).toEqual(waitResult);
    });
  });

  describe('Error Recovery', () => {
    it('should reset retry count on successful refresh', async () => {
      // First, make some failed attempts
      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ error: 'Server error' }),
        headers: new Headers(),
      });

      try {
        await tokenManager.refreshToken();
      } catch (error) {
        // Expected to fail
      }

      expect(tokenManager.getStatus().retryCount).toBeGreaterThan(0);

      // Now make a successful request
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ access: 'token' }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      await tokenManager.refreshToken();

      expect(tokenManager.getStatus().retryCount).toBe(0);
    });
  });
});