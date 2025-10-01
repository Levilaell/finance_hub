import apiClient from "@/lib/api-client";

export interface SubscriptionStatus {
  status: 'trialing' | 'active' | 'past_due' | 'canceled' | 'incomplete' | 'incomplete_expired' | 'unpaid' | 'none';
  trial_end?: string;
  current_period_end?: string;
  cancel_at_period_end?: boolean;
  canceled_at?: string;
  days_until_renewal?: number;
  amount?: number;
  currency?: string;
  requires_action?: boolean;
  message?: string;
  payment_method?: {
    last4?: string;
    brand?: string;
  };
}

export interface StripeConfig {
  publishable_key: string;
}

class SubscriptionService {
  async getConfig(): Promise<StripeConfig> {
    return apiClient.get<StripeConfig>("/api/subscriptions/config/");
  }

  async getStatus(): Promise<SubscriptionStatus> {
    return apiClient.get<SubscriptionStatus>("/api/subscriptions/status/");
  }

  async createCheckoutSession(successUrl?: string, cancelUrl?: string) {
    return apiClient.post<{ checkout_url: string; session_id: string }>("/api/subscriptions/checkout/", {
      success_url: successUrl,
      cancel_url: cancelUrl,
    });
  }

  async createPortalSession(returnUrl?: string) {
    return apiClient.post<{ url: string }>("/api/subscriptions/portal/", {
      return_url: returnUrl || `${window.location.origin}/settings?tab=subscription`,
    });
  }
}

export const subscriptionService = new SubscriptionService();
