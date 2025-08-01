/**
 * Integration tests for companies system - Frontend + Backend interaction
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useSubscription } from '@/hooks/useSubscription';
import { useUsageLimits } from '@/hooks/useUsageLimits';
import { subscriptionService } from '@/services/unified-subscription.service';
import { apiClient } from '@/lib/api-client';
import {
  mockSubscriptionStatus,
  mockActiveSubscriptionStatus,
  mockUsageLimits,
  mockSubscriptionPlan,
  createQueryClient,
} from '../test-utils';

// Mock the API client for integration testing
jest.mock('@/lib/api-client');
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

// Mock auth store
jest.mock('@/store/auth-store', () => ({
  useAuthStore: () => ({
    user: { id: 'user-1', email: 'test@example.com', name: 'Test User' },
    isAuthenticated: true,
    updateUser: jest.fn(),
  }),
}));

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
  }),
}));

jest.mock('@/components/ui/use-toast', () => ({
  toast: jest.fn(),
}));

const createWrapper = (queryClient: QueryClient) => {
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('Companies System Integration', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = createQueryClient();
    jest.clearAllMocks();
  });

  describe('Complete User Journey - Trial to Active Subscription', () => {
    it('should handle complete subscription flow from trial to active', async () => {
      // 1. Initial trial state
      const trialStatus = mockSubscriptionStatus({
        subscription_status: 'trial',
        trial_days_left: 10,
        requires_payment_setup: true,
        has_payment_method: false,
      });
      
      const initialUsage = mockUsageLimits({
        transactions: { used: 50, limit: 100, percentage: 50 },
        bank_accounts: { used: 1, limit: 2, percentage: 50 },
        ai_requests: { used: 5, limit: 10, percentage: 50 },
      });

      mockApiClient.get
        .mockResolvedValueOnce(trialStatus) // subscription status
        .mockResolvedValueOnce(initialUsage); // usage limits

      // Render subscription hook
      const { result: subscriptionResult } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      // Render usage hook
      const { result: usageResult } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      // Wait for initial data to load
      await waitFor(() => {
        expect(subscriptionResult.current.subscription).toEqual(trialStatus);
        expect(usageResult.current.usageLimits).toEqual(initialUsage);
      });

      // Verify initial state
      expect(subscriptionResult.current.isTrial).toBe(true);
      expect(subscriptionResult.current.isActive).toBe(false);
      expect(subscriptionResult.current.trialDaysRemaining).toBe(10);
      expect(subscriptionResult.current.shouldShowUpgradePrompt()).toBe(true);

      // 2. User starts checkout process
      const checkoutData = {
        plan_id: 2,
        billing_period: 'monthly' as const,
        success_url: 'https://example.com/success',
        cancel_url: 'https://example.com/cancel',
      };

      const checkoutResponse = {
        session_id: 'sess_123456',
        checkout_url: 'https://checkout.stripe.com/sess_123456',
      };

      mockApiClient.post.mockResolvedValueOnce(checkoutResponse);

      // Mock window.location
      delete (window as any).location;
      window.location = { href: '' } as any;

      // Create checkout session
      subscriptionResult.current.createCheckoutSession.mutate(checkoutData);

      await waitFor(() => {
        expect(mockApiClient.post).toHaveBeenCalledWith('/api/payments/checkout/create/', checkoutData);
      });

      // 3. Simulate successful payment validation
      const validationResponse = {
        status: 'success',
        message: 'Payment successful',
        subscription: {
          status: 'active',
          plan: { name: 'Premium' }
        }
      };

      mockApiClient.post.mockResolvedValueOnce(validationResponse);

      // Validate payment
      subscriptionResult.current.validatePayment.mutate('sess_123456');

      await waitFor(() => {
        expect(mockApiClient.post).toHaveBeenCalledWith('/api/payments/checkout/validate/', {
          session_id: 'sess_123456'
        });
      });

      // 4. Verify updated subscription status after payment
      const activeStatus = mockActiveSubscriptionStatus();
      const updatedUsage = mockUsageLimits({
        transactions: { used: 50, limit: 2000, percentage: 2.5 }, // Upgraded limits
        bank_accounts: { used: 1, limit: 5, percentage: 20 },
        ai_requests: { used: 5, limit: 200, percentage: 2.5 },
      });

      mockApiClient.get
        .mockResolvedValueOnce(activeStatus)
        .mockResolvedValueOnce(updatedUsage);

      // Force refetch after payment
      queryClient.invalidateQueries({ queryKey: ['subscription-status'] });
      queryClient.invalidateQueries({ queryKey: ['usage-limits'] });

      await waitFor(() => {
        expect(subscriptionResult.current.isActive).toBe(true);
        expect(subscriptionResult.current.isTrial).toBe(false);
        expect(subscriptionResult.current.shouldShowUpgradePrompt()).toBe(false);
      });
    });
  });

  describe('Usage Tracking Integration', () => {
    it('should track usage changes across the system', async () => {
      const initialUsage = mockUsageLimits({
        transactions: { used: 100, limit: 500, percentage: 20 },
        bank_accounts: { used: 1, limit: 2, percentage: 50 },
        ai_requests: { used: 10, limit: 50, percentage: 20 },
      });

      mockApiClient.get.mockResolvedValue(initialUsage);

      const { result, rerender } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.usageLimits).toEqual(initialUsage);
        expect(result.current.shouldShowUsageWarning()).toBe(false);
      });

      // Simulate usage increase (as would happen through backend)
      const increasedUsage = mockUsageLimits({
        transactions: { used: 450, limit: 500, percentage: 90 }, // Near limit
        bank_accounts: { used: 2, limit: 2, percentage: 100 },   // At limit
        ai_requests: { used: 45, limit: 50, percentage: 90 },    // Near limit
      });

      mockApiClient.get.mockResolvedValue(increasedUsage);

      // Trigger refetch (simulating backend update)
      queryClient.invalidateQueries({ queryKey: ['usage-limits'] });

      await waitFor(() => {
        expect(result.current.usageLimits).toEqual(increasedUsage);
        expect(result.current.shouldShowUsageWarning()).toBe(true);
        expect(result.current.isUsageLimitReached('bank_accounts')).toBe(true);
        expect(result.current.getUsageWarningLevel('transactions')).toBe('warning');
      });
    });
  });

  describe('Plan Changes and Feature Access', () => {
    it('should handle plan upgrades and feature access changes', async () => {
      // Start with basic plan
      const basicPlan = mockSubscriptionPlan({
        name: 'Basic',
        has_ai_insights: false,
        has_advanced_reports: false,
        max_transactions: 500,
        max_ai_requests: 50,
      });

      const basicStatus = mockActiveSubscriptionStatus();
      basicStatus.plan = basicPlan;

      mockApiClient.get.mockResolvedValue(basicStatus);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.subscription).toEqual(basicStatus);
        expect(result.current.canUseFeature('ai_insights')).toBe(false);
        expect(result.current.canUseFeature('advanced_reports')).toBe(false);
      });

      // Simulate plan upgrade to premium
      const premiumPlan = mockSubscriptionPlan({
        name: 'Premium',
        has_ai_insights: true,
        has_advanced_reports: true,
        max_transactions: 2000,
        max_ai_requests: 200,
      });

      const premiumStatus = mockActiveSubscriptionStatus();
      premiumStatus.plan = premiumPlan;

      mockApiClient.get.mockResolvedValue(premiumStatus);

      // Trigger refetch after plan change
      queryClient.invalidateQueries({ queryKey: ['subscription-status'] });

      await waitFor(() => {
        expect(result.current.subscription?.plan?.name).toBe('Premium');
        expect(result.current.canUseFeature('ai_insights')).toBe(true);
        expect(result.current.canUseFeature('advanced_reports')).toBe(true);
      });
    });
  });

  describe('Error Handling and Recovery', () => {
    it('should handle API errors gracefully and recover', async () => {
      // Initial successful load
      const mockStatus = mockActiveSubscriptionStatus();
      mockApiClient.get.mockResolvedValueOnce(mockStatus);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.subscription).toEqual(mockStatus);
        expect(result.current.error).toBeNull();
      });

      // Simulate API error
      const apiError = new Error('API Error');
      mockApiClient.get.mockRejectedValueOnce(apiError);

      // Trigger refetch that will fail
      queryClient.invalidateQueries({ queryKey: ['subscription-status'] });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      // Simulate recovery
      mockApiClient.get.mockResolvedValueOnce(mockStatus);

      // Retry the request
      queryClient.invalidateQueries({ queryKey: ['subscription-status'] });

      await waitFor(() => {
        expect(result.current.subscription).toEqual(mockStatus);
        expect(result.current.error).toBeNull();
      });
    });

    it('should handle payment failures gracefully', async () => {
      const mockStatus = mockSubscriptionStatus();
      mockApiClient.get.mockResolvedValue(mockStatus);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.subscription).toEqual(mockStatus);
      });

      // Simulate payment failure
      const paymentError = new Error('Payment failed');
      mockApiClient.post.mockRejectedValueOnce(paymentError);

      const checkoutData = {
        plan_id: 1,
        billing_period: 'monthly' as const,
        success_url: 'https://example.com/success',
        cancel_url: 'https://example.com/cancel',
      };

      result.current.createCheckoutSession.mutate(checkoutData);

      await waitFor(() => {
        expect(result.current.createCheckoutSession.error).toBeTruthy();
        expect(result.current.createCheckoutSession.error).toBe(paymentError);
      });

      // Verify subscription status remains unchanged
      expect(result.current.subscription).toEqual(mockStatus);
    });
  });

  describe('Data Consistency', () => {
    it('should maintain data consistency across multiple hooks', async () => {
      const mockStatus = mockActiveSubscriptionStatus();
      const mockUsage = mockUsageLimits();

      mockApiClient.get
        .mockResolvedValueOnce(mockStatus)
        .mockResolvedValueOnce(mockUsage);

      // Render both hooks with same query client
      const { result: subscriptionResult } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      const { result: usageResult } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(subscriptionResult.current.subscription).toEqual(mockStatus);
        expect(usageResult.current.usageLimits).toEqual(mockUsage);
      });

      // Both hooks should share the same query client and maintain consistency
      expect(subscriptionResult.current.isActive).toBe(true);
      expect(usageResult.current.shouldShowUsageWarning()).toBe(false);

      // Update data and verify both hooks update consistently
      const updatedUsage = mockUsageLimits({
        transactions: { used: 450, limit: 500, percentage: 90 },
      });

      mockApiClient.get.mockResolvedValueOnce(updatedUsage);

      queryClient.invalidateQueries({ queryKey: ['usage-limits'] });

      await waitFor(() => {
        expect(usageResult.current.usageLimits).toEqual(updatedUsage);
        expect(usageResult.current.shouldShowUsageWarning()).toBe(true);
      });

      // Subscription status should remain unchanged
      expect(subscriptionResult.current.subscription).toEqual(mockStatus);
    });
  });

  describe('Real-time Updates Simulation', () => {
    it('should handle real-time usage updates', async () => {
      const initialUsage = mockUsageLimits({
        transactions: { used: 100, limit: 500, percentage: 20 },
      });

      mockApiClient.get.mockResolvedValue(initialUsage);

      const { result } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.usageLimits?.transactions.used).toBe(100);
      });

      // Simulate real-time usage increase (e.g., WebSocket update)
      const updates = [
        { used: 120, limit: 500, percentage: 24 },
        { used: 150, limit: 500, percentage: 30 },
        { used: 200, limit: 500, percentage: 40 },
      ];

      for (const update of updates) {
        const updatedUsage = mockUsageLimits({
          transactions: update,
        });

        mockApiClient.get.mockResolvedValueOnce(updatedUsage);
        queryClient.invalidateQueries({ queryKey: ['usage-limits'] });

        await waitFor(() => {
          expect(result.current.usageLimits?.transactions.used).toBe(update.used);
          expect(result.current.usageLimits?.transactions.percentage).toBe(update.percentage);
        });
      }
    });
  });

  describe('Subscription Lifecycle Management', () => {
    it('should handle complete subscription cancellation flow', async () => {
      // Start with active subscription
      const activeStatus = mockActiveSubscriptionStatus();
      mockApiClient.get.mockResolvedValue(activeStatus);

      const { result } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isActive).toBe(true);
      });

      // Cancel subscription
      const cancellationResponse = {
        status: 'cancelled',
        message: 'Subscription cancelled successfully'
      };

      mockApiClient.post.mockResolvedValueOnce(cancellationResponse);

      result.current.cancelSubscription.mutate();

      await waitFor(() => {
        expect(mockApiClient.post).toHaveBeenCalledWith('/api/payments/subscription/cancel/', {});
      });

      // Update subscription status to reflect cancellation
      const cancelledStatus = mockSubscriptionStatus({
        subscription_status: 'cancelled',
        requires_payment_setup: false,
        has_payment_method: true,
      });

      mockApiClient.get.mockResolvedValue(cancelledStatus);
      queryClient.invalidateQueries({ queryKey: ['subscription-status'] });

      await waitFor(() => {
        expect(result.current.subscription?.subscription_status).toBe('cancelled');
        expect(result.current.isActive).toBe(false);
      });
    });
  });

  describe('Performance and Caching', () => {
    it('should efficiently cache and reuse data across multiple components', async () => {
      const mockStatus = mockActiveSubscriptionStatus();
      mockApiClient.get.mockResolvedValue(mockStatus);

      // Create multiple hook instances (simulating multiple components)
      const { result: result1 } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      const { result: result2 } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      const { result: result3 } = renderHook(() => useSubscription(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result1.current.subscription).toEqual(mockStatus);
        expect(result2.current.subscription).toEqual(mockStatus);
        expect(result3.current.subscription).toEqual(mockStatus);
      });

      // Should only make one API call due to caching
      expect(mockApiClient.get).toHaveBeenCalledTimes(1);

      // All instances should have the same data
      expect(result1.current.isActive).toBe(result2.current.isActive);
      expect(result2.current.isActive).toBe(result3.current.isActive);
    });
  });
});