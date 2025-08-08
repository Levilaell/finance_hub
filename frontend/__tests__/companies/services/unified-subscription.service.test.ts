/**
 * Unit tests for unified subscription service
 */
import { subscriptionService } from '@/services/unified-subscription.service';
import { apiClient } from '@/lib/api-client';
import {
  mockSubscriptionPlan,
  mockCompany,
  mockUsageLimits,
  mockSubscriptionStatus,
  mockPremiumPlan,
} from '../test-utils';

// Mock the API client
jest.mock('@/lib/api-client');
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('UnifiedSubscriptionService', () => {
  
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getSubscriptionPlans', () => {
    it('should fetch subscription plans successfully', async () => {
      const mockPlans = [mockSubscriptionPlan(), mockPremiumPlan()];
      mockApiClient.get.mockResolvedValue(mockPlans);

      const result = await subscriptionService.getSubscriptionPlans();

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/companies/plans/');
      expect(result).toEqual(mockPlans);
    });

    it('should handle API errors when fetching plans', async () => {
      const errorMessage = 'Failed to fetch plans';
      mockApiClient.get.mockRejectedValue(new Error(errorMessage));

      await expect(subscriptionService.getSubscriptionPlans()).rejects.toThrow(errorMessage);
      expect(mockApiClient.get).toHaveBeenCalledWith('/api/companies/plans/');
    });
  });

  describe('getCompanyDetails', () => {
    it('should fetch company details successfully', async () => {
      const mockCompanyData = mockCompany();
      mockApiClient.get.mockResolvedValue(mockCompanyData);

      const result = await subscriptionService.getCompanyDetails();

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/companies/detail/');
      expect(result).toEqual(mockCompanyData);
    });

    it('should handle API errors when fetching company details', async () => {
      const errorMessage = 'Company not found';
      mockApiClient.get.mockRejectedValue(new Error(errorMessage));

      await expect(subscriptionService.getCompanyDetails()).rejects.toThrow(errorMessage);
      expect(mockApiClient.get).toHaveBeenCalledWith('/api/companies/detail/');
    });
  });

  describe('getUsageLimits', () => {
    it('should fetch usage limits successfully', async () => {
      const mockUsage = mockUsageLimits();
      mockApiClient.get.mockResolvedValue(mockUsage);

      const result = await subscriptionService.getUsageLimits();

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/companies/usage-limits/');
      expect(result).toEqual(mockUsage);
      expect(result).toHaveProperty('transactions');
      expect(result).toHaveProperty('bank_accounts');
      expect(result).toHaveProperty('ai_requests');
    });

    it('should handle API errors when fetching usage limits', async () => {
      const errorMessage = 'Failed to fetch usage limits';
      mockApiClient.get.mockRejectedValue(new Error(errorMessage));

      await expect(subscriptionService.getUsageLimits()).rejects.toThrow(errorMessage);
    });
  });

  describe('getSubscriptionStatus', () => {
    it('should fetch subscription status successfully', async () => {
      const mockStatus = mockSubscriptionStatus();
      mockApiClient.get.mockResolvedValue(mockStatus);

      const result = await subscriptionService.getSubscriptionStatus();

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/companies/subscription-status/');
      expect(result).toEqual(mockStatus);
      expect(result).toHaveProperty('subscription_status');
      expect(result).toHaveProperty('plan');
      expect(result).toHaveProperty('trial_days_left');
    });

    it('should handle API errors when fetching subscription status', async () => {
      const errorMessage = 'Failed to fetch subscription status';
      mockApiClient.get.mockRejectedValue(new Error(errorMessage));

      await expect(subscriptionService.getSubscriptionStatus()).rejects.toThrow(errorMessage);
    });
  });

  describe('Payment Methods', () => {
    it('should create checkout session successfully', async () => {
      const checkoutData = {
        plan_id: 1,
        billing_period: 'monthly' as const,
        success_url: 'https://example.com/success',
        cancel_url: 'https://example.com/cancel',
      };
      const mockResponse = { session_id: 'sess_123', checkout_url: 'https://checkout.stripe.com' };
      mockApiClient.post.mockResolvedValue(mockResponse);

      const result = await subscriptionService.createCheckoutSession(checkoutData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/payments/checkout/create/', checkoutData);
      expect(result).toEqual(mockResponse);
    });

    it('should validate payment successfully', async () => {
      const mockValidation = { status: 'success', message: 'Payment validated' };
      mockApiClient.post.mockResolvedValue(mockValidation);

      const result = await subscriptionService.validatePayment('session_123');

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/payments/checkout/validate/', {
        session_id: 'session_123'
      });
      expect(result).toEqual(mockValidation);
    });

    it('should cancel subscription successfully', async () => {
      const mockCancellation = { status: 'cancelled', message: 'Subscription cancelled' };
      mockApiClient.post.mockResolvedValue(mockCancellation);

      const result = await subscriptionService.cancelSubscription();

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/payments/subscription/cancel/', {});
      expect(result).toEqual(mockCancellation);
    });

    it('should get payment methods successfully', async () => {
      const mockPaymentMethods = [
        { id: 1, type: 'card', brand: 'visa', last4: '4242', is_default: true }
      ];
      mockApiClient.get.mockResolvedValue(mockPaymentMethods);

      const result = await subscriptionService.getPaymentMethods();

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/payments/payment-methods/');
      expect(result).toEqual(mockPaymentMethods);
    });

    it('should get payment history successfully', async () => {
      const mockPayments = [
        { id: 1, amount: 19.99, status: 'paid', created_at: '2023-01-01' }
      ];
      mockApiClient.get.mockResolvedValue(mockPayments);

      const result = await subscriptionService.getPaymentHistory();

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/payments/payments/');
      expect(result).toEqual(mockPayments);
    });

    it('should create payment method successfully', async () => {
      const paymentMethodData = {
        type: 'card' as const,
        token: 'tok_123',
        brand: 'visa',
        last4: '4242',
        is_default: true,
      };
      const mockPaymentMethod = { id: 1, ...paymentMethodData };
      mockApiClient.post.mockResolvedValue(mockPaymentMethod);

      const result = await subscriptionService.createPaymentMethod(paymentMethodData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/payments/payment-methods/', paymentMethodData);
      expect(result).toEqual(mockPaymentMethod);
    });

    it('should delete payment method successfully', async () => {
      const mockResponse = { success: true, message: 'Payment method deleted' };
      mockApiClient.delete.mockResolvedValue(mockResponse);

      const result = await subscriptionService.deletePaymentMethod(1);

      expect(mockApiClient.delete).toHaveBeenCalledWith('/api/payments/payment-methods/1/');
      expect(result).toEqual(mockResponse);
    });

    it('should update payment method successfully', async () => {
      const updateData = { is_default: true };
      const mockUpdatedMethod = { id: 1, type: 'card', is_default: true };
      mockApiClient.patch.mockResolvedValue(mockUpdatedMethod);

      const result = await subscriptionService.updatePaymentMethod(1, updateData);

      expect(mockApiClient.patch).toHaveBeenCalledWith('/api/payments/payment-methods/1/', updateData);
      expect(result).toEqual(mockUpdatedMethod);
    });
  });

  describe('Utility Methods', () => {
    describe('canUseFeature', () => {
      it('should return false for null plan', () => {
        const result = subscriptionService.canUseFeature(null, 'ai_insights');
        expect(result).toBe(false);
      });

      it('should return true for ai_insights when plan has it', () => {
        const plan = mockSubscriptionPlan({ has_ai_insights: true });
        const result = subscriptionService.canUseFeature(plan, 'ai_insights');
        expect(result).toBe(true);
      });

      it('should return false for ai_insights when plan does not have it', () => {
        const plan = mockSubscriptionPlan({ has_ai_insights: false });
        const result = subscriptionService.canUseFeature(plan, 'ai_insights');
        expect(result).toBe(false);
      });

      it('should return true for advanced_reports when plan has it', () => {
        const plan = mockSubscriptionPlan({ has_advanced_reports: true });
        const result = subscriptionService.canUseFeature(plan, 'advanced_reports');
        expect(result).toBe(true);
      });

      it('should return false for advanced_reports when plan does not have it', () => {
        const plan = mockSubscriptionPlan({ has_advanced_reports: false });
        const result = subscriptionService.canUseFeature(plan, 'advanced_reports');
        expect(result).toBe(false);
      });

      it('should return false for unknown features', () => {
        const plan = mockSubscriptionPlan();
        const result = subscriptionService.canUseFeature(plan, 'unknown_feature');
        expect(result).toBe(false);
      });
    });

    describe('isUsageLimitReached', () => {
      it('should return true when percentage is 100 or more', () => {
        const usage = mockUsageLimits({
          transactions: { used: 500, limit: 500, percentage: 100 },
        });
        
        const result = subscriptionService.isUsageLimitReached(usage, 'transactions');
        expect(result).toBe(true);
      });

      it('should return true when percentage is over 100', () => {
        const usage = mockUsageLimits({
          transactions: { used: 550, limit: 500, percentage: 110 },
        });
        
        const result = subscriptionService.isUsageLimitReached(usage, 'transactions');
        expect(result).toBe(true);
      });

      it('should return false when percentage is under 100', () => {
        const usage = mockUsageLimits({
          transactions: { used: 450, limit: 500, percentage: 90 },
        });
        
        const result = subscriptionService.isUsageLimitReached(usage, 'transactions');
        expect(result).toBe(false);
      });

      it('should work for all usage types', () => {
        const usage = mockUsageLimits({
          transactions: { used: 500, limit: 500, percentage: 100 },
          bank_accounts: { used: 1, limit: 2, percentage: 50 },
          ai_requests: { used: 100, limit: 100, percentage: 100 },
        });
        
        expect(subscriptionService.isUsageLimitReached(usage, 'transactions')).toBe(true);
        expect(subscriptionService.isUsageLimitReached(usage, 'bank_accounts')).toBe(false);
        expect(subscriptionService.isUsageLimitReached(usage, 'ai_requests')).toBe(true);
      });
    });

    describe('getUsageWarningLevel', () => {
      it('should return "critical" for percentage >= 100', () => {
        expect(subscriptionService.getUsageWarningLevel(100)).toBe('critical');
        expect(subscriptionService.getUsageWarningLevel(110)).toBe('critical');
      });

      it('should return "warning" for percentage >= 80 and < 100', () => {
        expect(subscriptionService.getUsageWarningLevel(80)).toBe('warning');
        expect(subscriptionService.getUsageWarningLevel(90)).toBe('warning');
        expect(subscriptionService.getUsageWarningLevel(99)).toBe('warning');
      });

      it('should return "none" for percentage < 80', () => {
        expect(subscriptionService.getUsageWarningLevel(0)).toBe('none');
        expect(subscriptionService.getUsageWarningLevel(50)).toBe('none');
        expect(subscriptionService.getUsageWarningLevel(79)).toBe('none');
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      const networkError = new Error('Network Error');
      mockApiClient.get.mockRejectedValue(networkError);

      await expect(subscriptionService.getSubscriptionPlans()).rejects.toThrow('Network Error');
    });

    it('should handle API errors with specific status codes', async () => {
      const apiError = {
        response: {
          status: 404,
          data: { error: 'Company not found' }
        }
      };
      mockApiClient.get.mockRejectedValue(apiError);

      await expect(subscriptionService.getCompanyDetails()).rejects.toEqual(apiError);
    });

    it('should handle malformed response data', async () => {
      mockApiClient.get.mockResolvedValue(null);

      const result = await subscriptionService.getSubscriptionPlans();
      expect(result).toBeNull();
    });
  });

  describe('Data Type Validation', () => {
    it('should handle subscription plans with all required fields', async () => {
      const completePlan = mockSubscriptionPlan({
        id: 1,
        name: 'Complete Plan',
        slug: 'complete',
        price_monthly: 19.99,
        price_yearly: 199.99,
        max_transactions: 1000,
        max_bank_accounts: 5,
        max_ai_requests: 100,
        has_ai_insights: true,
        has_advanced_reports: true,
        is_active: true,
        display_order: 1,
      });

      mockApiClient.get.mockResolvedValue([completePlan]);

      const result = await subscriptionService.getSubscriptionPlans();
      expect(result[0]).toMatchObject(completePlan);
    });

    it('should handle company data with all required fields', async () => {
      const completeCompany = mockCompany({
        id: 'test-company',
        name: 'Test Company',
        owner_email: 'test@example.com',
        subscription_status: 'active',
        billing_cycle: 'monthly',
        current_month_transactions: 100,
        current_month_ai_requests: 25,
      });

      mockApiClient.get.mockResolvedValue(completeCompany);

      const result = await subscriptionService.getCompanyDetails();
      expect(result).toMatchObject(completeCompany);
    });

    it('should handle usage limits with proper structure', async () => {
      const completeUsage = mockUsageLimits({
        transactions: { used: 100, limit: 500, percentage: 20 },
        bank_accounts: { used: 2, limit: 5, percentage: 40 },
        ai_requests: { used: 25, limit: 100, percentage: 25 },
      });

      mockApiClient.get.mockResolvedValue(completeUsage);

      const result = await subscriptionService.getUsageLimits();
      expect(result).toMatchObject(completeUsage);
      
      // Validate structure
      ['transactions', 'bank_accounts', 'ai_requests'].forEach(key => {
        expect(result[key as keyof typeof result]).toHaveProperty('used');
        expect(result[key as keyof typeof result]).toHaveProperty('limit');
        expect(result[key as keyof typeof result]).toHaveProperty('percentage');
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty subscription plans array', async () => {
      mockApiClient.get.mockResolvedValue([]);

      const result = await subscriptionService.getSubscriptionPlans();
      expect(result).toEqual([]);
      expect(Array.isArray(result)).toBe(true);
    });

    it('should handle zero usage values', async () => {
      const zeroUsage = mockUsageLimits({
        transactions: { used: 0, limit: 500, percentage: 0 },
        bank_accounts: { used: 0, limit: 2, percentage: 0 },
        ai_requests: { used: 0, limit: 50, percentage: 0 },
      });

      mockApiClient.get.mockResolvedValue(zeroUsage);

      const result = await subscriptionService.getUsageLimits();
      expect(result.transactions.used).toBe(0);
      expect(result.transactions.percentage).toBe(0);
    });

    it('should handle maximum usage values', async () => {
      const maxUsage = mockUsageLimits({
        transactions: { used: 500, limit: 500, percentage: 100 },
        bank_accounts: { used: 2, limit: 2, percentage: 100 },
        ai_requests: { used: 50, limit: 50, percentage: 100 },
      });

      mockApiClient.get.mockResolvedValue(maxUsage);

      const result = await subscriptionService.getUsageLimits();
      expect(result.transactions.percentage).toBe(100);
      expect(subscriptionService.isUsageLimitReached(result, 'transactions')).toBe(true);
    });

    it('should handle company without subscription plan', async () => {
      const companyNoPlan = mockCompany({ subscription_plan: null });
      mockApiClient.get.mockResolvedValue(companyNoPlan);

      const result = await subscriptionService.getCompanyDetails();
      expect(result.subscription_plan).toBeNull();
      
      // Should return false for any feature
      expect(subscriptionService.canUseFeature(result.subscription_plan, 'ai_insights')).toBe(false);
    });
  });

  describe('Performance', () => {
    it('should not block on multiple concurrent calls', async () => {
      const mockPlan = mockSubscriptionPlan();
      mockApiClient.get.mockResolvedValue([mockPlan]);

      const promises = Array(10).fill(0).map(() => subscriptionService.getSubscriptionPlans());
      
      const results = await Promise.all(promises);
      
      expect(results).toHaveLength(10);
      results.forEach(result => {
        expect(result).toEqual([mockPlan]);
      });
      
      expect(mockApiClient.get).toHaveBeenCalledTimes(10);
    });

    it('should handle rapid successive calls', async () => {
      const mockCompanyData = mockCompany();
      mockApiClient.get.mockResolvedValue(mockCompanyData);

      // Make rapid successive calls
      const call1 = subscriptionService.getCompanyDetails();
      const call2 = subscriptionService.getCompanyDetails();
      const call3 = subscriptionService.getCompanyDetails();

      const [result1, result2, result3] = await Promise.all([call1, call2, call3]);

      expect(result1).toEqual(mockCompanyData);
      expect(result2).toEqual(mockCompanyData);
      expect(result3).toEqual(mockCompanyData);
    });
  });
});