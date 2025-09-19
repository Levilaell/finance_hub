import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth-store";

export function useAuth(requireAuth: boolean = true) {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, fetchUser, _hasHydrated } = useAuthStore();

  useEffect(() => {
    // Only perform auth checks after store has hydrated to prevent SSR mismatches
    if (!_hasHydrated) return;

    // If we have a stored auth state but no user data, fetch it
    if (isAuthenticated && !user && !isLoading) {
      fetchUser().catch(() => {
        // If fetching user fails, user is not authenticated
        if (requireAuth) {
          router.push("/login");
        }
      });
    }

    // If auth is required and user is not authenticated, redirect to login
    if (!isAuthenticated && !isLoading && requireAuth) {
      router.push("/login");
    }
  }, [isAuthenticated, user, isLoading, requireAuth, router, fetchUser, _hasHydrated]);

  return {
    user,
    isAuthenticated,
    isLoading: isLoading || !_hasHydrated, // Show loading until hydrated
  };
}