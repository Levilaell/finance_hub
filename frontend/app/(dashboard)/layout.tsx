'use client';

import { useAuthStore } from '@/store/auth-store';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { MainLayout } from '@/components/layouts/main-layout';
import { PaymentSetupBanner } from '@/components/payment/payment-setup-banner';
import { EmailVerificationBanner } from '@/components/email-verification-banner';
import { useSubscriptionCheck } from '@/hooks/use-subscription-check';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading, _hasHydrated, user } = useAuthStore();
  const router = useRouter();
  
  // Use subscription check hook - but only when authenticated
  const { subscriptionStatus, isTrialExpired } = useSubscriptionCheck();


  useEffect(() => {
    if (_hasHydrated && !isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, _hasHydrated, router]);

  // Handle trial expiration redirect
  useEffect(() => {
    if (isAuthenticated && isTrialExpired) {
      // Check if user is on allowed pages
      const currentPath = window.location.pathname;
      const allowedPaths = [
        '/dashboard/subscription',
        '/dashboard/billing',
        '/dashboard/settings',
        '/settings'
      ];
      
      const isOnAllowedPath = allowedPaths.some(path => 
        currentPath.startsWith(path)
      );
      
      if (!isOnAllowedPath) {
        router.push('/dashboard/subscription/upgrade');
      }
    }
  }, [isAuthenticated, isTrialExpired, router]);

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
    return null;
  }

  return (
    <MainLayout>
      <div className="min-h-screen">
        {/* Email Verification Banner */}
        {isAuthenticated && user && <EmailVerificationBanner />}
        
        {/* Payment Setup Banner - Will only show when needed */}
        {isAuthenticated && user && <PaymentSetupBanner />}
        
        {/* Main content */}
        {children}
      </div>
    </MainLayout>
  );
}