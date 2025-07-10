import { apiClient } from '@/lib/api-client';

export interface SubscriptionPlan {
  id: number;
  name: string;
  slug: string;
  plan_type: 'starter' | 'pro' | 'enterprise';
  price_monthly: string;
  price_yearly: string;
  max_users: number;
  max_bank_accounts: number;
  max_transactions: number;
  has_ai_categorization: boolean;
  has_advanced_reports: boolean;
  has_api_access: boolean;
  has_accountant_access: boolean;
  is_active: boolean;
}

export interface UpgradeSubscriptionData {
  plan_slug: string;
  payment_method_id: string;
  billing_cycle: 'monthly' | 'yearly';
}

export const subscriptionService = {
  // Get all public subscription plans
  async getPublicPlans(): Promise<SubscriptionPlan[]> {
    const response = await apiClient.get<SubscriptionPlan[]>('/companies/public/plans/');
    return response.data;
  },

  // Get current user's available plans
  async getAvailablePlans(): Promise<SubscriptionPlan[]> {
    const response = await apiClient.get<SubscriptionPlan[]>('/companies/subscription/plans/');
    return response.data;
  },

  // Upgrade subscription
  async upgradeSubscription(data: UpgradeSubscriptionData) {
    const response = await apiClient.post('/companies/subscription/upgrade/', data);
    return response.data;
  },

  // Cancel subscription
  async cancelSubscription() {
    const response = await apiClient.post('/companies/subscription/cancel/');
    return response.data;
  },
};