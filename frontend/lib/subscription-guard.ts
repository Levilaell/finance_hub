import { Company } from '@/types';
import { toast } from 'sonner';

export interface SubscriptionError {
  type: 'trial_expired' | 'subscription_expired' | 'limit_reached' | 'feature_not_available';
  message: string;
  redirectUrl?: string;
}

export class SubscriptionGuard {
  static checkTrialStatus(company: Company | null): SubscriptionError | null {
    if (!company) return null;
    
    // Check if trial has expired
    if (company.subscription_status === 'trial' && company.trial_ends_at) {
      const trialEndDate = new Date(company.trial_ends_at);
      const now = new Date();
      
      if (now > trialEndDate) {
        return {
          type: 'trial_expired',
          message: 'Seu período de teste expirou. Escolha um plano para continuar.',
          redirectUrl: '/dashboard/subscription/upgrade'
        };
      }
    }
    
    // Check if subscription is expired or suspended
    if (['expired', 'suspended', 'cancelled'].includes(company.subscription_status)) {
      return {
        type: 'subscription_expired',
        message: 'Sua assinatura está inativa. Regularize para continuar usando o sistema.',
        redirectUrl: '/dashboard/subscription'
      };
    }
    
    return null;
  }
  
  static checkFeatureAccess(company: Company | null, feature: string): SubscriptionError | null {
    if (!company || !company.subscription_plan) return null;
    
    const plan = company.subscription_plan;
    
    // Check specific features based on plan
    const featureChecks: Record<string, boolean> = {
      'ai_categorization': plan.has_ai_categorization,
      'advanced_reports': plan.has_advanced_reports,
      'api_access': plan.has_api_access,
      'accountant_access': plan.has_accountant_access,
      'priority_support': plan.has_priority_support,
    };
    
    if (feature in featureChecks && !featureChecks[feature]) {
      return {
        type: 'feature_not_available',
        message: `Este recurso não está disponível no plano ${plan.name}. Faça upgrade para acessar.`,
        redirectUrl: '/dashboard/subscription/upgrade'
      };
    }
    
    return null;
  }
  
  static checkUsageLimits(company: Company | null, limitType: string, currentUsage: number): SubscriptionError | null {
    if (!company || !company.subscription_plan) return null;
    
    const plan = company.subscription_plan;
    const limits: Record<string, number> = {
      'transactions': plan.max_transactions,
      'bank_accounts': plan.max_bank_accounts,
      'ai_requests': plan.max_ai_requests_per_month,
    };
    
    if (limitType in limits) {
      const limit = limits[limitType];
      if (currentUsage >= limit) {
        return {
          type: 'limit_reached',
          message: `Você atingiu o limite de ${limit} ${limitType} do plano ${plan.name}. Faça upgrade para continuar.`,
          redirectUrl: '/dashboard/subscription/upgrade'
        };
      }
    }
    
    return null;
  }
  
  static handleSubscriptionError(error: SubscriptionError | null, router?: any) {
    if (!error) return false;
    
    toast.error(error.message, {
      duration: 5000,
      action: error.redirectUrl ? {
        label: 'Resolver',
        onClick: () => {
          if (router && error.redirectUrl) {
            router.push(error.redirectUrl);
          } else if (error.redirectUrl) {
            window.location.href = error.redirectUrl;
          }
        }
      } : undefined
    });
    
    return true;
  }
  
  static async checkApiResponse(response: Response) {
    // Check for payment required status
    if (response.status === 402) {
      const data = await response.json();
      const error: SubscriptionError = {
        type: data.error?.includes('trial') ? 'trial_expired' : 'subscription_expired',
        message: data.message || 'Ação requer pagamento',
        redirectUrl: data.redirect || '/dashboard/subscription'
      };
      
      this.handleSubscriptionError(error);
      throw new Error(error.message);
    }
  }
}