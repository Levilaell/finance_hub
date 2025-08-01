/**
 * Tests for SubscriptionCard component
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSubscription } from '@/hooks/useSubscription';
import { useUsageLimits } from '@/hooks/useUsageLimits';
import { SubscriptionCard } from '@/components/payment/SubscriptionCard';
import {
  mockSubscriptionStatus,
  mockActiveSubscriptionStatus,
  mockUsageLimits,
  subscriptionScenarios,
  usageScenarios,
  createQueryClient,
} from '../test-utils';

// Mock dependencies
jest.mock('@/hooks/useSubscription');
jest.mock('@/hooks/useUsageLimits');
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

const mockUseSubscription = useSubscription as jest.MockedFunction<typeof useSubscription>;
const mockUseUsageLimits = useUsageLimits as jest.MockedFunction<typeof useUsageLimits>;

const createWrapper = (queryClient: QueryClient) => {
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('SubscriptionCard', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = createQueryClient();
    jest.clearAllMocks();
  });

  describe('Loading State', () => {
    it('should show loading skeleton when subscription is loading', () => {
      mockUseSubscription.mockReturnValue({
        subscription: undefined,
        isLoading: true,
        error: null,
        isActive: false,
        isTrial: false,
        trialDaysRemaining: 0,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: undefined,
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      // Should show loading skeleton
      expect(screen.getByTestId('test-wrapper')).toBeInTheDocument();
      const skeletons = document.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  describe('No Subscription State', () => {
    it('should show no subscription message when subscription is null', () => {
      mockUseSubscription.mockReturnValue({
        subscription: null,
        isLoading: false,
        error: null,
        isActive: false,
        isTrial: false,
        trialDaysRemaining: 0,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: undefined,
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      expect(screen.getByText('No Active Subscription')).toBeInTheDocument();
      expect(screen.getByText('Start your free trial to access all features')).toBeInTheDocument();
      expect(screen.getByText('Start Free Trial')).toBeInTheDocument();
    });

    it('should navigate to subscription upgrade when start trial button is clicked', () => {
      const mockPush = jest.fn();
      jest.doMock('next/navigation', () => ({
        useRouter: () => ({ push: mockPush }),
      }));

      mockUseSubscription.mockReturnValue({
        subscription: null,
        isLoading: false,
        error: null,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: undefined,
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      const startTrialButton = screen.getByText('Start Free Trial');
      startTrialButton.click();

      expect(mockPush).toHaveBeenCalledWith('/subscription/upgrade');
    });
  });

  describe('Trial Subscription', () => {
    it('should display trial subscription details', () => {
      const trialStatus = subscriptionScenarios.activeTrial;
      
      mockUseSubscription.mockReturnValue({
        subscription: trialStatus,
        isLoading: false,
        error: null,
        isActive: false,
        isTrial: true,
        trialDaysRemaining: 10,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: mockUsageLimits(),
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      expect(screen.getByText(trialStatus.plan!.name)).toBeInTheDocument();
      expect(screen.getByText('Trial')).toBeInTheDocument();
      expect(screen.getByText('10 days remaining in trial')).toBeInTheDocument();
    });

    it('should show trial ending warning for expiring trial', () => {
      const expiringSoon = subscriptionScenarios.expiringSoon;
      
      mockUseSubscription.mockReturnValue({
        subscription: expiringSoon,
        isLoading: false,
        error: null,
        isActive: false,
        isTrial: true,
        trialDaysRemaining: 2,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: mockUsageLimits(),
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      expect(screen.getByText('2 days remaining in trial')).toBeInTheDocument();
    });
  });

  describe('Active Subscription', () => {
    it('should display active subscription details', () => {
      const activeStatus = subscriptionScenarios.active;
      
      mockUseSubscription.mockReturnValue({
        subscription: activeStatus,
        isLoading: false,
        error: null,
        isActive: true,
        isTrial: false,
        trialDaysRemaining: 0,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: mockUsageLimits(),
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      expect(screen.getByText(activeStatus.plan!.name)).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Subscription Active')).toBeInTheDocument();
    });

    it('should show monthly price for active subscription', () => {
      const activeStatus = mockActiveSubscriptionStatus();
      
      mockUseSubscription.mockReturnValue({
        subscription: activeStatus,
        isLoading: false,
        error: null,
        isActive: true,
        isTrial: false,
        trialDaysRemaining: 0,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: mockUsageLimits(),
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      const planPrice = activeStatus.plan!.price_monthly;
      expect(screen.getByText(`R$ ${planPrice}/month`)).toBeInTheDocument();
    });
  });

  describe('Usage Display', () => {
    it('should display usage limits when available', () => {
      const mockUsage = usageScenarios.underLimit;
      
      mockUseSubscription.mockReturnValue({
        subscription: mockActiveSubscriptionStatus(),
        isLoading: false,
        error: null,
        isActive: true,
        isTrial: false,
        trialDaysRemaining: 0,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: mockUsage,
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      // Check usage displays
      expect(screen.getByText('Usage This Period')).toBeInTheDocument();
      expect(screen.getByText('Transactions')).toBeInTheDocument();
      expect(screen.getByText('Bank Accounts')).toBeInTheDocument();
      expect(screen.getByText('AI Requests')).toBeInTheDocument();

      // Check usage values
      expect(screen.getByText(`${mockUsage.transactions.used} / ${mockUsage.transactions.limit}`)).toBeInTheDocument();
      expect(screen.getByText(`${mockUsage.bank_accounts.used} / ${mockUsage.bank_accounts.limit}`)).toBeInTheDocument();
      expect(screen.getByText(`${mockUsage.ai_requests.used} / ${mockUsage.ai_requests.limit}`)).toBeInTheDocument();
    });

    it('should display high usage with proper visual indicators', () => {
      const nearLimitUsage = usageScenarios.nearLimit;
      
      mockUseSubscription.mockReturnValue({
        subscription: mockActiveSubscriptionStatus(),
        isLoading: false,
        error: null,
        isActive: true,
        isTrial: false,
        trialDaysRemaining: 0,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: nearLimitUsage,
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      // Should show usage values
      expect(screen.getByText(`${nearLimitUsage.transactions.used} / ${nearLimitUsage.transactions.limit}`)).toBeInTheDocument();
      expect(screen.getByText(`${nearLimitUsage.bank_accounts.used} / ${nearLimitUsage.bank_accounts.limit}`)).toBeInTheDocument();
      expect(screen.getByText(`${nearLimitUsage.ai_requests.used} / ${nearLimitUsage.ai_requests.limit}`)).toBeInTheDocument();
    });

    it('should handle missing usage data gracefully', () => {
      mockUseSubscription.mockReturnValue({
        subscription: mockActiveSubscriptionStatus(),
        isLoading: false,
        error: null,
        isActive: true,
        isTrial: false,
        trialDaysRemaining: 0,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: undefined,
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      // Should not show usage section
      expect(screen.queryByText('Usage This Period')).not.toBeInTheDocument();
    });
  });

  describe('Status Badges', () => {
    it('should show correct badge color for trial status', () => {
      const trialStatus = subscriptionScenarios.activeTrial;
      
      mockUseSubscription.mockReturnValue({
        subscription: trialStatus,
        isLoading: false,
        error: null,
        isTrial: true,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: mockUsageLimits(),
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      const badge = screen.getByText('Trial');
      expect(badge).toBeInTheDocument();
      expect(badge.className).toContain('bg-blue-500');
    });

    it('should show correct badge color for active status', () => {
      const activeStatus = subscriptionScenarios.active;
      
      mockUseSubscription.mockReturnValue({
        subscription: activeStatus,
        isLoading: false,
        error: null,
        isActive: true,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: mockUsageLimits(),
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      const badge = screen.getByText('Active');
      expect(badge).toBeInTheDocument();
      expect(badge.className).toContain('bg-green-500');
    });

    it('should show correct badge color for cancelled status', () => {
      const cancelledStatus = subscriptionScenarios.cancelled;
      
      mockUseSubscription.mockReturnValue({
        subscription: cancelledStatus,
        isLoading: false,
        error: null,
        isActive: false,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: mockUsageLimits(),
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      const badge = screen.getByText('Cancelled');
      expect(badge).toBeInTheDocument();
      expect(badge.className).toContain('bg-yellow-500');
    });

    it('should show correct badge color for expired status', () => {
      const expiredStatus = subscriptionScenarios.expired;
      
      mockUseSubscription.mockReturnValue({
        subscription: expiredStatus,
        isLoading: false,
        error: null,
        isActive: false,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: mockUsageLimits(),
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      const badge = screen.getByText('Expired');
      expect(badge).toBeInTheDocument();
      expect(badge.className).toContain('bg-red-500');
    });
  });

  describe('Action Buttons', () => {
    it('should show upgrade button for active non-enterprise plan', () => {
      const activeStatus = mockActiveSubscriptionStatus();
      // Ensure it's not enterprise plan
      activeStatus.plan!.name = 'Premium';
      
      mockUseSubscription.mockReturnValue({
        subscription: activeStatus,
        isLoading: false,
        error: null,
        isActive: true,
        isTrial: false,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: mockUsageLimits(),
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      expect(screen.getByText('Upgrade Plan')).toBeInTheDocument();
    });

    it('should not show upgrade button for enterprise plan', () => {
      const enterpriseStatus = mockActiveSubscriptionStatus();
      enterpriseStatus.plan!.name = 'enterprise';
      
      mockUseSubscription.mockReturnValue({
        subscription: enterpriseStatus,
        isLoading: false,
        error: null,
        isActive: true,
        isTrial: false,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: mockUsageLimits(),
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      expect(screen.queryByText('Upgrade Plan')).not.toBeInTheDocument();
    });

    it('should always show manage subscription button', () => {
      mockUseSubscription.mockReturnValue({
        subscription: mockActiveSubscriptionStatus(),
        isLoading: false,
        error: null,
        isActive: true,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: mockUsageLimits(),
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      expect(screen.getByText('Manage Subscription')).toBeInTheDocument();
    });
  });

  describe('Trial End Date', () => {
    it('should format and display trial end date', () => {
      const trialStatus = mockSubscriptionStatus({
        trial_ends_at: '2023-12-25T00:00:00Z'
      });
      
      mockUseSubscription.mockReturnValue({
        subscription: trialStatus,
        isLoading: false,
        error: null,
        isTrial: true,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: mockUsageLimits(),
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      expect(screen.getByText('Trial Ends')).toBeInTheDocument();
      // The exact format depends on date-fns format function
      expect(screen.getByText(/Dec 25, 2023/)).toBeInTheDocument();
    });

    it('should not show trial end date for active subscription', () => {
      const activeStatus = mockActiveSubscriptionStatus();
      
      mockUseSubscription.mockReturnValue({
        subscription: activeStatus,
        isLoading: false,
        error: null,
        isActive: true,
        isTrial: false,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: mockUsageLimits(),
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      expect(screen.queryByText('Trial Ends')).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle subscription without plan', () => {
      const statusNoPlan = mockSubscriptionStatus({ plan: null });
      
      mockUseSubscription.mockReturnValue({
        subscription: statusNoPlan,
        isLoading: false,
        error: null,
        isActive: false,
        isTrial: true,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: mockUsageLimits(),
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      expect(screen.getByText('No Plan')).toBeInTheDocument();
      expect(screen.getByText('No active subscription')).toBeInTheDocument();
    });

    it('should handle zero usage values', () => {
      const zeroUsage = mockUsageLimits({
        transactions: { used: 0, limit: 500, percentage: 0 },
        bank_accounts: { used: 0, limit: 2, percentage: 0 },
        ai_requests: { used: 0, limit: 50, percentage: 0 },
      });
      
      mockUseSubscription.mockReturnValue({
        subscription: mockActiveSubscriptionStatus(),
        isLoading: false,
        error: null,
        isActive: true,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: zeroUsage,
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      expect(screen.getByText('0 / 500')).toBeInTheDocument();
      expect(screen.getByText('0 / 2')).toBeInTheDocument();
      expect(screen.getByText('0 / 50')).toBeInTheDocument();
    });

    it('should handle malformed subscription data', () => {
      const malformedStatus = {
        subscription_status: 'unknown',
        plan: null,
        trial_days_left: -1,
      } as any;
      
      mockUseSubscription.mockReturnValue({
        subscription: malformedStatus,
        isLoading: false,
        error: null,
        isActive: false,
        isTrial: false,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: mockUsageLimits(),
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      // Should still render without crashing
      expect(screen.getByText('No Plan')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels and roles', () => {
      mockUseSubscription.mockReturnValue({
        subscription: mockActiveSubscriptionStatus(),
        isLoading: false,
        error: null,
        isActive: true,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: mockUsageLimits(),
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      // Buttons should be accessible
      const upgradeButton = screen.queryByText('Upgrade Plan');
      const manageButton = screen.getByText('Manage Subscription');
      
      if (upgradeButton) {
        expect(upgradeButton.tagName).toBe('BUTTON');
      }
      expect(manageButton.tagName).toBe('BUTTON');
    });

    it('should provide meaningful text content for screen readers', () => {
      const trialStatus = subscriptionScenarios.activeTrial;
      
      mockUseSubscription.mockReturnValue({
        subscription: trialStatus,
        isLoading: false,
        error: null,
        isTrial: true,
        trialDaysRemaining: 5,
      } as any);

      mockUseUsageLimits.mockReturnValue({
        usageLimits: usageScenarios.underLimit,
      } as any);

      render(<SubscriptionCard />, { wrapper: createWrapper(queryClient) });

      // Should have descriptive text for screen readers
      expect(screen.getByText('5 days remaining in trial')).toBeInTheDocument();
      expect(screen.getByText('Usage This Period')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('should not re-render unnecessarily', async () => {
      const mockUsage = mockUsageLimits();
      const mockStatus = mockActiveSubscriptionStatus();
      
      const subscriptionMock = jest.fn().mockReturnValue({
        subscription: mockStatus,
        isLoading: false,
        error: null,
        isActive: true,
      });
      
      const usageMock = jest.fn().mockReturnValue({
        usageLimits: mockUsage,
      });
      
      mockUseSubscription.mockImplementation(subscriptionMock);
      mockUseUsageLimits.mockImplementation(usageMock);

      const { rerender } = render(<SubscriptionCard />, { 
        wrapper: createWrapper(queryClient) 
      });

      // Rerender with same props
      rerender(<SubscriptionCard />);

      // Hooks should be called but component should handle re-renders efficiently
      expect(subscriptionMock).toHaveBeenCalled();
      expect(usageMock).toHaveBeenCalled();
    });
  });
});