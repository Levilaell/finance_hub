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
    color: 'bg-success-subtle text-success-subtle border border-success-subtle',
    description: 'Sua assinatura está ativa'
  },
  [SUBSCRIPTION_STATUS.TRIALING]: {
    label: 'Período de Teste',
    color: 'bg-info-subtle text-info-subtle border border-info-subtle',
    description: 'Você está no período de teste gratuito'
  },
  [SUBSCRIPTION_STATUS.TRIAL]: {
    label: 'Período de Teste',
    color: 'bg-info-subtle text-info-subtle border border-info-subtle',
    description: 'Você está no período de teste gratuito'
  },
  [SUBSCRIPTION_STATUS.PAST_DUE]: {
    label: 'Em Atraso',
    color: 'bg-error-subtle text-error-subtle border border-error-subtle',
    description: 'Pagamento em atraso'
  },
  [SUBSCRIPTION_STATUS.CANCELED]: {
    label: 'Cancelada',
    color: 'bg-muted text-muted-foreground border border-muted',
    description: 'Assinatura cancelada'
  },
  [SUBSCRIPTION_STATUS.CANCELLED]: {
    label: 'Cancelada',
    color: 'bg-muted text-muted-foreground border border-muted',
    description: 'Assinatura cancelada'
  },
  [SUBSCRIPTION_STATUS.CANCELLING]: {
    label: 'Cancelando',
    color: 'bg-warning-subtle text-warning-subtle border border-warning-subtle',
    description: 'Assinatura sendo cancelada'
  },
  [SUBSCRIPTION_STATUS.EXPIRED]: {
    label: 'Expirada',
    color: 'bg-error-subtle text-error-subtle border border-error-subtle',
    description: 'Assinatura expirada'
  },
  [SUBSCRIPTION_STATUS.SUSPENDED]: {
    label: 'Suspensa',
    color: 'bg-error-subtle text-error-subtle border border-error-subtle',
    description: 'Assinatura suspensa'
  },
  [SUBSCRIPTION_STATUS.UNPAID]: {
    label: 'Não Paga',
    color: 'bg-error-subtle text-error-subtle border border-error-subtle',
    description: 'Pagamento pendente'
  }
} as const;

export const BILLING_CYCLES = {
  MONTHLY: 'monthly',
  YEARLY: 'yearly'
} as const;

export const PAYMENT_PROVIDERS = {
  STRIPE: 'stripe'
  // MERCADO_PAGO: 'mercadopago' - Removed in favor of Stripe-only integration
} as const;

export const TRIAL_DAYS = 14;
export const TRIAL_WARNING_DAYS = 3;