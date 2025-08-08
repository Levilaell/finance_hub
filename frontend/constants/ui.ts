/**
 * UI-related constants
 */

// AI Insights predefined options
export const PREDEFINED_GOALS = [
  'Aumentar faturamento em 20%',
  'Reduzir despesas em 15%',
  'Melhorar fluxo de caixa',
  'Expandir para novos mercados',
  'Lançar novo produto/serviço',
  'Aumentar margem de lucro',
  'Reduzir inadimplência',
  'Otimizar capital de giro'
] as const;

export const PREDEFINED_CHALLENGES = [
  'Alto custo de aquisição de clientes',
  'Baixa taxa de conversão',
  'Fluxo de caixa negativo',
  'Alta inadimplência',
  'Custos operacionais elevados',
  'Baixa margem de lucro',
  'Dependência de poucos clientes',
  'Falta de capital de giro'
] as const;

export const EXAMPLE_QUESTIONS = [
  'Como posso reduzir meu CAC (Custo de Aquisição de Cliente)?',
  'Qual a melhor estratégia para aumentar meu ticket médio?',
  'Como otimizar meu fluxo de caixa nos próximos 3 meses?',
  'Devo investir em marketing digital ou vendas diretas?',
  'Como reduzir a inadimplência sem perder clientes?',
  'Qual o momento ideal para buscar investimento externo?'
] as const;

// Report types
export const REPORT_TYPES = [
  { value: 'cash_flow', label: 'Fluxo de Caixa' },
  { value: 'profit_loss', label: 'DRE' },
  { value: 'balance_sheet', label: 'Balanço Patrimonial' },
  { value: 'custom', label: 'Personalizado' }
] as const;

// Date ranges
export const DATE_RANGES = {
  TODAY: 'today',
  YESTERDAY: 'yesterday',
  LAST_7_DAYS: 'last_7_days',
  LAST_30_DAYS: 'last_30_days',
  THIS_MONTH: 'this_month',
  LAST_MONTH: 'last_month',
  THIS_QUARTER: 'this_quarter',
  LAST_QUARTER: 'last_quarter',
  THIS_YEAR: 'this_year',
  LAST_YEAR: 'last_year',
  CUSTOM: 'custom'
} as const;

// Transaction types
export const TRANSACTION_TYPES = {
  INCOME: 'income',
  EXPENSE: 'expense',
  TRANSFER: 'transfer'
} as const;

// Category icons
export const CATEGORY_ICONS = [
  'shopping-cart',
  'home',
  'car',
  'utensils',
  'heart',
  'book',
  'plane',
  'gift',
  'dollar-sign',
  'briefcase',
  'coffee',
  'smartphone',
  'tv',
  'music',
  'gamepad2',
  'dumbbell',
  'pill',
  'scissors',
  'shirt',
  'baby',
  'paw-print',
  'hammer',
  'palette',
  'camera',
  'umbrella'
] as const;

// Status colors - Professional system
export const STATUS_COLORS = {
  success: 'bg-success-subtle text-success-subtle border border-success-subtle',
  warning: 'bg-warning-subtle text-warning-subtle border border-warning-subtle',
  error: 'bg-error-subtle text-error-subtle border border-error-subtle',
  info: 'bg-info-subtle text-info-subtle border border-info-subtle',
  default: 'bg-muted text-muted-foreground border border-muted'
} as const;