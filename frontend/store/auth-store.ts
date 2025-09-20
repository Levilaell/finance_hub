import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import apiClient from "@/lib/api-client";
import { User } from "@/types";
import { authStorage } from "@/lib/auth-storage";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  _hasHydrated: boolean;

  // Actions
  setAuth: (user: User, tokens: { access: string; refresh: string }) => void;
  logout: () => Promise<void>;
  fetchUser: () => Promise<void>;
  updateUser: (user: Partial<User>) => void;
  checkAuth: () => Promise<void>;
  setHasHydrated: (state: boolean) => void;
  validateAndSync: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      _hasHydrated: false,

      setAuth: (user, tokens) => {
        // Store tokens first
        if (tokens) {
          authStorage.setTokens(tokens);
        }

        // Then update state
        set({
          user,
          isAuthenticated: true,
          isLoading: false,
        });
      },

      logout: async () => {
        set({ isLoading: true });
        
        try {
          await apiClient.logout();
        } catch (error) {
          console.warn('Logout API call failed:', error);
        } finally {
          // Always clear tokens and state
          authStorage.clearTokens();
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      },

      fetchUser: async () => {
        set({ isLoading: true });
        
        try {
          const user = await apiClient.get<User>("/api/auth/profile/");
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
          });

          // Trigger subscription update event
          if (typeof window !== 'undefined') {
            const event = new CustomEvent('subscription-updated', { detail: { user } });
            window.dispatchEvent(event);
          }
        } catch (error) {
          // If fetch fails, clear everything
          authStorage.clearTokens();
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          });
          throw error;
        }
      },

      updateUser: (userData) => {
        const currentUser = get().user;
        if (currentUser) {
          set({ user: { ...currentUser, ...userData } });
        }
      },

      checkAuth: async () => {
        const { isAuthenticated, user, validateAndSync } = get();
        
        // First validate tokens
        if (!validateAndSync()) {
          return;
        }
        
        // If authenticated but no user data, fetch it
        if (isAuthenticated && !user) {
          try {
            await get().fetchUser();
          } catch (error) {
            console.warn('Failed to fetch user during auth check');
          }
        }
      },

      validateAndSync: () => {
        const { isAuthenticated } = get();
        
        // Check if we have valid tokens
        const hasValidTokens = authStorage.hasTokens() && 
                              authStorage.validateTokens() && 
                              !authStorage.isAccessTokenExpired();
        
        // Case 1: Store says authenticated but no valid tokens
        if (isAuthenticated && !hasValidTokens) {
          console.log('[Auth] Invalid tokens detected, clearing auth state');
          authStorage.clearTokens();
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          });
          return false;
        }
        
        // Case 2: Valid tokens but store says not authenticated
        if (!isAuthenticated && hasValidTokens) {
          console.log('[Auth] Valid tokens found, updating auth state');
          set({ isAuthenticated: true });
          // Don't set user here - let fetchUser handle it
          return true;
        }
        
        // Case 3: Both aligned
        return isAuthenticated && hasValidTokens;
      },

      setHasHydrated: (state) => {
        set({ _hasHydrated: state });
        
        // Validate and sync after hydration
        if (state) {
          // Use setTimeout to avoid hydration conflicts
          setTimeout(() => {
            const isValid = get().validateAndSync();
            
            // If we have valid tokens but no user, fetch user
            if (isValid && get().isAuthenticated && !get().user) {
              get().fetchUser().catch(() => {
                console.warn('Failed to fetch user after hydration');
              });
            }
          }, 0);
        }
      },
    }),
    {
      name: "auth-storage",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? localStorage : {
          getItem: () => null,
          setItem: () => {},
          removeItem: () => {},
        }
      ),
      // Only persist essential data
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);