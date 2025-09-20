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
  const { isAuthenticated, isLoading, _hasHydrated } = useAuthStore();
  const router = useRouter();
  


  useEffect(() => {
    if (_hasHydrated && !isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, _hasHydrated, router]);


  if (!_hasHydrated || isLoading) {
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
    // Show loading spinner while redirecting
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Redirecionando...</p>
        </div>
      </div>
    );
  }

  return (
    <MainLayout>
      <div className="min-h-screen">
        {/* Main content */}
        {children}
      </div>
    </MainLayout>
  );
}