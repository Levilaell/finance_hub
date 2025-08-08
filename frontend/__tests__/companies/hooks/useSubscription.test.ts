/**
 * Tests for useSubscription hook
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useSubscription } from '@/hooks/useSubscription';
import { subscriptionService } from '@/services/unified-subscription.service';
import { useAuthStore } from '@/store/auth-store';
import {
  mockSubscriptionStatus,
  mockActiveSubscriptionStatus,
  subscriptionScenarios,
  createQueryClient,
} from '../test-utils';

// Mock dependencies
jest.mock('@/services/unified-subscription.service');
jest.mock('@/store/auth-store');
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    prefetch: jest.fn(),
  }),
}));

jest.mock('@/components/ui/use-toast', () => ({
  toast: jest.fn(),
}));

const mockSubscriptionService = subscriptionService as jest.Mocked<typeof subscriptionService>;
const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;

describe('useSubscription', () => {
  let queryClient: QueryClient;

  const createWrapper = (client: QueryClient) => {
    return ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>
        {children}
      </QueryClientProvider>
    );
  };

  beforeEach(() => {
    queryClient = createQueryClient();
    jest.clearAllMocks();
    
    // Mock auth store
    mockUseAuthStore.mockReturnValue({
      user: { id: 'user-1', email: 'test@example.com', name: 'Test User' },
      isAuthenticated: true,
      updateUser: jest.fn(),
    } as any);
  });

  describe('Basic Functionality', () => {
    it('should fetch subscription status successfully', async () => {
      const mockStatus = mockSubscriptionStatus();
      mockSubscriptionService.getSubscriptionStatus.mockResolvedValue(mockStatus);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.subscription).toEqual(mockStatus);
        expect(result.current.isLoading).toBe(false);
        expect(result.current.error).toBeNull();
      });

      expect(mockSubscriptionService.getSubscriptionStatus).toHaveBeenCalledTimes(1);
    });

    it('should handle loading state', () => {
      mockSubscriptionService.getSubscriptionStatus.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.subscription).toBeUndefined();
    });

    it('should handle error state', async () => {
      const error = new Error('Failed to fetch subscription');
      mockSubscriptionService.getSubscriptionStatus.mockRejectedValue(error);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
        expect(result.current.isLoading).toBe(false);
        expect(result.current.subscription).toBeUndefined();
      });
    });

    it('should not fetch when user is not authenticated', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
        updateUser: jest.fn(),
      } as any);

      renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      expect(mockSubscriptionService.getSubscriptionStatus).not.toHaveBeenCalled();
    });
  });

  describe('Helper Properties', () => {
    it('should correctly identify active subscription', async () => {
      const activeStatus = mockActiveSubscriptionStatus();
      mockSubscriptionService.getSubscriptionStatus.mockResolvedValue(activeStatus);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isActive).toBe(true);
        expect(result.current.isTrial).toBe(false);
      });
    });

    it('should correctly identify trial subscription', async () => {
      const trialStatus = mockSubscriptionStatus({ subscription_status: 'trial' });
      mockSubscriptionService.getSubscriptionStatus.mockResolvedValue(trialStatus);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isActive).toBe(false);
        expect(result.current.isTrial).toBe(true);
        expect(result.current.trialDaysRemaining).toBe(14);
      });
    });

    it('should handle cancelled subscription', async () => {
      const cancelledStatus = mockSubscriptionStatus({ subscription_status: 'cancelled' });
      mockSubscriptionService.getSubscriptionStatus.mockResolvedValue(cancelledStatus);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isActive).toBe(false);
        expect(result.current.isTrial).toBe(false);
      });
    });

    it('should handle expired subscription', async () => {
      const expiredStatus = mockSubscriptionStatus({ 
        subscription_status: 'expired',
        trial_days_left: 0 
      });
      mockSubscriptionService.getSubscriptionStatus.mockResolvedValue(expiredStatus);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isActive).toBe(false);
        expect(result.current.isTrial).toBe(false);
        expect(result.current.trialDaysRemaining).toBe(0);
      });
    });
  });

  describe('Feature Access', () => {
    it('should check feature access correctly', async () => {
      const statusWithPlan = mockSubscriptionStatus({
        plan: {
          ...mockSubscriptionStatus().plan!,
          has_ai_insights: true,
          has_advanced_reports: false,
        },
      });
      mockSubscriptionService.getSubscriptionStatus.mockResolvedValue(statusWithPlan);
      mockSubscriptionService.canUseFeature.mockImplementation((plan, feature) => {
        if (feature === 'ai_insights') return true;
        if (feature === 'advanced_reports') return false;
        return false;
      });

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.canUseFeature('ai_insights')).toBe(true);
        expect(result.current.canUseFeature('advanced_reports')).toBe(false);
        expect(result.current.canUseFeature('unknown_feature')).toBe(false);
      });
    });

    it('should return false for feature access when no plan', async () => {
      const statusNoPlan = mockSubscriptionStatus({ plan: null });
      mockSubscriptionService.getSubscriptionStatus.mockResolvedValue(statusNoPlan);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.canUseFeature('ai_insights')).toBe(false);
        expect(result.current.canUseFeature('advanced_reports')).toBe(false);
      });
    });
  });

  describe('Upgrade Prompt Logic', () => {
    it('should show upgrade prompt for trial ending soon', async () => {
      const expiringSoon = subscriptionScenarios.expiringSoon;
      mockSubscriptionService.getSubscriptionStatus.mockResolvedValue(expiringSoon);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.shouldShowUpgradePrompt()).toBe(true);
      });
    });

    it('should show upgrade prompt when payment setup required', async () => {
      const needsPayment = mockSubscriptionStatus({ requires_payment_setup: true });
      mockSubscriptionService.getSubscriptionStatus.mockResolvedValue(needsPayment);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.shouldShowUpgradePrompt()).toBe(true);
      });
    });

    it('should not show upgrade prompt for active subscription', async () => {
      const activeStatus = mockActiveSubscriptionStatus();
      mockSubscriptionService.getSubscriptionStatus.mockResolvedValue(activeStatus);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.shouldShowUpgradePrompt()).toBe(false);
      });
    });

    it('should not show upgrade prompt for early trial', async () => {
      const earlyTrial = mockSubscriptionStatus({ 
        trial_days_left: 10,
        requires_payment_setup: false 
      });
      mockSubscriptionService.getSubscriptionStatus.mockResolvedValue(earlyTrial);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.shouldShowUpgradePrompt()).toBe(false);
      });
    });
  });

  describe('Mutations', () => {
    it('should handle createCheckoutSession mutation', async () => {
      const mockCheckoutSession = { session_id: 'sess_123', checkout_url: 'https://checkout.stripe.com' };
      mockSubscriptionService.createCheckoutSession.mockResolvedValue(mockCheckoutSession);
      
      // Mock window.location
      delete (window as any).location;
      window.location = { href: '' } as any;

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      const checkoutData = {
        plan_id: 1,
        billing_period: 'monthly' as const,
        success_url: 'https://example.com/success',
        cancel_url: 'https://example.com/cancel',
      };

      await waitFor(() => {
        result.current.createCheckoutSession.mutate(checkoutData);
      });

      await waitFor(() => {
        expect(mockSubscriptionService.createCheckoutSession).toHaveBeenCalledWith(checkoutData);
      });
    });

    it('should handle validatePayment mutation', async () => {
      const mockValidation = { status: 'success' };
      mockSubscriptionService.validatePayment.mockResolvedValue(mockValidation);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        result.current.validatePayment.mutate('session_123');
      });

      await waitFor(() => {
        expect(mockSubscriptionService.validatePayment).toHaveBeenCalledWith('session_123');
      });
    });

    it('should handle cancelSubscription mutation', async () => {
      const mockCancellation = { status: 'cancelled', message: 'Subscription cancelled' };
      mockSubscriptionService.cancelSubscription.mockResolvedValue(mockCancellation);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        result.current.cancelSubscription.mutate();
      });

      await waitFor(() => {
        expect(mockSubscriptionService.cancelSubscription).toHaveBeenCalled();
      });
    });
  });

  describe('Query Invalidation', () => {
    it('should invalidate queries after successful payment validation', async () => {
      const mockValidation = { 
        status: 'success',
        subscription: {
          status: 'active',
          plan: { name: 'Premium' }
        }
      };
      mockSubscriptionService.validatePayment.mockResolvedValue(mockValidation);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      // Spy on query invalidation
      const invalidateQueriesSpy = jest.spyOn(queryClient, 'invalidateQueries');

      await waitFor(() => {
        result.current.validatePayment.mutate('session_123');
      });

      await waitFor(() => {
        expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['subscription-status'] });
        expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['user'] });
      });
    });

    it('should invalidate queries after successful cancellation', async () => {
      const mockCancellation = { status: 'cancelled', message: 'Cancelled' };
      mockSubscriptionService.cancelSubscription.mockResolvedValue(mockCancellation);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      const invalidateQueriesSpy = jest.spyOn(queryClient, 'invalidateQueries');

      await waitFor(() => {
        result.current.cancelSubscription.mutate();
      });

      await waitFor(() => {
        expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['subscription-status'] });
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      const networkError = new Error('Network error');
      mockSubscriptionService.getSubscriptionStatus.mockRejectedValue(networkError);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
        expect(result.current.subscription).toBeUndefined();
      });
    });

    it('should handle mutation errors', async () => {
      const mutationError = new Error('Payment failed');
      mockSubscriptionService.createCheckoutSession.mockRejectedValue(mutationError);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      const checkoutData = {
        plan_id: 1,
        billing_period: 'monthly' as const,
        success_url: 'https://example.com/success',
        cancel_url: 'https://example.com/cancel',
      };

      await waitFor(() => {
        result.current.createCheckoutSession.mutate(checkoutData);
      });

      await waitFor(() => {
        expect(result.current.createCheckoutSession.error).toBeTruthy();
      });
    });
  });

  describe('Caching and Stale Time', () => {
    it('should use correct stale time for caching', async () => {
      const mockStatus = mockSubscriptionStatus();
      mockSubscriptionService.getSubscriptionStatus.mockResolvedValue(mockStatus);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.subscription).toEqual(mockStatus);
      });

      // Clear mock calls
      mockSubscriptionService.getSubscriptionStatus.mockClear();

      // Render again - should use cached data within stale time
      const { result: result2 } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result2.current.subscription).toEqual(mockStatus);
      });

      // Should not make another API call due to caching
      expect(mockSubscriptionService.getSubscriptionStatus).not.toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    it('should handle undefined subscription data', async () => {
      mockSubscriptionService.getSubscriptionStatus.mockResolvedValue(undefined as any);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.subscription).toBeUndefined();
        expect(result.current.isActive).toBe(false);
        expect(result.current.isTrial).toBe(false);
        expect(result.current.trialDaysRemaining).toBe(0);
      });
    });

    it('should handle null trial_days_left', async () => {
      const statusNullDays = mockSubscriptionStatus({ trial_days_left: null as any });
      mockSubscriptionService.getSubscriptionStatus.mockResolvedValue(statusNullDays);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.trialDaysRemaining).toBe(0);
      });
    });

    it('should handle malformed subscription status', async () => {
      const malformedStatus = {
        subscription_status: 'unknown_status',
        plan: null,
        trial_days_left: -1,
      } as any;
      mockSubscriptionService.getSubscriptionStatus.mockResolvedValue(malformedStatus);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isActive).toBe(false);
        expect(result.current.isTrial).toBe(false);
        expect(result.current.canUseFeature('ai_insights')).toBe(false);
      });
    });
  });
});