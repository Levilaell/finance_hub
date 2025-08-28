'use client';

import { useAuthStore } from '@/store/auth-store';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { MainLayout } from '@/components/layouts/main-layout';
import { PaymentSetupBanner } from '@/components/payment/payment-setup-banner';
import { useSubscriptionCheck } from '@/hooks/use-subscription-check';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading, _hasHydrated, user } = useAuthStore();
  const router = useRouter();
  
  // Use subscription check hook - but only when authenticated and user exists
  const { subscriptionStatus, isTrialExpired, isLoading: isLoadingSubscription } = useSubscriptionCheck();


  useEffect(() => {
    if (_hasHydrated && !isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, _hasHydrated, router]);

  // Handle subscription blocking - more strict approach
  useEffect(() => {
    // Only run after component has mounted to avoid hydration issues
    if (typeof window !== 'undefined' && isAuthenticated && subscriptionStatus && !isLoadingSubscription) {
      const currentPath = window.location.pathname;
      
      // Check if subscription is blocked
      const isBlocked = subscriptionStatus.subscription_status === 'expired' ||
                       subscriptionStatus.subscription_status === 'cancelled' ||
                       subscriptionStatus.subscription_status === 'suspended' ||
                       (subscriptionStatus.subscription_status === 'trial' && subscriptionStatus.trial_days_left <= 0);
      
      if (isBlocked) {
        // Only allow access to subscription/billing pages and blocked page
        const allowedPaths = [
          '/dashboard/subscription',
          '/dashboard/subscription-blocked',
          '/settings'
        ];
        
        const isOnAllowedPath = allowedPaths.some(path => 
          currentPath.startsWith(path)
        );
        
        // If not on allowed path, redirect to blocked page
        if (!isOnAllowedPath) {
          router.push('/dashboard/subscription-blocked');
        }
      }
    }
  }, [isAuthenticated, subscriptionStatus, isLoadingSubscription, router]);

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
        {/* Payment Setup Banner - Will only show when needed */}
        {isAuthenticated && user && <PaymentSetupBanner />}
        
        {/* Main content */}
        {children}
      </div>
    </MainLayout>
  );
}