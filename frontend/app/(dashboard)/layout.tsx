'use client';

import { useAuthStore } from '@/store/auth-store';
import { useRouter, usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { MainLayout } from '@/components/layouts/main-layout';
import { subscriptionService } from '@/services/subscription.service';
import { startStripeCheckout } from '@/utils/checkout';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading, user, fetchUser, hasHydrated } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();
  const [checkingSubscription, setCheckingSubscription] = useState(true);
  const [hasSubscription, setHasSubscription] = useState(false);

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

  // Check subscription status after authentication
  useEffect(() => {
    if (!hasHydrated || !isAuthenticated || !user) {
      return;
    }

    // Paths that don't require subscription check
    const exemptPaths = ['/settings'];
    const isExempt = exemptPaths.some(path => pathname?.startsWith(path));

    if (isExempt) {
      setHasSubscription(true);
      setCheckingSubscription(false);
      return;
    }

    // Check subscription
    subscriptionService.getStatus()
      .then(async (status) => {
        if (status.status === 'trialing' || status.status === 'active') {
          setHasSubscription(true);
        } else if (status.status === 'none') {
          await startStripeCheckout();
        } else {
          router.push('/subscription/expired');
        }
      })
      .catch(async (error) => {
        console.error('Error checking subscription:', error);
        // Se der erro na verificação, inicia checkout direto
        await startStripeCheckout();
      })
      .finally(() => {
        setCheckingSubscription(false);
      });
  }, [hasHydrated, isAuthenticated, user, pathname, router]);

  // Show loading while hydrating or checking authentication
  if (!hasHydrated || isLoading || checkingSubscription) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>{checkingSubscription ? 'Verificando assinatura...' : 'Carregando...'}</p>
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

  // Block access if no subscription
  if (!hasSubscription) {
    return null;
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