import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import apiClient from "@/lib/api-client";
import { User, LoginCredentials, RegisterData } from "@/types";
import { authStorage } from "@/lib/auth-storage";

interface AuthState {
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
  setAuth: (user: User, tokens: { access: string; refresh: string }) => void;
}

export const useAuthStore = create<AuthState>()(
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
          const response = await apiClient.login(credentials.email, credentials.password);
          // Use setAuth to properly set cookies and tokens
          if (response.tokens && response.user) {
            get().setAuth(response.user, response.tokens);
          } else {
            // If user is not in response, fetch it
            await get().fetchUser();
            set({ isAuthenticated: true, isLoading: false });
          }
        } catch (error: any) {
          set({
            error: error.response?.data?.detail || "Login failed",
            isLoading: false,
          });
          throw error;
        }
      },

      register: async (data) => {
        set({ isLoading: true, error: null });
        try {
          await apiClient.register(data);
          // After registration, log the user in
          await get().login({ email: data.email, password: data.password });
        } catch (error: any) {
          set({
            error: error.response?.data?.detail || "Registration failed",
            isLoading: false,
          });
          throw error;
        }
      },

      logout: async () => {
        set({ isLoading: true });
        try {
          await apiClient.logout();
        } finally {
          // Clear tokens using appropriate method
          authStorage.clearTokens();
          
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
          const user = await apiClient.get<User>("/api/auth/profile/");
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
          
          // Force update of all related data after subscription change
          if (typeof window !== 'undefined') {
            // Invalidate any cached data
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

      setAuth: (user, tokens) => {
        // Store tokens using appropriate method (localStorage for mobile Safari, cookies for others)
        if (tokens) {
          authStorage.setTokens(tokens);
        }
        
        set({
          user,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
      },

      setHasHydrated: (state) => {
        set({
          _hasHydrated: state,
        });
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