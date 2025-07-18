import apiClient from '@/lib/api-client';

export interface CheckoutSessionData {
  plan_slug: string;
  billing_cycle: 'monthly' | 'yearly';
}

export interface CheckoutSessionResponse {
  checkout_url: string;
  session_id?: string;
  preference_id?: string;
}

export interface PaymentValidationData {
  session_id?: string;
  payment_id?: string;
}

export interface PaymentValidationResponse {
  status: 'success' | 'pending' | 'failed';
  message: string;
}

export const paymentService = {
  // Create checkout session for immediate payment
  async createCheckoutSession(data: CheckoutSessionData): Promise<CheckoutSessionResponse> {
    const response = await apiClient.post<CheckoutSessionResponse>('/api/payments/checkout/create/', data);
    return response;
  },

  // Validate payment after returning from checkout
  async validatePayment(data: PaymentValidationData): Promise<PaymentValidationResponse> {
    const response = await apiClient.post<PaymentValidationResponse>('/api/payments/checkout/validate/', data);
    return response;
  },
};