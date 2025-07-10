import { apiClient } from '@/lib/api-client';
import { SubscriptionPlan } from '@/types';

export interface UpgradeSubscriptionData {
  plan_id: string;
  billing_cycle: string;
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
};