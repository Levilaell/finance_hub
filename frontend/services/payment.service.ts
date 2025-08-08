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
import { apiClient } from '@/lib/api-client';

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
  private async get<T>(url: string, params?: any): Promise<T> {
    const response = params ? await apiClient.get(url, params) : await apiClient.get(url);
    return (response as any).data;
  }

  private async post<T>(url: string, data?: any): Promise<T> {
    const response = await apiClient.post(url, data);
    return (response as any).data;
  }

  private async put<T>(url: string, data: any): Promise<T> {
    const response = await apiClient.put(url, data);
    return (response as any).data;
  }

  private async patch<T>(url: string, data: any): Promise<T> {
    const response = await apiClient.patch(url, data);
    return (response as any).data;
  }

  private async delete<T>(url: string): Promise<T> {
    const response = await apiClient.delete(url);
    return (response as any).data;
  }
  // Subscription Plans
  async getSubscriptionPlans(): Promise<SubscriptionPlan[]> {
    return this.get<SubscriptionPlan[]>('/payments/subscription-plans/');
  }

  // Subscription Status
  async getSubscriptionStatus(): Promise<SubscriptionStatus> {
    return this.get<SubscriptionStatus>('/payments/subscription/status/');
  }

  async cancelSubscription(subscriptionId: string, cancelData: any): Promise<{ status: string; message: string; subscription: Subscription }> {
    return this.post<{ status: string; message: string; subscription: Subscription }>(`/payments/subscription/${subscriptionId}/cancel/`, cancelData);
  }

  // Checkout Flow
  async createCheckoutSession(data: CheckoutSessionRequest): Promise<CheckoutSessionResponse> {
    return this.post<CheckoutSessionResponse>('/payments/checkout-sessions/', data);
  }

  async validatePayment(sessionId: string): Promise<{ status: string; subscription?: Subscription; message?: string }> {
    return this.post<{ status: string; subscription?: Subscription; message?: string }>('/payments/checkout/validate/', { session_id: sessionId });
  }

  // Payment Methods
  async getPaymentMethods(): Promise<PaymentMethod[]> {
    return this.get<PaymentMethod[]>('/payments/payment-methods/');
  }

  async createPaymentMethod(data: CreatePaymentMethodRequest): Promise<PaymentMethod> {
    return this.post<PaymentMethod>('/payments/payment-methods/', data);
  }

  async updatePaymentMethod(id: number, data: { is_default: boolean }): Promise<PaymentMethod> {
    return this.patch<PaymentMethod>(`/payments/payment-methods/${id}/`, data);
  }

  async deletePaymentMethod(id: number): Promise<any> {
    return this.delete(`/payments/payment-methods/${id}/`);
  }

  // Payment History
  async getPaymentHistory(filters?: any): Promise<any> {
    return this.get<any>('/payments/history/', { params: filters });
  }

  // Additional methods expected by tests
  async getCurrentSubscription(): Promise<Subscription> {
    return this.get<Subscription>('/payments/subscription/current/');
  }

  async updateSubscription(subscriptionId: string, updateData: any): Promise<Subscription> {
    return this.put<Subscription>(`/payments/subscription/${subscriptionId}/`, updateData);
  }

  async getUsageLimits(): Promise<any> {
    return this.get<any>('/payments/usage-limits/');
  }

  // Payment Intents (expected by tests)
  async createPaymentIntent(data: any): Promise<any> {
    return this.post<any>('/payments/payment-intents/', data);
  }

  async confirmPaymentIntent(paymentIntentId: string, confirmData: any): Promise<any> {
    return this.post<any>(`/payments/payment-intents/${paymentIntentId}/confirm/`, confirmData);
  }
}

const paymentService = new PaymentService();
export { paymentService as PaymentService };
export default paymentService;