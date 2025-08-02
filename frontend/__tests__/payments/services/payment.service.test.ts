/**
 * Tests for payment service
 */
import { PaymentService } from '../../../services/payment.service';
import { apiClient } from '../../../lib/api-client';

// Mock API client
jest.mock('../../../lib/api-client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  },
}));

// Mock toast notifications
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
}));

describe('PaymentService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Subscription Plans', () => {
    it('should fetch subscription plans successfully', async () => {
      const mockPlans = [
        {
          id: 'basic',
          name: 'Basic Plan',
          display_name: 'Basic',
          monthly_price: 29.99,
          yearly_price: 299.99,
          max_transactions: 1000,
          max_bank_accounts: 2,
          max_ai_requests: 100,
        },
        {
          id: 'premium',
          name: 'Premium Plan',
          display_name: 'Premium',
          monthly_price: 99.99,
          yearly_price: 999.99,
          max_transactions: 10000,
          max_bank_accounts: 10,
          max_ai_requests: 1000,
        },
      ];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockPlans });

      const result = await PaymentService.getSubscriptionPlans();

      expect(apiClient.get).toHaveBeenCalledWith('/payments/subscription-plans/');
      expect(result).toEqual(mockPlans);
    });

    it('should handle subscription plans fetch error', async () => {
      const error = new Error('Failed to fetch plans');
      (apiClient.get as jest.Mock).mockRejectedValue(error);

      await expect(PaymentService.getSubscriptionPlans()).rejects.toThrow(
        'Failed to fetch plans'
      );
    });
  });

  describe('Payment Methods', () => {
    it('should fetch payment methods successfully', async () => {
      const mockPaymentMethods = [
        {
          id: 'pm_1234567890',
          type: 'card',
          card: {
            brand: 'visa',
            last4: '4242',
            exp_month: 12,
            exp_year: 2025,
          },
          billing_details: {
            name: 'John Doe',
            email: 'john@example.com',
          },
          created: '2023-01-01T00:00:00Z',
        },
      ];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockPaymentMethods });

      const result = await PaymentService.getPaymentMethods();

      expect(apiClient.get).toHaveBeenCalledWith('/payments/payment-methods/');
      expect(result).toEqual(mockPaymentMethods);
    });

    it('should create payment method successfully', async () => {
      const mockPaymentMethod = {
        id: 'pm_new123456',
        type: 'card',
        card: {
          brand: 'mastercard',
          last4: '5555',
          exp_month: 6,
          exp_year: 2026,
        },
      };

      const paymentMethodData = {
        payment_method_id: 'pm_new123456',
        billing_details: {
          name: 'Jane Doe',
          email: 'jane@example.com',
        },
      };

      (apiClient.post as jest.Mock).mockResolvedValue({ data: mockPaymentMethod });

      const result = await PaymentService.createPaymentMethod(paymentMethodData);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/payments/payment-methods/',
        paymentMethodData
      );
      expect(result).toEqual(mockPaymentMethod);
    });

    it('should delete payment method successfully', async () => {
      const paymentMethodId = 'pm_1234567890';

      (apiClient.delete as jest.Mock).mockResolvedValue({ data: { success: true } });

      const result = await PaymentService.deletePaymentMethod(paymentMethodId);

      expect(apiClient.delete).toHaveBeenCalledWith(
        `/payments/payment-methods/${paymentMethodId}/`
      );
      expect(result).toEqual({ success: true });
    });
  });

  describe('Checkout Sessions', () => {
    it('should create checkout session successfully', async () => {
      const mockSession = {
        id: 'cs_test_1234567890',
        url: 'https://checkout.stripe.com/c/pay/cs_test_1234567890',
        client_secret: 'cs_test_1234567890_secret',
        payment_status: 'unpaid',
      };

      const sessionData = {
        plan_id: 'basic',
        billing_cycle: 'monthly',
        success_url: 'https://app.example.com/success',
        cancel_url: 'https://app.example.com/cancel',
      };

      (apiClient.post as jest.Mock).mockResolvedValue({ data: mockSession });

      const result = await PaymentService.createCheckoutSession(sessionData);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/payments/checkout-sessions/',
        sessionData
      );
      expect(result).toEqual(mockSession);
    });

    it('should handle checkout session creation error', async () => {
      const sessionData = {
        plan_id: 'invalid',
        billing_cycle: 'monthly',
        success_url: 'https://app.example.com/success',
        cancel_url: 'https://app.example.com/cancel',
      };

      const error = new Error('Invalid plan ID');
      (apiClient.post as jest.Mock).mockRejectedValue(error);

      await expect(PaymentService.createCheckoutSession(sessionData)).rejects.toThrow(
        'Invalid plan ID'
      );
    });
  });

  describe('Payment Intents', () => {
    it('should create payment intent successfully', async () => {
      const mockIntent = {
        id: 'pi_1234567890',
        client_secret: 'pi_1234567890_secret_abc123',
        amount: 2999,
        currency: 'usd',
        status: 'requires_payment_method',
      };

      const intentData = {
        amount: 2999,
        currency: 'usd',
        description: 'Basic Plan Subscription',
        metadata: {
          plan_id: 'basic',
          billing_cycle: 'monthly',
        },
      };

      (apiClient.post as jest.Mock).mockResolvedValue({ data: mockIntent });

      const result = await PaymentService.createPaymentIntent(intentData);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/payments/payment-intents/',
        intentData
      );
      expect(result).toEqual(mockIntent);
    });

    it('should confirm payment intent successfully', async () => {
      const paymentIntentId = 'pi_1234567890';
      const confirmData = {
        payment_method: 'pm_1234567890',
        return_url: 'https://app.example.com/return',
      };

      const mockConfirmedIntent = {
        id: 'pi_1234567890',
        status: 'succeeded',
        charges: {
          data: [
            {
              id: 'ch_1234567890',
              amount: 2999,
              paid: true,
              status: 'succeeded',
            },
          ],
        },
      };

      (apiClient.post as jest.Mock).mockResolvedValue({ data: mockConfirmedIntent });

      const result = await PaymentService.confirmPaymentIntent(
        paymentIntentId,
        confirmData
      );

      expect(apiClient.post).toHaveBeenCalledWith(
        `/payments/payment-intents/${paymentIntentId}/confirm/`,
        confirmData
      );
      expect(result).toEqual(mockConfirmedIntent);
    });
  });

  describe('Payment History', () => {
    it('should fetch payment history successfully', async () => {
      const mockHistory = {
        count: 25,
        next: null,
        previous: null,
        results: [
          {
            id: 'pay_1234567890',
            amount: 2999,
            currency: 'usd',
            status: 'succeeded',
            description: 'Basic Plan Subscription',
            created: '2023-01-01T00:00:00Z',
            payment_method: {
              type: 'card',
              card: {
                brand: 'visa',
                last4: '4242',
              },
            },
          },
        ],
      };

      const filters = { limit: 10, offset: 0 };

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockHistory });

      const result = await PaymentService.getPaymentHistory(filters);

      expect(apiClient.get).toHaveBeenCalledWith('/payments/history/', {
        params: filters,
      });
      expect(result).toEqual(mockHistory);
    });

    it('should fetch payment history with date filters', async () => {
      const filters = {
        limit: 10,
        offset: 0,
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        status: 'succeeded',
      };

      (apiClient.get as jest.Mock).mockResolvedValue({ data: { results: [] } });

      await PaymentService.getPaymentHistory(filters);

      expect(apiClient.get).toHaveBeenCalledWith('/payments/history/', {
        params: filters,
      });
    });
  });

  describe('Subscription Management', () => {
    it('should get current subscription successfully', async () => {
      const mockSubscription = {
        id: 'sub_1234567890',
        status: 'active',
        plan: {
          id: 'basic',
          name: 'Basic Plan',
          amount: 2999,
        },
        current_period_start: '2023-01-01T00:00:00Z',
        current_period_end: '2023-02-01T00:00:00Z',
        trial_end: null,
        cancel_at_period_end: false,
      };

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockSubscription });

      const result = await PaymentService.getCurrentSubscription();

      expect(apiClient.get).toHaveBeenCalledWith('/payments/subscription/current/');
      expect(result).toEqual(mockSubscription);
    });

    it('should cancel subscription successfully', async () => {
      const subscriptionId = 'sub_1234567890';
      const cancelData = {
        cancel_at_period_end: true,
        cancellation_reason: 'customer_request',
      };

      const mockCancelledSubscription = {
        id: 'sub_1234567890',
        status: 'active',
        cancel_at_period_end: true,
        cancellation_details: {
          reason: 'customer_request',
          comment: null,
        },
      };

      (apiClient.post as jest.Mock).mockResolvedValue({
        data: mockCancelledSubscription,
      });

      const result = await PaymentService.cancelSubscription(subscriptionId, cancelData);

      expect(apiClient.post).toHaveBeenCalledWith(
        `/payments/subscription/${subscriptionId}/cancel/`,
        cancelData
      );
      expect(result).toEqual(mockCancelledSubscription);
    });

    it('should update subscription successfully', async () => {
      const subscriptionId = 'sub_1234567890';
      const updateData = {
        plan_id: 'premium',
        proration_behavior: 'create_prorations',
      };

      const mockUpdatedSubscription = {
        id: 'sub_1234567890',
        status: 'active',
        plan: {
          id: 'premium',
          name: 'Premium Plan',
          amount: 9999,
        },
      };

      (apiClient.put as jest.Mock).mockResolvedValue({
        data: mockUpdatedSubscription,
      });

      const result = await PaymentService.updateSubscription(subscriptionId, updateData);

      expect(apiClient.put).toHaveBeenCalledWith(
        `/payments/subscription/${subscriptionId}/`,
        updateData
      );
      expect(result).toEqual(mockUpdatedSubscription);
    });
  });

  describe('Usage and Limits', () => {
    it('should fetch usage limits successfully', async () => {
      const mockUsage = {
        current_plan: {
          id: 'basic',
          name: 'Basic Plan',
          max_transactions: 1000,
          max_bank_accounts: 2,
          max_ai_requests: 100,
        },
        current_usage: {
          transactions: 450,
          bank_accounts: 1,
          ai_requests: 75,
        },
        usage_percentage: {
          transactions: 45,
          bank_accounts: 50,
          ai_requests: 75,
        },
        warnings: [],
      };

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockUsage });

      const result = await PaymentService.getUsageLimits();

      expect(apiClient.get).toHaveBeenCalledWith('/payments/usage-limits/');
      expect(result).toEqual(mockUsage);
    });

    it('should handle usage limits with warnings', async () => {
      const mockUsage = {
        current_plan: {
          id: 'basic',
          name: 'Basic Plan',
          max_transactions: 1000,
          max_bank_accounts: 2,
          max_ai_requests: 100,
        },
        current_usage: {
          transactions: 950,
          bank_accounts: 2,
          ai_requests: 95,
        },
        usage_percentage: {
          transactions: 95,
          bank_accounts: 100,
          ai_requests: 95,
        },
        warnings: [
          {
            type: 'transactions',
            message: 'You are approaching your transaction limit',
            severity: 'warning',
          },
          {
            type: 'bank_accounts',
            message: 'You have reached your bank account limit',
            severity: 'error',
          },
        ],
      };

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockUsage });

      const result = await PaymentService.getUsageLimits();

      expect(result.warnings).toHaveLength(2);
      expect(result.warnings[0].type).toBe('transactions');
      expect(result.warnings[1].severity).toBe('error');
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      const apiError = {
        response: {
          status: 400,
          data: {
            error: 'Invalid request',
            details: 'Plan ID is required',
          },
        },
      };

      (apiClient.get as jest.Mock).mockRejectedValue(apiError);

      await expect(PaymentService.getSubscriptionPlans()).rejects.toEqual(apiError);
    });

    it('should handle network errors', async () => {
      const networkError = new Error('Network Error');
      (apiClient.get as jest.Mock).mockRejectedValue(networkError);

      await expect(PaymentService.getSubscriptionPlans()).rejects.toThrow(
        'Network Error'
      );
    });
  });
});