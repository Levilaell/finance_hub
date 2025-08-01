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
  price_monthly: number;
  price_yearly: number;
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
  // PAYMENT MANAGEMENT (Future Payments API - placeholder implementations)
  // -------------------------------------------------------------------------
  
  /**
   * Create checkout session for subscription upgrade
   * TODO: Implement when payments app endpoints are ready
   */
  async createCheckoutSession(data: CheckoutSessionRequest): Promise<CheckoutSessionResponse> {
    // For now, return mock data or throw not implemented
    throw new Error('Payment endpoints not yet implemented. Use companies API for subscription management.');
  }

  /**
   * Validate payment after checkout
   * TODO: Implement when payments app endpoints are ready
   */
  async validatePayment(sessionId: string): Promise<{ status: string; message?: string }> {
    throw new Error('Payment endpoints not yet implemented. Use companies API for subscription management.');
  }

  /**
   * Cancel subscription
   * TODO: Implement when payments app endpoints are ready
   */
  async cancelSubscription(): Promise<{ status: string; message: string }> {
    throw new Error('Payment endpoints not yet implemented. Use companies API for subscription management.');
  }

  /**
   * Get payment methods
   * TODO: Implement when payments app endpoints are ready
   */
  async getPaymentMethods(): Promise<PaymentMethod[]> {
    return [];
  }

  /**
   * Get payment history
   * TODO: Implement when payments app endpoints are ready
   */
  async getPaymentHistory(): Promise<Payment[]> {
    return [];
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
 *    - import { subscriptionService } from '@/services/subscription.service'
 *    - import paymentService from '@/services/payment.service' 
 *    + import { subscriptionService } from '@/services/unified-subscription.service'
 * 
 * 2. Update method calls:
 *    - paymentService.getSubscriptionPlans() → subscriptionService.getSubscriptionPlans()
 *    - paymentService.getSubscriptionStatus() → subscriptionService.getSubscriptionStatus()
 * 
 * 3. Payment methods temporarily unavailable:
 *    - createCheckoutSession, validatePayment, cancelSubscription will throw errors
 *    - Implement these when payments app endpoints are ready
 * 
 * 4. Interface changes:
 *    - SubscriptionPlan.id is now number (was string)
 *    - Added utility methods for feature/usage checking
 */