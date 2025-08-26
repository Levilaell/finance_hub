import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { subscriptionService, SubscriptionStatus, CheckoutSessionRequest } from '@/services/unified-subscription.service';
import { toast } from 'sonner';

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
      toast.error('Failed to create checkout session. Please try again.');
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
        
        // Subscription data is already cached in the query
        // No need to update user data
        
        toast.success('Your subscription has been activated!');
      }
    },
    onError: (error: any) => {
      // Enhanced error handling for payment validation
      if (error?.response?.data?.code === 'COMPANY_MISMATCH') {
        toast.error(
          'Payment processed successfully, but there was an account issue. Please contact support.',
          {
            description: error.response.data.details?.support_message || 'We\'ll help you resolve this quickly.',
            duration: 10000, // Show longer for important message
          }
        );
      } else {
        toast.error('Payment validation failed. Please try again or contact support.');
      }
    },
  });

  // Cancel subscription
  const cancelSubscription = useMutation({
    mutationFn: subscriptionService.cancelSubscription,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['subscription-status'] });
      
      toast.success(data.message || 'Subscription cancelled successfully.');
    },
    onError: () => {
      toast.error('Failed to cancel subscription. Please try again.');
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