import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { useAuthStore } from '@/store/auth-store';
import { subscriptionService, SubscriptionStatus } from '@/services/subscription.service';

export function useSubscriptionCheck() {
  const router = useRouter();
  const { user } = useAuthStore();
  
  const { data, isLoading, error } = useQuery<SubscriptionStatus>({
    queryKey: ['subscription-status'],
    queryFn: () => subscriptionService.getSubscriptionStatus(),
    enabled: !!user,
    refetchInterval: 5 * 60 * 1000, // Check every 5 minutes
    staleTime: 4 * 60 * 1000, // Consider data stale after 4 minutes
    retry: 1, // Only retry once on failure
  });
  
  useEffect(() => {
    if (data && !isLoading) {
      // If trial expired and no payment method
      if (data.subscription_status === 'expired' && !data.has_payment_method) {
        // Only show toast once per session
        const toastShown = sessionStorage.getItem('trial_expired_toast');
        if (!toastShown) {
          toast.error('Seu período de teste expirou. Configure o pagamento para continuar.');
          sessionStorage.setItem('trial_expired_toast', 'true');
        }
        
        // Redirect to upgrade page if on restricted page
        const currentPath = window.location.pathname;
        const allowedPaths = ['/dashboard/subscription', '/dashboard/billing', '/settings'];
        const isAllowedPath = allowedPaths.some(path => currentPath.startsWith(path));
        
        if (!isAllowedPath) {
          router.push('/dashboard/subscription/upgrade');
        }
      }
      
      // Warning when trial is ending soon
      if (data.subscription_status === 'trial' && data.trial_days_left <= 3 && data.trial_days_left > 0 && !data.has_payment_method) {
        // Show warning once per day
        const lastWarning = localStorage.getItem('trial_warning_date');
        const today = new Date().toDateString();
        
        if (lastWarning !== today) {
          const message = data.trial_days_left === 1 
            ? 'Seu trial expira amanhã! Configure o pagamento para não perder acesso.'
            : `Seu trial expira em ${data.trial_days_left} dias. Configure o pagamento.`;
          
          toast.warning(message, {
            duration: 10000, // Show for 10 seconds
            action: {
              label: 'Configurar',
              onClick: () => router.push('/dashboard/subscription/upgrade'),
            },
          });
          
          localStorage.setItem('trial_warning_date', today);
        }
      }
    }
  }, [data, router, isLoading]);
  
  return {
    subscriptionStatus: data,
    isLoading,
    error,
    isTrialExpiring: data ? data.trial_days_left <= 7 && data.subscription_status === 'trial' : false,
    isTrialExpired: data ? data.subscription_status === 'expired' : false,
    needsPaymentSetup: data ? data.requires_payment_setup : false,
  };
}