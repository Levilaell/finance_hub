import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { subscriptionService, SubscriptionStatus, CheckoutSessionRequest } from '@/services/unified-subscription.service';
import { toast } from '@/components/ui/use-toast';

export function useSubscription() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const { user, updateUser } = useAuthStore();

  // Get subscription status
  const { data: subscription, isLoading, error } = useQuery({
    queryKey: ['subscription-status'],
    queryFn: subscriptionService.getSubscriptionStatus,
    enabled: !!user,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  // Create checkout session
  const createCheckoutSession = useMutation({
    mutationFn: (data: CheckoutSessionRequest) => subscriptionService.createCheckoutSession(data),
    onSuccess: (data) => {
      // Redirect to Stripe checkout
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to create checkout session. Please try again.',
        variant: 'destructive',
      });
    },
  });

  // Validate payment
  const validatePayment = useMutation({
    mutationFn: (sessionId: string) => subscriptionService.validatePayment(sessionId),
    onSuccess: (data) => {
      if (data.status === 'success') {
        // Invalidate relevant queries
        queryClient.invalidateQueries({ queryKey: ['subscription-status'] });
        queryClient.invalidateQueries({ queryKey: ['user'] });
        
        // Update user data if subscription is active
        if (data.subscription && user) {
          updateUser({
            ...user,
            subscription_status: data.subscription.status,
            subscription_plan: data.subscription.plan.name,
          });
        }
        
        toast({
          title: 'Success',
          description: 'Your subscription has been activated!',
        });
      }
    },
  });

  // Cancel subscription
  const cancelSubscription = useMutation({
    mutationFn: subscriptionService.cancelSubscription,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['subscription-status'] });
      
      toast({
        title: 'Subscription Cancelled',
        description: data.message,
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to cancel subscription. Please try again.',
        variant: 'destructive',
      });
    },
  });

  // Helper functions
  const isActive = subscription?.subscription_status === 'active';
  const isTrial = subscription?.subscription_status === 'trial';
  const trialDaysRemaining = subscription?.trial_days_left ?? 0;
  
  const canUseFeature = (feature: string): boolean => {
    if (!subscription?.plan) return false;
    return subscriptionService.canUseFeature(subscription.plan, feature);
  };

  const shouldShowUpgradePrompt = (): boolean => {
    // Show prompt if trial is ending soon
    if (isTrial && trialDaysRemaining <= 3) return true;
    
    // Show prompt if payment setup is required
    if (subscription?.requires_payment_setup) return true;
    
    return false;
  };

  return {
    subscription,
    isLoading,
    error,
    isActive,
    isTrial,
    trialDaysRemaining,
    canUseFeature,
    shouldShowUpgradePrompt,
    createCheckoutSession,
    validatePayment,
    cancelSubscription,
  };
}