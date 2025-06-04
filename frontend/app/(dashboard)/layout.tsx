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
  console.log('DashboardLayout rendered');
  const { isAuthenticated, isLoading, _hasHydrated } = useAuthStore();
  const router = useRouter();

  console.log('Auth state:', { isAuthenticated, isLoading, _hasHydrated });

  useEffect(() => {
    console.log('Auth effect:', { isAuthenticated, isLoading, _hasHydrated });
    if (_hasHydrated && !isLoading && !isAuthenticated) {
      console.log('Redirecting to login');
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, _hasHydrated, router]);

  if (!_hasHydrated || isLoading) {
    console.log('Showing loading');
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Carregando...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    console.log('Not authenticated, showing null');
    return null;
  }

  console.log('Rendering children');
  return <MainLayout>{children}</MainLayout>;
}