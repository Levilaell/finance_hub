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
    isExpiringSoon: daysRemaining <= 3 && daysRemaining > 0,
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
  const statusMap = {
    active: {
      label: 'Ativa',
      color: 'bg-green-100 text-green-800',
      description: 'Sua assinatura está ativa'
    },
    trialing: {
      label: 'Período de Teste',
      color: 'bg-blue-100 text-blue-800',
      description: 'Você está no período de teste gratuito'
    },
    trial: {
      label: 'Período de Teste',
      color: 'bg-blue-100 text-blue-800',
      description: 'Você está no período de teste gratuito'
    },
    past_due: {
      label: 'Em Atraso',
      color: 'bg-red-100 text-red-800',
      description: 'Pagamento em atraso'
    },
    canceled: {
      label: 'Cancelada',
      color: 'bg-gray-100 text-gray-800',
      description: 'Assinatura cancelada'
    },
    cancelled: {
      label: 'Cancelada',
      color: 'bg-gray-100 text-gray-800',
      description: 'Assinatura cancelada'
    },
    cancelling: {
      label: 'Cancelando',
      color: 'bg-orange-100 text-orange-800',
      description: 'Assinatura sendo cancelada'
    },
    expired: {
      label: 'Expirada',
      color: 'bg-red-100 text-red-800',
      description: 'Assinatura expirada'
    },
    suspended: {
      label: 'Suspensa',
      color: 'bg-red-100 text-red-800',
      description: 'Assinatura suspensa'
    },
    unpaid: {
      label: 'Não Paga',
      color: 'bg-red-100 text-red-800',
      description: 'Pagamento pendente'
    }
  };

  return statusMap[status as keyof typeof statusMap] || {
    label: status,
    color: 'bg-gray-100 text-gray-800',
    description: 'Status desconhecido'
  };
}

/**
 * Format currency value
 */
export function formatCurrency(amount: number, currency: string = 'BRL'): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency,
  }).format(amount);
}

/**
 * Format date for display
 */
export function formatDate(date: Date | string): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return dateObj.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
}

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