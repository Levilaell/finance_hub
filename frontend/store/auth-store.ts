import { create } from "zustand";
import { persist } from "zustand/middleware";
import apiClient from "@/lib/api-client";
import { User } from "@/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  setAuth: (user: User, tokens: { access: string; refresh: string }) => void;
  login: (email: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => Promise<void>;
  fetchUser: () => Promise<void>;
  updateUser: (user: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,

      setAuth: (user, tokens) => {
        // Tokens are already stored by apiClient
        set({
          user,
          isAuthenticated: true,
          isLoading: false,
        });
      },

      login: async (email: string, password: string) => {
        set({ isLoading: true });
        
        try {
          const response = await apiClient.login(email, password);
          
          // Fix: Handle nested user object
          const userData = response.user?.user || response.user;
          
          set({
            user: userData,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (data: any) => {
        set({ isLoading: true });
        
        try {
          const response = await apiClient.register(data);
          
          // Fix: Handle nested user object
          const userData = response.user?.user || response.user;
          
          set({
            user: userData,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: async () => {
        set({ isLoading: true });
        
        try {
          await apiClient.logout();
        } catch (error) {
          console.warn('Logout API call failed:', error);
        } finally {
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
        } catch (error) {
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
    }),
    {
      name: "auth-storage",
      // Only persist essential data
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);