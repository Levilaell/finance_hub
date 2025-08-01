/**
 * DEPRECATED - Subscription functionality moved to unified-subscription.service.ts
 * 
 * This service contains both subscription and payment functionality that was causing
 * API contract confusion. The subscription functionality has been moved to the
 * unified service. Payment processing functionality will be re-implemented when
 * the backend payment endpoints are ready.
 * 
 * For subscription functionality, use:
 * import { subscriptionService } from '@/services/unified-subscription.service'
 */
import api from './api';

export interface SubscriptionPlan {
  id: number;
  name: string;
  display_name: string;
  monthly_price: number;
  yearly_price: number;
  yearly_savings: number;
  max_transactions: number;
  max_bank_accounts: number;
  max_ai_requests: number;
  features: Record<string, boolean>;
}

export interface Subscription {
  id: number;
  plan: SubscriptionPlan;
  status: 'trial' | 'active' | 'cancelled' | 'expired' | 'past_due';
  billing_period: 'monthly' | 'yearly';
  is_active: boolean;
  is_trial: boolean;
  trial_days_remaining: number;
  trial_ends_at: string | null;
  current_period_start: string | null;
  current_period_end: string | null;
  cancelled_at: string | null;
  created_at: string;
}

export interface UsageData {
  type: 'transaction' | 'bank_account' | 'ai_request';
  count: number;
  limit: number;
  percentage: number;
  period_start: string;
  period_end: string;
}

export interface SubscriptionStatus {
  id: number;
  name: string;
  subscription: Subscription | null;
  current_usage: {
    transaction: UsageData;
    bank_account: UsageData;
    ai_request: UsageData;
  };
}

export interface PaymentMethod {
  id: number;
  type: 'card' | 'bank_account' | 'pix';
  is_default: boolean;
  brand?: string;
  last4?: string;
  exp_month?: number;
  exp_year?: number;
  display_name: string;
  created_at: string;
}

export interface Payment {
  id: number;
  amount: number;
  currency: string;
  status: string;
  description: string;
  gateway: string;
  payment_method: PaymentMethod | null;
  created_at: string;
  paid_at: string | null;
}

export interface CheckoutSessionRequest {
  plan_id: number;
  billing_period: 'monthly' | 'yearly';
  success_url: string;
  cancel_url: string;
}

export interface CheckoutSessionResponse {
  session_id: string;
  checkout_url: string;
}

export interface CreatePaymentMethodRequest {
  type: 'card' | 'bank_account' | 'pix';
  token: string;
  is_default?: boolean;
  brand?: string;
  last4?: string;
  exp_month?: number;
  exp_year?: number;
}

class PaymentService {
  // Subscription Plans
  async getSubscriptionPlans(): Promise<SubscriptionPlan[]> {
    const response = await api.get('/payments/plans/');
    return response.data;
  }

  // Subscription Status
  async getSubscriptionStatus(): Promise<SubscriptionStatus> {
    const response = await api.get('/payments/subscription/status/');
    return response.data;
  }

  async cancelSubscription(): Promise<{ status: string; message: string; subscription: Subscription }> {
    const response = await api.post('/payments/subscription/cancel/');
    return response.data;
  }

  // Checkout Flow
  async createCheckoutSession(data: CheckoutSessionRequest): Promise<CheckoutSessionResponse> {
    const response = await api.post('/payments/checkout/create/', data);
    return response.data;
  }

  async validatePayment(sessionId: string): Promise<{ status: string; subscription?: Subscription; message?: string }> {
    const response = await api.post('/payments/checkout/validate/', { session_id: sessionId });
    return response.data;
  }

  // Payment Methods
  async getPaymentMethods(): Promise<PaymentMethod[]> {
    const response = await api.get('/payments/payment-methods/');
    return response.data;
  }

  async createPaymentMethod(data: CreatePaymentMethodRequest): Promise<PaymentMethod> {
    const response = await api.post('/payments/payment-methods/', data);
    return response.data;
  }

  async updatePaymentMethod(id: number, data: { is_default: boolean }): Promise<PaymentMethod> {
    const response = await api.patch(`/payments/payment-methods/${id}/`, data);
    return response.data;
  }

  async deletePaymentMethod(id: number): Promise<void> {
    await api.delete(`/payments/payment-methods/${id}/`);
  }

  // Payment History
  async getPaymentHistory(): Promise<Payment[]> {
    const response = await api.get('/payments/payments/');
    return response.data;
  }
}

export default new PaymentService();