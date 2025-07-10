import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import apiClient from "@/lib/api-client";
import { User, LoginCredentials, RegisterData } from "@/types";

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
          await get().fetchUser();
          set({ isAuthenticated: true, isLoading: false });
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
          // Clear cookies
          if (typeof window !== "undefined") {
            document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
            document.cookie = "refresh_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
          }
          
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
        // Save tokens to localStorage and cookies
        if (typeof window !== "undefined") {
          localStorage.setItem("access_token", tokens.access);
          localStorage.setItem("refresh_token", tokens.refresh);
          
          // Also set cookies for SSR middleware
          document.cookie = `access_token=${tokens.access}; path=/; max-age=3600`;
          document.cookie = `refresh_token=${tokens.refresh}; path=/; max-age=604800`;
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