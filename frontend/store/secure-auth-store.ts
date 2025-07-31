import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import secureApiClient from "@/lib/secure-api-client";
import { User, LoginCredentials, RegisterData } from "@/types";

interface SecureAuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  _hasHydrated: boolean;
  
  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  fetchUser: () => Promise<void>;
  clearError: () => void;
  updateUser: (user: Partial<User>) => void;
  checkAuth: () => Promise<void>;
  setHasHydrated: (state: boolean) => void;
  handleAuthError: () => void;
  handleTokenRefresh: (user: User) => void;
}

export const useSecureAuthStore = create<SecureAuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      _hasHydrated: false,

      login: async (credentials) => {
        set({ isLoading: true, error: null });
        try {
          const response = await secureApiClient.login(credentials.email, credentials.password);
          
          // Handle 2FA requirement
          if (response.requires_2fa) {
            set({ isLoading: false });
            return; // Let component handle 2FA flow
          }
          
          // Successful login - user data and tokens are handled by httpOnly cookies
          set({ 
            user: response.user, 
            isAuthenticated: true, 
            isLoading: false,
            error: null 
          });
          
        } catch (error: any) {
          set({
            error: error.response?.data?.error || 
                   error.response?.data?.detail || 
                   "Login failed",
            isLoading: false,
            isAuthenticated: false,
            user: null
          });
          throw error;
        }
      },

      register: async (data) => {
        set({ isLoading: true, error: null });
        try {
          const response = await secureApiClient.register(data);
          
          // Registration automatically logs user in with secure cookies
          set({ 
            user: response.user, 
            isAuthenticated: true, 
            isLoading: false,
            error: null 
          });
          
        } catch (error: any) {
          set({
            error: error.response?.data?.error || 
                   error.response?.data?.detail || 
                   "Registration failed",
            isLoading: false,
            isAuthenticated: false,
            user: null
          });
          throw error;
        }
      },

      logout: async () => {
        set({ isLoading: true });
        try {
          await secureApiClient.logout();
        } finally {
          // Clear local state - cookies are cleared by server
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },

      fetchUser: async () => {
        set({ isLoading: true });
        try {
          const user = await secureApiClient.get<User>("/api/auth/profile/");
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
          
          // Dispatch subscription update event
          if (typeof window !== 'undefined') {
            const event = new CustomEvent('subscription-updated', { detail: { user } });
            window.dispatchEvent(event);
          }
        } catch (error) {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          });
          throw error;
        }
      },

      checkAuth: async () => {
        const { isAuthenticated, user } = get();
        if (isAuthenticated && !user) {
          try {
            await get().fetchUser();
          } catch (error) {
            // Silently handle auth check errors
            set({ isAuthenticated: false, user: null });
          }
        }
      },

      clearError: () => set({ error: null }),

      updateUser: (userData) => {
        const currentUser = get().user;
        if (currentUser) {
          set({ user: { ...currentUser, ...userData } });
        }
      },

      setHasHydrated: (state) => {
        set({ _hasHydrated: state });
      },

      handleAuthError: () => {
        // Called when authentication fails (e.g., invalid/expired tokens)
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: 'Session expired. Please login again.'
        });
      },

      handleTokenRefresh: (user) => {
        // Called when tokens are successfully refreshed
        set({
          user,
          isAuthenticated: true,
          error: null
        });
      },
    }),
    {
      name: "secure-auth-storage",
      storage: createJSONStorage(() => 
        typeof window !== "undefined" ? localStorage : {
          getItem: () => null,
          setItem: () => {},
          removeItem: () => {},
        }
      ),
      // Only persist user data and auth state - no tokens
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
        
        // Set up event listeners for auth events
        if (typeof window !== 'undefined') {
          // Handle token refresh events
          const handleTokenRefresh = (event: CustomEvent) => {
            if (event.detail?.user) {
              state?.handleTokenRefresh(event.detail.user);
            }
          };
          
          // Handle auth error events
          const handleAuthError = () => {
            state?.handleAuthError();
          };
          
          // Handle logout events
          const handleLogout = () => {
            state?.logout();
          };
          
          window.addEventListener('auth-token-refreshed', handleTokenRefresh as EventListener);
          window.addEventListener('auth-error', handleAuthError);
          window.addEventListener('auth-logout', handleLogout);
          
          // Cleanup function (though this won't be called in practice)
          return () => {
            window.removeEventListener('auth-token-refreshed', handleTokenRefresh as EventListener);
            window.removeEventListener('auth-error', handleAuthError);
            window.removeEventListener('auth-logout', handleLogout);
          };
        }
      },
    }
  )
);

// Enhanced auth hook with security features
export function useSecureAuth(requireAuth: boolean = true) {
  const { user, isAuthenticated, isLoading, fetchUser, _hasHydrated, handleAuthError } = useSecureAuthStore();

  // Auto-check authentication on mount
  React.useEffect(() => {
    if (!_hasHydrated) return;

    // If we think we're authenticated but have no user data, fetch it
    if (isAuthenticated && !user && !isLoading) {
      fetchUser().catch(() => {
        if (requireAuth) {
          handleAuthError();
        }
      });
    }

    // If auth is required and user is not authenticated, they'll be redirected by API client
    if (!isAuthenticated && !isLoading && requireAuth) {
      // The middleware/API client will handle the redirect
      console.log('Authentication required but user not authenticated');
    }
  }, [isAuthenticated, user, isLoading, requireAuth, fetchUser, _hasHydrated, handleAuthError]);

  return {
    user,
    isAuthenticated,
    isLoading: isLoading || !_hasHydrated,
  };
}