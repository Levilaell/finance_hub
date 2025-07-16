import apiClient from '@/lib/api-client';
import { SubscriptionPlan, UsageLimits } from '@/types';

export interface UpgradeSubscriptionData {
  plan_id: string;
  billing_cycle: string;
}

export interface SubscriptionStatus {
  subscription_status: string;
  has_payment_method: boolean;
  trial_days_left: number;
  plan: SubscriptionPlan | null;
  requires_payment_setup: boolean;
  trial_ends_at: string | null;
  next_billing_date: string | null;
}

export const subscriptionService = {
  // Get all public subscription plans
  async getPublicPlans(): Promise<SubscriptionPlan[]> {
    const response = await apiClient.get('/api/companies/public/plans/');
    return response;
  },

  // Get current user's available plans
  async getAvailablePlans(): Promise<SubscriptionPlan[]> {
    const response = await apiClient.get('/api/companies/subscription/plans/');
    return response;
  },

  // Upgrade subscription
  async upgradeSubscription(data: UpgradeSubscriptionData) {
    const response = await apiClient.post('/api/companies/subscription/upgrade/', data);
    return response;
  },

  // Cancel subscription
  async cancelSubscription() {
    const response = await apiClient.post('/api/companies/subscription/cancel/');
    return response;
  },

  // Get subscription status
  async getSubscriptionStatus(): Promise<SubscriptionStatus> {
    const response = await apiClient.get('/api/payments/subscription-status/');
    return response;
  },

  // Get usage limits
  async getUsageLimits(): Promise<UsageLimits> {
    // This might be part of the company profile or a separate endpoint
    const response = await apiClient.get('/api/companies/usage-limits/');
    return response;
  },
};