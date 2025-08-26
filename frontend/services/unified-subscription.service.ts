/**
 * Unified Subscription Service - Production Ready
 * 
 * This service consolidates subscription and payment functionality with proper API routing:
 * - Subscription data: /api/companies/ endpoints  
 * - Payment processing: /api/payments/ endpoints (when implemented)
 * 
 * Replaces both subscription.service.ts and payment.service.ts to eliminate confusion.
 */
import { apiClient } from '@/lib/api-client';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

export interface SubscriptionPlan {
  id: number;
  name: string;
  slug: string;
  price_monthly: number | string; // Django DecimalField serializes as string
  price_yearly: number | string;   // Django DecimalField serializes as string
  yearly_discount?: number;
  max_transactions: number;
  max_bank_accounts: number;
  max_ai_requests: number;
  has_ai_insights: boolean;
  has_advanced_reports: boolean;
  stripe_price_id_monthly?: string;
  stripe_price_id_yearly?: string;
  is_active: boolean;
  display_order: number;
}

export interface Company {
  id: string;
  name: string;
  owner_email: string;
  subscription_plan: SubscriptionPlan | null;
  subscription_status: 'trial' | 'active' | 'cancelled' | 'expired' | 'suspended';
  billing_cycle: 'monthly' | 'yearly';
  trial_ends_at: string | null;
  is_trial_active: boolean;
  days_until_trial_ends: number;
  current_month_transactions: number;
  current_month_ai_requests: number;
  created_at: string;
}

export interface UsageLimits {
  transactions: {
    used: number;
    limit: number;
    percentage: number;
  };
  bank_accounts: {
    used: number;
    limit: number;
    percentage: number;
  };
  ai_requests: {
    used: number;
    limit: number;
    percentage: number;
  };
}

export interface SubscriptionStatus {
  subscription_status: string;
  plan: SubscriptionPlan | null;
  trial_days_left: number;
  trial_ends_at: string | null;
  requires_payment_setup: boolean;
  has_payment_method: boolean;
}

// Payment-related interfaces (for future implementation)
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

// ============================================================================
// UNIFIED SUBSCRIPTION SERVICE
// ============================================================================

class UnifiedSubscriptionService {
  
  // -------------------------------------------------------------------------
  // SUBSCRIPTION MANAGEMENT (Companies API)
  // -------------------------------------------------------------------------
  
  /**
   * Get available subscription plans
   */
  async getSubscriptionPlans(): Promise<SubscriptionPlan[]> {
    return await apiClient.get<SubscriptionPlan[]>('/api/companies/plans/');
  }

  /**
   * Get current company details
   */
  async getCompanyDetails(): Promise<Company> {
    return await apiClient.get<Company>('/api/companies/detail/');
  }

  /**
   * Get current usage limits and status
   */
  async getUsageLimits(): Promise<UsageLimits> {
    return await apiClient.get<UsageLimits>('/api/companies/usage-limits/');
  }

  /**
   * Get comprehensive subscription status
   */
  async getSubscriptionStatus(): Promise<SubscriptionStatus> {
    return await apiClient.get<SubscriptionStatus>('/api/companies/subscription-status/');
  }

  // -------------------------------------------------------------------------
  // PAYMENT MANAGEMENT (Payments API)
  // -------------------------------------------------------------------------
  
  /**
   * Create checkout session for subscription upgrade
   */
  async createCheckoutSession(data: CheckoutSessionRequest): Promise<CheckoutSessionResponse> {
    return await apiClient.post<CheckoutSessionResponse>('/api/payments/checkout/create/', data);
  }

  /**
   * Validate payment after checkout
   */
  async validatePayment(sessionId: string): Promise<{ status: string; message?: string; subscription?: any }> {
    return await apiClient.post<{ status: string; message?: string; subscription?: any }>('/api/payments/checkout/validate/', {
      session_id: sessionId
    });
  }

  /**
   * Cancel subscription
   */
  async cancelSubscription(): Promise<{ status: string; message: string }> {
    return await apiClient.post<{ status: string; message: string }>('/api/payments/subscription/cancel/', {});
  }

  /**
   * Get payment methods
   */
  async getPaymentMethods(): Promise<PaymentMethod[]> {
    return await apiClient.get<PaymentMethod[]>('/api/payments/payment-methods/');
  }

  /**
   * Get payment history
   */
  async getPaymentHistory(): Promise<Payment[]> {
    return await apiClient.get<Payment[]>('/api/payments/payments/');
  }

  /**
   * Create new payment method
   */
  async createPaymentMethod(data: CreatePaymentMethodRequest): Promise<PaymentMethod> {
    return await apiClient.post<PaymentMethod>('/api/payments/payment-methods/', data);
  }

  /**
   * Delete payment method
   */
  async deletePaymentMethod(paymentMethodId: number): Promise<{ success: boolean; message: string }> {
    return await apiClient.delete<{ success: boolean; message: string }>(`/api/payments/payment-methods/${paymentMethodId}/`);
  }

  /**
   * Update payment method (set as default, etc.)
   */
  async updatePaymentMethod(paymentMethodId: number, data: Partial<PaymentMethod>): Promise<PaymentMethod> {
    return await apiClient.patch<PaymentMethod>(`/api/payments/payment-methods/${paymentMethodId}/`, data);
  }

  // -------------------------------------------------------------------------
  // UTILITY METHODS
  // -------------------------------------------------------------------------

  /**
   * Check if user can use specific feature based on plan
   */
  canUseFeature(plan: SubscriptionPlan | null, feature: string): boolean {
    if (!plan) return false;
    
    switch (feature) {
      case 'ai_insights':
        return plan.has_ai_insights;
      case 'advanced_reports':
        return plan.has_advanced_reports;
      default:
        return false;
    }
  }

  /**
   * Check if usage limit is reached
   */
  isUsageLimitReached(usage: UsageLimits, type: keyof UsageLimits): boolean {
    const limit = usage[type];
    return limit.percentage >= 100;
  }

  /**
   * Get usage warning level (none, warning, critical)
   */
  getUsageWarningLevel(percentage: number): 'none' | 'warning' | 'critical' {
    if (percentage >= 100) return 'critical';
    if (percentage >= 80) return 'warning';
    return 'none';
  }
}

// Export singleton instance
export const subscriptionService = new UnifiedSubscriptionService();
export default subscriptionService;

// ============================================================================
// MIGRATION NOTES
// ============================================================================

/**
 * MIGRATION FROM OLD SERVICES:
 * 
 * 1. Replace imports:
 *    - import { subscriptionService } from '@/services/unified-subscription.service'
 *    - import paymentService from '@/services/payment.service' 
 *    + import { subscriptionService } from '@/services/unified-subscription.service'
 * 
 * 2. Update method calls:
 *    - paymentService.getSubscriptionPlans() → subscriptionService.getSubscriptionPlans()
 *    - paymentService.getSubscriptionStatus() → subscriptionService.getSubscriptionStatus()
 * 
 * 3. Payment methods now available:
 *    - createCheckoutSession, validatePayment, cancelSubscription are fully functional
 *    - All payment endpoints are integrated with backend API
 * 
 * 4. Interface changes:
 *    - SubscriptionPlan.id is now number (was string)
 *    - Added utility methods for feature/usage checking
 */