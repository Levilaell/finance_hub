/**
 * Tests for useAuth hook
 */

import { renderHook, act } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import { useAuth, useRequireAuth, useOptionalAuth } from '@/hooks/use-auth';
import { useAuthStore } from '@/store/auth-store';

// Mock Next.js router
jest.mock('next/navigation');
const mockRouter = useRouter as jest.MockedFunction<typeof useRouter>;
const mockPush = jest.fn();

// Mock auth store
jest.mock('@/store/auth-store');
const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;

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

describe('useAuth Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    mockRouter.mockReturnValue({
      push: mockPush,
      replace: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
      prefetch: jest.fn(),
    } as any);
  });

  describe('Basic Functionality', () => {
    it('should return auth state from store', () => {
      const mockFetchUser = jest.fn();
      
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        _hasHydrated: true,
        fetchUser: mockFetchUser,
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
    });

    it('should show loading state when not hydrated', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        _hasHydrated: false, // Not hydrated
        fetchUser: jest.fn(),
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.isLoading).toBe(true);
    });

    it('should combine store loading and hydration state', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: true, // Store is loading
        error: null,
        _hasHydrated: true, // But hydrated
        fetchUser: jest.fn(),
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.isLoading).toBe(true);
    });
  });

  describe('Authentication Required (requireAuth = true)', () => {
    it('should redirect to login when not authenticated', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        _hasHydrated: true,
        fetchUser: jest.fn(),
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      renderHook(() => useAuth(true));

      expect(mockPush).toHaveBeenCalledWith('/login');
    });

    it('should not redirect when authenticated', () => {
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        _hasHydrated: true,
        fetchUser: jest.fn(),
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      renderHook(() => useAuth(true));

      expect(mockPush).not.toHaveBeenCalled();
    });

    it('should not redirect when loading', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: true, // Still loading
        error: null,
        _hasHydrated: true,
        fetchUser: jest.fn(),
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      renderHook(() => useAuth(true));

      expect(mockPush).not.toHaveBeenCalled();
    });

    it('should not redirect when not hydrated', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        _hasHydrated: false, // Not hydrated yet
        fetchUser: jest.fn(),
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      renderHook(() => useAuth(true));

      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  describe('Authentication Optional (requireAuth = false)', () => {
    it('should not redirect when not authenticated', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        _hasHydrated: true,
        fetchUser: jest.fn(),
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      renderHook(() => useAuth(false));

      expect(mockPush).not.toHaveBeenCalled();
    });

    it('should still fetch user data when authenticated but no user', async () => {
      const mockFetchUser = jest.fn().mockResolvedValue(mockUser);
      
      mockUseAuthStore.mockReturnValue({
        user: null, // No user data
        isAuthenticated: true, // But authenticated
        isLoading: false,
        error: null,
        _hasHydrated: true,
        fetchUser: mockFetchUser,
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      renderHook(() => useAuth(false));

      expect(mockFetchUser).toHaveBeenCalled();
      expect(mockPush).not.toHaveBeenCalled(); // Should not redirect on fetch failure
    });
  });

  describe('User Data Fetching', () => {
    it('should fetch user when authenticated but no user data', async () => {
      const mockFetchUser = jest.fn().mockResolvedValue(mockUser);
      
      mockUseAuthStore.mockReturnValue({
        user: null, // No user data
        isAuthenticated: true, // But authenticated
        isLoading: false,
        error: null,
        _hasHydrated: true,
        fetchUser: mockFetchUser,
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      renderHook(() => useAuth(true));

      expect(mockFetchUser).toHaveBeenCalled();
    });

    it('should redirect on fetch user failure when auth required', async () => {
      const mockFetchUser = jest.fn().mockRejectedValue(new Error('Unauthorized'));
      
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        _hasHydrated: true,
        fetchUser: mockFetchUser,
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      renderHook(() => useAuth(true));

      // Wait for the async operation
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(mockPush).toHaveBeenCalledWith('/login');
    });

    it('should not redirect on fetch user failure when auth optional', async () => {
      const mockFetchUser = jest.fn().mockRejectedValue(new Error('Unauthorized'));
      
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        _hasHydrated: true,
        fetchUser: mockFetchUser,
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      renderHook(() => useAuth(false));

      // Wait for the async operation
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(mockPush).not.toHaveBeenCalled();
    });

    it('should not fetch user when already loading', () => {
      const mockFetchUser = jest.fn();
      
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: true,
        isLoading: true, // Already loading
        error: null,
        _hasHydrated: true,
        fetchUser: mockFetchUser,
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      renderHook(() => useAuth(true));

      expect(mockFetchUser).not.toHaveBeenCalled();
    });

    it('should not fetch user when user already exists', () => {
      const mockFetchUser = jest.fn();
      
      mockUseAuthStore.mockReturnValue({
        user: mockUser, // User already exists
        isAuthenticated: true,
        isLoading: false,
        error: null,
        _hasHydrated: true,
        fetchUser: mockFetchUser,
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      renderHook(() => useAuth(true));

      expect(mockFetchUser).not.toHaveBeenCalled();
    });
  });

  describe('Hook Variants', () => {
    it('useRequireAuth should require authentication', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        _hasHydrated: true,
        fetchUser: jest.fn(),
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      renderHook(() => useRequireAuth());

      expect(mockPush).toHaveBeenCalledWith('/login');
    });

    it('useOptionalAuth should not require authentication', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        _hasHydrated: true,
        fetchUser: jest.fn(),
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      renderHook(() => useOptionalAuth());

      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  describe('State Changes', () => {
    it('should react to authentication state changes', () => {
      const mockFetchUser = jest.fn();
      
      // Start with unauthenticated state
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        _hasHydrated: true,
        fetchUser: mockFetchUser,
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      const { rerender } = renderHook(() => useAuth(true));

      expect(mockPush).toHaveBeenCalledWith('/login');
      mockPush.mockClear();

      // Change to authenticated state
      mockUseAuthStore.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        _hasHydrated: true,
        fetchUser: mockFetchUser,
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      rerender();

      expect(mockPush).not.toHaveBeenCalled();
    });

    it('should react to hydration state changes', () => {
      const mockFetchUser = jest.fn();
      
      // Start with not hydrated
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        _hasHydrated: false, // Not hydrated
        fetchUser: mockFetchUser,
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      const { result, rerender } = renderHook(() => useAuth(true));

      expect(result.current.isLoading).toBe(true);
      expect(mockPush).not.toHaveBeenCalled();

      // Change to hydrated
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        _hasHydrated: true, // Now hydrated
        fetchUser: mockFetchUser,
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      rerender();

      expect(result.current.isLoading).toBe(false);
      expect(mockPush).toHaveBeenCalledWith('/login');
    });
  });

  describe('Edge Cases', () => {
    it('should handle undefined user gracefully', () => {
      mockUseAuthStore.mockReturnValue({
        user: undefined as any,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        _hasHydrated: true,
        fetchUser: jest.fn(),
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      const { result } = renderHook(() => useAuth(false));

      expect(result.current.user).toBeUndefined();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should handle store errors gracefully', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: 'Some error',
        _hasHydrated: true,
        fetchUser: jest.fn(),
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        clearError: jest.fn(),
        updateUser: jest.fn(),
        checkAuth: jest.fn(),
        setHasHydrated: jest.fn(),
        setAuth: jest.fn(),
      });

      const { result } = renderHook(() => useAuth(false));

      expect(result.current.isAuthenticated).toBe(false);
      // Hook should still work despite error in store
    });
  });
});