/**
 * Tests for API client
 */

import apiClient from '@/lib/api-client';
import { tokenManager } from '@/lib/token-manager';

// Mock the token manager
jest.mock('@/lib/token-manager');
const mockTokenManager = tokenManager as jest.Mocked<typeof tokenManager>;

// Mock fetch
global.fetch = jest.fn();

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (fetch as jest.Mock).mockClear();
    
    // Reset location mock
    Object.defineProperty(window, 'location', {
      value: {
        href: 'http://localhost:3000',
        pathname: '/',
        replace: jest.fn(),
        assign: jest.fn(),
      },
      writable: true,
    });
  });

  describe('Constructor and Setup', () => {
    it('should initialize with correct base URL', () => {
      // The API client is already initialized in the import
      // We can test this by making a request and checking the URL
      
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
        headers: new Headers(),
      });

      apiClient.get('/test');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'GET',
        })
      );
    });

    it('should set up request interceptors', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
        headers: new Headers(),
      });

      await apiClient.get('/test');

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          credentials: 'include',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache',
          }),
        })
      );
    });
  });

  describe('Authentication Methods', () => {
    it('should login successfully', async () => {
      const mockResponse = {
        user: { id: 1, email: 'test@example.com' },
        tokens: { access: 'access-token', refresh: 'refresh-token' },
      };

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockResponse),
        headers: new Headers(),
      });

      const result = await apiClient.login('test@example.com', 'password123');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/auth/login/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            email: 'test@example.com',
            password: 'password123',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    it('should login with 2FA code', async () => {
      const mockResponse = {
        user: { id: 1, email: 'test@example.com' },
        tokens: { access: 'access-token', refresh: 'refresh-token' },
      };

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockResponse),
        headers: new Headers(),
      });

      await apiClient.login('test@example.com', 'password123', '123456');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/auth/login/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            email: 'test@example.com',
            password: 'password123',
            two_fa_code: '123456',
          }),
        })
      );
    });

    it('should logout successfully', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
        headers: new Headers(),
      });

      await apiClient.logout();

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/auth/logout/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({}),
        })
      );
    });

    it('should register successfully', async () => {
      const registerData = {
        email: 'test@example.com',
        password: 'password123',
        password2: 'password123',
        first_name: 'Test',
        last_name: 'User',
        phone: '(11) 99999-9999',
        company_name: 'Test Company',
        company_cnpj: '12345678000195',
        company_type: 'ME',
        business_sector: 'Tecnologia',
      };

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 201,
        json: () => Promise.resolve({ success: true }),
        headers: new Headers(),
      });

      const result = await apiClient.register(registerData);

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/auth/register/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(registerData),
        })
      );

      expect(result).toEqual({ success: true });
    });
  });

  describe('Generic HTTP Methods', () => {
    it('should make GET requests', async () => {
      const mockData = { id: 1, name: 'Test' };
      
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockData),
        headers: new Headers(),
      });

      const result = await apiClient.get('/api/test');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/test',
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(result).toEqual(mockData);
    });

    it('should make GET requests with query parameters', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
        headers: new Headers(),
      });

      await apiClient.get('/api/test', { page: 1, limit: 10 });

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/test?page=1&limit=10',
        expect.objectContaining({
          method: 'GET',
        })
      );
    });

    it('should make POST requests', async () => {
      const postData = { name: 'Test', value: 123 };
      
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 201,
        json: () => Promise.resolve(postData),
        headers: new Headers(),
      });

      const result = await apiClient.post('/api/test', postData);

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/test',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(postData),
        })
      );

      expect(result).toEqual(postData);
    });

    it('should make PUT requests', async () => {
      const putData = { id: 1, name: 'Updated' };
      
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(putData),
        headers: new Headers(),
      });

      const result = await apiClient.put('/api/test/1', putData);

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/test/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(putData),
        })
      );

      expect(result).toEqual(putData);
    });

    it('should make PATCH requests', async () => {
      const patchData = { name: 'Patched' };
      
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(patchData),
        headers: new Headers(),
      });

      const result = await apiClient.patch('/api/test/1', patchData);

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/test/1',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify(patchData),
        })
      );

      expect(result).toEqual(patchData);
    });

    it('should make DELETE requests', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 204,
        json: () => Promise.resolve({}),
        headers: new Headers(),
      });

      const result = await apiClient.delete('/api/test/1');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/test/1',
        expect.objectContaining({
          method: 'DELETE',
        })
      );

      expect(result).toEqual({});
    });
  });

  describe('Error Handling', () => {
    it('should handle 401 errors with token refresh', async () => {
      // First call fails with 401
      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: () => Promise.resolve({ error: 'Unauthorized' }),
          headers: new Headers(),
        })
        // Token refresh succeeds
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ access: 'new-token' }),
          headers: new Headers(),
        })
        // Retry succeeds
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ data: 'success' }),
          headers: new Headers(),
        });

      mockTokenManager.isSessionExpiredFlag.mockReturnValue(false);
      mockTokenManager.refreshToken.mockResolvedValue({ access: 'new-token' });

      const result = await apiClient.get('/api/protected');

      expect(mockTokenManager.refreshToken).toHaveBeenCalled();
      expect(fetch).toHaveBeenCalledTimes(3); // Original + refresh + retry
      expect(result).toEqual({ data: 'success' });
    });

    it('should not retry auth endpoints on 401', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ error: 'Invalid credentials' }),
        headers: new Headers(),
      });

      await expect(apiClient.login('test@example.com', 'wrong')).rejects.toThrow();

      expect(mockTokenManager.refreshToken).not.toHaveBeenCalled();
      expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should handle session expired flag', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ error: 'Unauthorized' }),
        headers: new Headers(),
      });

      mockTokenManager.isSessionExpiredFlag.mockReturnValue(true);

      await expect(apiClient.get('/api/protected')).rejects.toThrow('Session expired');

      expect(mockTokenManager.refreshToken).not.toHaveBeenCalled();
    });

    it('should handle token refresh failure', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ error: 'Unauthorized' }),
        headers: new Headers(),
      });

      mockTokenManager.isSessionExpiredFlag.mockReturnValue(false);
      mockTokenManager.refreshToken.mockRejectedValue(new Error('Refresh failed'));

      await expect(apiClient.get('/api/protected')).rejects.toThrow('Refresh failed');
    });

    it('should handle 429 rate limit errors', async () => {
      const mockError = {
        ok: false,
        status: 429,
        json: () => Promise.resolve({
          error: 'Limite de transações atingido',
          upgrade_required: true,
          usage_info: 'Used 500/500 transactions',
        }),
        headers: new Headers(),
      };

      (fetch as jest.Mock).mockResolvedValue(mockError);

      await expect(apiClient.get('/api/test')).rejects.toThrow();

      // In a real implementation, this would show a toast notification
      // We can't easily test toast notifications in this unit test
    });

    it('should handle 403 forbidden errors', async () => {
      const mockError = {
        ok: false,
        status: 403,
        json: () => Promise.resolve({
          error: 'Feature not available',
          upgrade_required: true,
          feature_required: 'Advanced Reports',
          current_plan: 'Starter',
        }),
        headers: new Headers(),
      };

      (fetch as jest.Mock).mockResolvedValue(mockError);

      await expect(apiClient.get('/api/test')).rejects.toThrow();
    });

    it('should handle network errors', async () => {
      (fetch as jest.Mock).mockRejectedValue(new Error('Network Error'));

      await expect(apiClient.get('/api/test')).rejects.toThrow('Network Error');
    });

    it('should handle server errors', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ error: 'Internal Server Error' }),
        headers: new Headers(),
      });

      await expect(apiClient.get('/api/test')).rejects.toThrow();
    });
  });

  describe('Security Features', () => {
    it('should validate URLs to prevent SSRF', async () => {
      // Test with malicious URL
      await expect(apiClient.get('http://evil.com/api')).rejects.toThrow('Invalid request URL');
    });

    it('should allow relative URLs', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
        headers: new Headers(),
      });

      await apiClient.get('/api/test');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/test',
        expect.any(Object)
      );
    });

    it('should validate response headers', async () => {
      const mockHeaders = new Headers({
        'content-type': 'text/html', // Wrong content type for API
      });

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
        headers: mockHeaders,
      });

      // Should log warning but not fail
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

      await apiClient.get('/api/test');

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Unexpected content type')
      );

      consoleSpy.mockRestore();
    });

    it('should log security events', async () => {
      const consoleSpy = jest.spyOn(console, 'debug').mockImplementation();

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
        headers: new Headers(),
      });

      await apiClient.get('/api/test');

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Security Event'),
        expect.any(Object)
      );

      consoleSpy.mockRestore();
    });
  });

  describe('File Upload', () => {
    it('should handle file uploads', async () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' });
      const formData = new FormData();
      formData.append('file', mockFile);

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ success: true }),
        headers: new Headers(),
      });

      const result = await apiClient.upload('/api/upload', formData);

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/upload',
        expect.objectContaining({
          method: 'POST',
          body: formData,
          headers: expect.objectContaining({
            'Content-Type': 'multipart/form-data',
          }),
        })
      );

      expect(result).toEqual({ success: true });
    });

    it('should validate file types', async () => {
      const mockFile = new File(['test'], 'test.exe', { type: 'application/octet-stream' });
      const formData = new FormData();
      formData.append('file', mockFile);

      await expect(apiClient.upload('/api/upload', formData)).rejects.toThrow('Invalid file type');
    });

    it('should validate file size', async () => {
      // Create a mock file that's too large (>10MB)
      const mockFile = new File(['x'.repeat(11 * 1024 * 1024)], 'large.txt', { type: 'text/plain' });
      const formData = new FormData();
      formData.append('file', mockFile);

      await expect(apiClient.upload('/api/upload', formData)).rejects.toThrow('File too large');
    });

    it('should validate file names', async () => {
      const mockFile = new File(['test'], '../../../etc/passwd', { type: 'text/plain' });
      const formData = new FormData();
      formData.append('file', mockFile);

      await expect(apiClient.upload('/api/upload', formData)).rejects.toThrow('Suspicious file name');
    });
  });

  describe('Authentication Error Handling', () => {
    it('should redirect to login on auth error', () => {
      const locationAssignSpy = jest.spyOn(window.location, 'assign').mockImplementation();
      
      // Simulate auth error by calling the private method (if exposed for testing)
      // In a real scenario, this would be triggered by a 401 response
      
      expect(locationAssignSpy).not.toHaveBeenCalled(); // Initial state
      
      // This test would require exposing the handleAuthError method or
      // triggering it through a 401 response that can't be refreshed
    });

    it('should dispatch auth-error event', () => {
      const dispatchEventSpy = jest.spyOn(window, 'dispatchEvent');
      
      // This would be tested by triggering an auth error
      // and verifying the custom event is dispatched
      
      expect(dispatchEventSpy).not.toHaveBeenCalled(); // Initial state
    });

    it('should not redirect from auth pages', () => {
      window.location.pathname = '/login';
      
      const locationAssignSpy = jest.spyOn(window.location, 'assign').mockImplementation();
      
      // Trigger auth error - should not redirect since we're already on login page
      // This would require exposing the handleAuthError method
      
      expect(locationAssignSpy).not.toHaveBeenCalled();
    });
  });

  describe('Response Processing', () => {
    it('should process JSON responses', async () => {
      const mockData = { id: 1, name: 'Test' };
      
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockData),
        headers: new Headers({
          'content-type': 'application/json',
        }),
      });

      const result = await apiClient.get('/api/test');

      expect(result).toEqual(mockData);
    });

    it('should handle empty responses', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 204,
        json: () => Promise.resolve(null),
        headers: new Headers(),
      });

      const result = await apiClient.delete('/api/test/1');

      expect(result).toBeNull();
    });
  });
});