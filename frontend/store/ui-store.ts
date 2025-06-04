import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

interface UIState {
  // Theme
  theme: "light" | "dark" | "system";
  setTheme: (theme: "light" | "dark" | "system") => void;
  applyTheme: (theme: "light" | "dark" | "system") => void;
  _hasHydrated: boolean;

  // Sidebar
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;

  // Modals
  modals: Record<string, boolean>;
  openModal: (modalId: string) => void;
  closeModal: (modalId: string) => void;
  isModalOpen: (modalId: string) => boolean;

  // Loading states
  loadingStates: Record<string, boolean>;
  setLoading: (key: string, loading: boolean) => void;
  isLoading: (key: string) => boolean;

  // Notifications
  notificationCount: number;
  setNotificationCount: (count: number) => void;
  incrementNotificationCount: () => void;
  decrementNotificationCount: () => void;
  setHasHydrated: (state: boolean) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      // Theme
      theme: "system",
      _hasHydrated: false,
      
      setTheme: (theme) => {
        set({ theme });
        // Only apply theme after hydration to prevent mismatches
        if (get()._hasHydrated) {
          get().applyTheme(theme);
        }
      },

      applyTheme: (theme) => {
        if (typeof window === "undefined") return;
        
        const root = window.document.documentElement;
        root.classList.remove("light", "dark");
        
        if (theme === "system") {
          const systemTheme = window.matchMedia("(prefers-color-scheme: dark)")
            .matches
            ? "dark"
            : "light";
          root.classList.add(systemTheme);
        } else {
          root.classList.add(theme);
        }
      },

      // Sidebar
      sidebarCollapsed: false,
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

      // Modals
      modals: {},
      openModal: (modalId) =>
        set((state) => ({
          modals: { ...state.modals, [modalId]: true },
        })),
      closeModal: (modalId) =>
        set((state) => ({
          modals: { ...state.modals, [modalId]: false },
        })),
      isModalOpen: (modalId) => get().modals[modalId] || false,

      // Loading states
      loadingStates: {},
      setLoading: (key, loading) =>
        set((state) => ({
          loadingStates: { ...state.loadingStates, [key]: loading },
        })),
      isLoading: (key) => get().loadingStates[key] || false,

      // Notifications
      notificationCount: 0,
      setNotificationCount: (count) => set({ notificationCount: count }),
      incrementNotificationCount: () =>
        set((state) => ({ notificationCount: state.notificationCount + 1 })),
      decrementNotificationCount: () =>
        set((state) => ({
          notificationCount: Math.max(0, state.notificationCount - 1),
        })),

      setHasHydrated: (state) => {
        set({ _hasHydrated: state });
      },
    }),
    {
      name: "ui-storage",
      storage: createJSONStorage(() => 
        typeof window !== "undefined" ? localStorage : {
          getItem: () => null,
          setItem: () => {},
          removeItem: () => {},
        }
      ),
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
        // Apply theme after hydration
        if (state) {
          state.applyTheme(state.theme);
        }
      },
    }
  )
);