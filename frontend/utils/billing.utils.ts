/**
 * Utility functions for billing and subscription management
 */

export interface TrialInfo {
  isActive: boolean;
  daysRemaining: number;
  endDate: Date | null;
  isExpired: boolean;
  isExpiringSoon: boolean; // less than 3 days
}

export interface BillingInfo {
  nextBillingDate: Date | null;
  subscriptionStartDate: Date | null;
  subscriptionEndDate: Date | null;
  daysUntilNextBilling: number | null;
}

/**
 * Calculate trial information based on trial end date
 */
export function calculateTrialInfo(trialEndsAt: string | null): TrialInfo {
  if (!trialEndsAt) {
    return {
      isActive: false,
      daysRemaining: 0,
      endDate: null,
      isExpired: false,
      isExpiringSoon: false,
    };
  }

  const endDate = new Date(trialEndsAt);
  const now = new Date();
  const diffTime = endDate.getTime() - now.getTime();
  const daysRemaining = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  return {
    isActive: daysRemaining > 0,
    daysRemaining: Math.max(0, daysRemaining),
    endDate,
    isExpired: daysRemaining <= 0,
    isExpiringSoon: daysRemaining <= TRIAL_WARNING_DAYS && daysRemaining > 0,
  };
}

/**
 * Calculate billing information based on subscription dates
 */
export function calculateBillingInfo(
  nextBillingDate: string | null,
  subscriptionStartDate: string | null,
  subscriptionEndDate: string | null
): BillingInfo {
  return {
    nextBillingDate: nextBillingDate ? new Date(nextBillingDate) : null,
    subscriptionStartDate: subscriptionStartDate ? new Date(subscriptionStartDate) : null,
    subscriptionEndDate: subscriptionEndDate ? new Date(subscriptionEndDate) : null,
    daysUntilNextBilling: nextBillingDate 
      ? Math.ceil((new Date(nextBillingDate).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))
      : null,
  };
}

/**
 * Get subscription status display info
 */
export function getSubscriptionStatusInfo(status: string) {
  return SUBSCRIPTION_STATUS_INFO[status as keyof typeof SUBSCRIPTION_STATUS_INFO] || {
    label: status,
    color: 'bg-gray-100 text-gray-800',
    description: 'Status desconhecido'
  };
}

// Re-export shared formatting functions from lib/utils
export { formatCurrency, formatDate } from '@/lib/utils';

import { SUBSCRIPTION_STATUS_INFO, TRIAL_WARNING_DAYS } from '@/constants/billing';

/**
 * Check if user should see upgrade prompt
 */
export function shouldShowUpgradePrompt(
  subscriptionStatus: string,
  trialInfo: TrialInfo
): boolean {
  return subscriptionStatus === 'trialing' && 
         (trialInfo.isExpiringSoon || trialInfo.isExpired);
}