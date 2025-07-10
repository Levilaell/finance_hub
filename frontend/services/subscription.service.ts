import { apiClient } from '@/lib/api-client';
import { SubscriptionPlan } from '@/types';

export interface UpgradeSubscriptionData {
  plan_id: string;
  billing_cycle: string;
}

export const subscriptionService = {
  // Get all public subscription plans
  async getPublicPlans(): Promise<SubscriptionPlan[]> {
    const response = await apiClient.get('/companies/public/plans/');
    return response.data;
  },

  // Get current user's available plans
  async getAvailablePlans(): Promise<SubscriptionPlan[]> {
    const response = await apiClient.get('/companies/subscription/plans/');
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