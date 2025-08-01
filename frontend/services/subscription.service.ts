/**
 * DEPRECATED - Use unified-subscription.service.ts instead
 * 
 * This service is deprecated and will be removed in a future version.
 * Please migrate to the unified subscription service.
 * 
 * Migration: import { subscriptionService } from '@/services/unified-subscription.service'
 */
import { apiClient } from '@/lib/api-client';

export interface SubscriptionPlan {
  id: string;
  name: string;
  slug: string;
  price_monthly: number;
  price_yearly: number;
  yearly_discount: number;
  max_transactions: number;
  max_bank_accounts: number;
  max_ai_requests: number;
  has_ai_insights: boolean;
  has_advanced_reports: boolean;
}

export interface Company {
  id: string;
  name: string;
  owner_email: string;
  subscription_plan: SubscriptionPlan | null;
  subscription_status: 'trial' | 'active' | 'cancelled' | 'expired';
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

export const subscriptionService = {
  // Get available plans
  async getPlans(): Promise<SubscriptionPlan[]> {
    return await apiClient.get<SubscriptionPlan[]>('/api/companies/plans/');
  },

  // Get company details
  async getCompanyDetails(): Promise<Company> {
    return await apiClient.get<Company>('/api/companies/detail/');
  },

  // Get usage limits
  async getUsageLimits(): Promise<UsageLimits> {
    return await apiClient.get<UsageLimits>('/api/companies/usage-limits/');
  },

  // Get subscription status
  async getSubscriptionStatus(): Promise<SubscriptionStatus> {
    return await apiClient.get<SubscriptionStatus>('/api/companies/subscription-status/');
  },

  // Note: Payment-related methods moved to payment.service.ts
  // - upgradeSubscription
  // - cancelSubscription
  // - addPaymentMethod
  // - etc.
};