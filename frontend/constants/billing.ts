/**
 * Billing and subscription constants
 */

export const SUBSCRIPTION_STATUS = {
  ACTIVE: 'active',
  TRIALING: 'trialing',
  TRIAL: 'trial',
  PAST_DUE: 'past_due',
  CANCELED: 'canceled',
  CANCELLED: 'cancelled',
  CANCELLING: 'cancelling',
  EXPIRED: 'expired',
  SUSPENDED: 'suspended',
  UNPAID: 'unpaid'
} as const;

export const SUBSCRIPTION_STATUS_INFO = {
  [SUBSCRIPTION_STATUS.ACTIVE]: {
    label: 'Ativa',
    color: 'bg-green-100 text-green-800',
    description: 'Sua assinatura está ativa'
  },
  [SUBSCRIPTION_STATUS.TRIALING]: {
    label: 'Período de Teste',
    color: 'bg-blue-100 text-blue-800',
    description: 'Você está no período de teste gratuito'
  },
  [SUBSCRIPTION_STATUS.TRIAL]: {
    label: 'Período de Teste',
    color: 'bg-blue-100 text-blue-800',
    description: 'Você está no período de teste gratuito'
  },
  [SUBSCRIPTION_STATUS.PAST_DUE]: {
    label: 'Em Atraso',
    color: 'bg-red-100 text-red-800',
    description: 'Pagamento em atraso'
  },
  [SUBSCRIPTION_STATUS.CANCELED]: {
    label: 'Cancelada',
    color: 'bg-gray-100 text-gray-800',
    description: 'Assinatura cancelada'
  },
  [SUBSCRIPTION_STATUS.CANCELLED]: {
    label: 'Cancelada',
    color: 'bg-gray-100 text-gray-800',
    description: 'Assinatura cancelada'
  },
  [SUBSCRIPTION_STATUS.CANCELLING]: {
    label: 'Cancelando',
    color: 'bg-orange-100 text-orange-800',
    description: 'Assinatura sendo cancelada'
  },
  [SUBSCRIPTION_STATUS.EXPIRED]: {
    label: 'Expirada',
    color: 'bg-red-100 text-red-800',
    description: 'Assinatura expirada'
  },
  [SUBSCRIPTION_STATUS.SUSPENDED]: {
    label: 'Suspensa',
    color: 'bg-red-100 text-red-800',
    description: 'Assinatura suspensa'
  },
  [SUBSCRIPTION_STATUS.UNPAID]: {
    label: 'Não Paga',
    color: 'bg-red-100 text-red-800',
    description: 'Pagamento pendente'
  }
} as const;

export const BILLING_CYCLES = {
  MONTHLY: 'monthly',
  YEARLY: 'yearly'
} as const;

export const PAYMENT_PROVIDERS = {
  STRIPE: 'stripe',
  MERCADO_PAGO: 'mercadopago'
} as const;

export const TRIAL_DAYS = 14;
export const TRIAL_WARNING_DAYS = 3;