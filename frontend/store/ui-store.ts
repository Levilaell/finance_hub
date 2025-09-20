import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

interface UIState {
  // Theme (currently unused - theme-switcher component uses its own state)
  theme: "light" | "dark" | "system";
  setTheme: (theme: "light" | "dark" | "system") => void;
  _hasHydrated: boolean;
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
      },

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
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);