import { apiClient } from '@/lib/api-client';

export interface BillingTransaction {
  id: string;
  transaction_type: string;
  amount: number;
  currency: string;
  status: 'paid' | 'pending' | 'failed' | 'canceled' | 'refunded';
  description: string;
  invoice_number: string;
  invoice_url?: string;
  transaction_date: string;
  due_date?: string;
  paid_at?: string;
  payment_method_display: string;
  plan_name?: string;
  created_at: string;
}

export interface PaymentMethod {
  id: string;
  payment_type: 'credit_card' | 'debit_card' | 'pix' | 'bank_transfer';
  card_brand?: string;
  last_four?: string;
  exp_month?: number;
  exp_year?: number;
  cardholder_name?: string;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
}

export interface AddPaymentMethodData {
  payment_type: string;
  card_number?: string;
  exp_month?: number;
  exp_year?: number;
  cvc?: string;
  cardholder_name?: string;
}

export const billingService = {
  // Payment History
  async getPaymentHistory(params?: {
    status?: string;
    search?: string;
  }): Promise<BillingTransaction[]> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.append('status', params.status);
    if (params?.search) searchParams.append('search', params.search);
    
    const response = await apiClient.get<BillingTransaction[]>(`/api/companies/billing/history/?${searchParams}`);
    return response;
  },

  async downloadInvoice(paymentId: string): Promise<{ download_url: string }> {
    const response = await apiClient.get<{ download_url: string }>(`/api/companies/billing/invoices/${paymentId}/`);
    return response;
  },

  // Payment Methods
  async getPaymentMethods(): Promise<PaymentMethod[]> {
    const response = await apiClient.get<PaymentMethod[]>('/api/companies/billing/payment-methods/');
    return response;
  },

  async addPaymentMethod(data: AddPaymentMethodData): Promise<PaymentMethod> {
    const response = await apiClient.post<PaymentMethod>('/api/companies/billing/payment-methods/', data);
    return response;
  },

  async setDefaultPaymentMethod(paymentMethodId: string): Promise<void> {
    await apiClient.post(`/api/companies/billing/payment-methods/${paymentMethodId}/`);
  },

  async deletePaymentMethod(paymentMethodId: string): Promise<void> {
    await apiClient.delete(`/api/companies/billing/payment-methods/${paymentMethodId}/`);
  },
};