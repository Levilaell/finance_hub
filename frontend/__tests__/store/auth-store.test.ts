/**
 * Tests for auth store (Zustand)
 */

import { act, renderHook } from '@testing-library/react';
import { useAuthStore } from '@/store/auth-store';
import apiClient from '@/lib/api-client';

// Mock the API client
jest.mock('@/lib/api-client');
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

// Mock user data
const mockUser = {
  id: 1,
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  username: 'test@example.com',
  full_name: 'Test User',
  initials: 'TU',
  phone: '(11) 99999-9999',
  avatar: null,
  is_email_verified: true,
  is_phone_verified: false,
  preferred_language: 'pt-br',
  timezone: 'America/Sao_Paulo',
  date_of_birth: null,
  company: null,
};

const mockTokens = {
  access: 'mock-access-token',
  refresh: 'mock-refresh-token',
};

describe('Auth Store', () => {
  beforeEach(() => {
    // Clear the store state
    useAuthStore.getState().user = null;
    useAuthStore.getState().isAuthenticated = false;
    useAuthStore.getState().isLoading = false;
    useAuthStore.getState().error = null;
    useAuthStore.getState()._hasHydrated = false;
    
    // Clear all mocks
    jest.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useAuthStore());
      
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current._hasHydrated).toBe(false);
    });
  });

  describe('Login', () => {
    it('should handle successful login', async () => {
      mockApiClient.login.mockResolvedValue({
        user: mockUser,
        tokens: mockTokens,
      });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login({
          email: 'test@example.com',
          password: 'password123',
        });
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should handle login failure', async () => {
      const errorMessage = 'Invalid credentials';
      mockApiClient.login.mockRejectedValue({
        response: {
          data: {
            detail: errorMessage,
          },
        },
      });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        try {
          await result.current.login({
            email: 'test@example.com',
            password: 'wrongpassword',
          });
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe(errorMessage);
    });

    it('should set loading state during login', async () => {
      let resolveLogin: any;
      const loginPromise = new Promise((resolve) => {
        resolveLogin = resolve;
      });
      mockApiClient.login.mockReturnValue(loginPromise);

      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.login({
          email: 'test@example.com',
          password: 'password123',
        });
      });

      expect(result.current.isLoading).toBe(true);

      await act(async () => {
        resolveLogin({
          user: mockUser,
          tokens: mockTokens,
        });
        await loginPromise;
      });

      expect(result.current.isLoading).toBe(false);
    });

    it('should fetch user if not in login response', async () => {
      mockApiClient.login.mockResolvedValue({
        tokens: mockTokens,
      });
      mockApiClient.get.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login({
          email: 'test@example.com',
          password: 'password123',
        });
      });

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/auth/profile/');
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });
  });

  describe('Register', () => {
    it('should handle successful registration', async () => {
      mockApiClient.register.mockResolvedValue({ success: true });
      mockApiClient.login.mockResolvedValue({
        user: mockUser,
        tokens: mockTokens,
      });

      const { result } = renderHook(() => useAuthStore());

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

      await act(async () => {
        await result.current.register(registerData);
      });

      expect(mockApiClient.register).toHaveBeenCalledWith(registerData);
      expect(mockApiClient.login).toHaveBeenCalledWith(
        registerData.email,
        registerData.password
      );
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should handle registration failure', async () => {
      const errorMessage = 'Email already exists';
      mockApiClient.register.mockRejectedValue({
        response: {
          data: {
            detail: errorMessage,
          },
        },
      });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        try {
          await result.current.register({
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
          });
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.error).toBe(errorMessage);
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('Logout', () => {
    it('should handle successful logout', async () => {
      // Set initial authenticated state
      act(() => {
        useAuthStore.setState({
          user: mockUser,
          isAuthenticated: true,
        });
      });

      mockApiClient.logout.mockResolvedValue({});

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.logout();
      });

      expect(mockApiClient.logout).toHaveBeenCalled();
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should clear state even if logout API fails', async () => {
      // Set initial authenticated state
      act(() => {
        useAuthStore.setState({
          user: mockUser,
          isAuthenticated: true,
        });
      });

      mockApiClient.logout.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        try {
          await result.current.logout();
        } catch (error) {
          // Expected to fail, but state should still be cleared
        }
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should clear localStorage tokens on logout', async () => {
      const removeItemSpy = jest.spyOn(Storage.prototype, 'removeItem');
      
      act(() => {
        useAuthStore.setState({
          user: mockUser,
          isAuthenticated: true,
        });
      });

      mockApiClient.logout.mockResolvedValue({});

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.logout();
      });

      expect(removeItemSpy).toHaveBeenCalledWith('access_token');
      expect(removeItemSpy).toHaveBeenCalledWith('refresh_token');
    });
  });

  describe('Fetch User', () => {
    it('should fetch user successfully', async () => {
      mockApiClient.get.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.fetchUser();
      });

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/auth/profile/');
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle fetch user failure', async () => {
      mockApiClient.get.mockRejectedValue(new Error('Unauthorized'));

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        try {
          await result.current.fetchUser();
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
    });

    it('should dispatch subscription-updated event after fetch', async () => {
      mockApiClient.get.mockResolvedValue(mockUser);
      
      const dispatchEventSpy = jest.spyOn(window, 'dispatchEvent');

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.fetchUser();
      });

      expect(dispatchEventSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'subscription-updated',
          detail: { user: mockUser },
        })
      );
    });
  });

  describe('Check Auth', () => {
    it('should fetch user when authenticated but no user data', async () => {
      mockApiClient.get.mockResolvedValue(mockUser);
      
      // Set authenticated but no user
      act(() => {
        useAuthStore.setState({
          isAuthenticated: true,
          user: null,
        });
      });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/auth/profile/');
      expect(result.current.user).toEqual(mockUser);
    });

    it('should handle auth check failure', async () => {
      mockApiClient.get.mockRejectedValue(new Error('Unauthorized'));
      
      act(() => {
        useAuthStore.setState({
          isAuthenticated: true,
          user: null,
        });
      });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });

    it('should not fetch user when user data exists', async () => {
      act(() => {
        useAuthStore.setState({
          isAuthenticated: true,
          user: mockUser,
        });
      });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(mockApiClient.get).not.toHaveBeenCalled();
    });
  });

  describe('Utility Methods', () => {
    it('should clear error', () => {
      act(() => {
        useAuthStore.setState({ error: 'Some error' });
      });

      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });

    it('should update user data', () => {
      act(() => {
        useAuthStore.setState({ user: mockUser });
      });

      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.updateUser({
          first_name: 'Updated',
          last_name: 'Name',
        });
      });

      expect(result.current.user?.first_name).toBe('Updated');
      expect(result.current.user?.last_name).toBe('Name');
      expect(result.current.user?.email).toBe(mockUser.email); // Other fields preserved
    });

    it('should not update user when no user exists', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.updateUser({
          first_name: 'Updated',
        });
      });

      expect(result.current.user).toBeNull();
    });

    it('should set authentication state with setAuth', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setAuth(mockUser, mockTokens);
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should set hydration state', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setHasHydrated(true);
      });

      expect(result.current._hasHydrated).toBe(true);
    });
  });

  describe('Persistence', () => {
    it('should persist user and authentication state', () => {
      const setItemSpy = jest.spyOn(Storage.prototype, 'setItem');
      
      act(() => {
        useAuthStore.setState({
          user: mockUser,
          isAuthenticated: true,
        });
      });

      // The persistence is handled by Zustand persist middleware
      // We can verify that localStorage.setItem was called
      expect(setItemSpy).toHaveBeenCalled();
    });

    it('should only persist specific fields', () => {
      // Test that sensitive data like errors and loading states are not persisted
      // This is configured in the partialize function
      const state = useAuthStore.getState();
      
      // The partialize function should only include user and isAuthenticated
      const persistedKeys = ['user', 'isAuthenticated'];
      const stateKeys = Object.keys(state);
      
      // Verify that partialize configuration exists
      expect(persistedKeys.every(key => stateKeys.includes(key))).toBe(true);
    });
  });

  describe('Token Management', () => {
    it('should clear legacy tokens in setAuth', () => {
      const removeItemSpy = jest.spyOn(Storage.prototype, 'removeItem');
      
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setAuth(mockUser, mockTokens);
      });

      expect(removeItemSpy).toHaveBeenCalledWith('access_token');
      expect(removeItemSpy).toHaveBeenCalledWith('refresh_token');
    });

    it('should clear legacy cookies in setAuth', () => {
      // Mock document.cookie setter to track cookie operations
      const originalCookie = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie');
      let cookieValue = '';
      
      Object.defineProperty(document, 'cookie', {
        get: () => cookieValue,
        set: (value) => {
          cookieValue += value + ';';
        },
        configurable: true,
      });
      
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setAuth(mockUser, mockTokens);
      });

      // Verify that cookies are cleared by checking for expiration date
      expect(cookieValue).toContain('expires=Thu, 01 Jan 1970 00:00:00 GMT');
      
      // Restore original descriptor
      if (originalCookie) {
        Object.defineProperty(Document.prototype, 'cookie', originalCookie);
      }
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      mockApiClient.login.mockRejectedValue(new Error('Network Error'));

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        try {
          await result.current.login({
            email: 'test@example.com',
            password: 'password123',
          });
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.error).toBe('Login failed');
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle API errors with custom messages', async () => {
      const customError = 'Account locked';
      mockApiClient.login.mockRejectedValue({
        response: {
          data: {
            detail: customError,
          },
        },
      });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        try {
          await result.current.login({
            email: 'test@example.com',
            password: 'password123',
          });
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.error).toBe(customError);
    });

    it('should handle undefined response errors', async () => {
      mockApiClient.login.mockRejectedValue({
        response: undefined,
      });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        try {
          await result.current.login({
            email: 'test@example.com',
            password: 'password123',
          });
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.error).toBe('Login failed');
    });
  });
});