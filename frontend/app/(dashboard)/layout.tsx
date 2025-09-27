'use client';

import { useAuthStore } from '@/store/auth-store';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { MainLayout } from '@/components/layouts/main-layout';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading, user, fetchUser, hasHydrated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    // Wait for Zustand to hydrate from localStorage
    if (!hasHydrated) {
      return;
    }

    // Check if user is authenticated
    const token = localStorage.getItem('access_token');

    if (!token) {
      // No token, redirect to login
      router.push('/login');
      return;
    }

    // Only fetch user if we have a token but no user data after hydration
    if (token && !user && !isLoading) {
      fetchUser().catch(() => {
        // If fetch fails, redirect to login
        router.push('/login');
      });
    }
  }, [hasHydrated, user, fetchUser, router, isLoading]);

  // Show loading while hydrating or checking authentication
  if (!hasHydrated || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Carregando...</p>
        </div>
      </div>
    );
  }

  // Show loading while user data is being fetched
  if (!user && !isLoading && hasHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Verificando autenticação...</p>
        </div>
      </div>
    );
  }

  // If we have user data, show the protected content
  if (isAuthenticated && user) {
    return (
      <MainLayout>
        <div className="min-h-screen">
          {children}
        </div>
      </MainLayout>
    );
  }

  // Fallback - redirect to login
  router.push('/login');
  return null;
}