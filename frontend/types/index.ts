// User and Authentication
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  company: Company;
  role: "owner" | "admin" | "member";
  is_active: boolean;
  is_email_verified: boolean;
  is_two_factor_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  password2: string;
  first_name: string;
  last_name: string;
  company_name: string;
  company_cnpj: string;
  company_type: string;
  business_sector: string;
  phone: string;
  selected_plan?: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginResponse {
  user: User;
  tokens: AuthTokens;
  requires_2fa?: boolean;
}

export interface TwoFactorVerifyResponse {
  user: User;
  tokens: AuthTokens;
}

// Company
export interface Company {
  id: string;
  name: string;
  trade_name?: string;
  cnpj?: string;
  company_type: string;
  business_sector: string;
  subscription_plan?: SubscriptionPlan;
  subscription_status: 'trial' | 'active' | 'past_due' | 'cancelled' | 'suspended' | 'expired';
  billing_cycle: 'monthly' | 'yearly';
  trial_ends_at?: string;
  next_billing_date?: string;
  subscription_start_date?: string;
  subscription_end_date?: string;
  current_month_transactions: number;
  current_month_ai_requests: number;
  // ... outros campos
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  slug: string;
  plan_type: 'free' | 'starter' | 'professional' | 'enterprise';
  price_monthly: number;
  price_yearly: number;
  max_transactions: number;
  max_bank_accounts: number;
  max_users: number;
  has_ai_categorization: boolean;
  enable_ai_insights: boolean;
  enable_ai_reports: boolean;
  max_ai_requests_per_month: number;
  has_advanced_reports: boolean;
  has_api_access: boolean;
  has_accountant_access: boolean;
  has_priority_support: boolean;
  yearly_discount?: number;
}

export interface UsageLimits {
  transactions: {
    used: number;
    limit: number;
    percentage: number;
  };
  bank_accounts: {
    used: number;
    limit: number;
    percentage: number;
  };
  ai_requests: {
    used: number;
    limit: number;
    percentage: number;
  };
}

// Banking
export interface BankProvider {
  id: string;
  name: string;
  logo_url: string | null;
  is_active: boolean;
}

export interface Account {
  id: string;
  name: string;
  account_type: "checking" | "savings" | "credit_card" | "investment";
  balance: number;
  currency: string;
  bank_provider?: BankProvider;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BankAccount {
  id: string;
  provider: BankProvider;
  account_name: string;
  account_number: string;
  account_type: "checking" | "savings" | "credit_card" | "investment";
  currency: string;
  current_balance: number;
  available_balance: number;
  is_active: boolean;
  status: "active" | "inactive" | "sync_error" | "pending";
  last_sync_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface BankTransaction {
  id: string;
  bank_account: string;
  transaction_id: string;
  amount: number;
  currency: string;
  description: string;
  category: Category | null;
  transaction_date: string;
  posted_date: string;
  transaction_type: "debit" | "credit";
  status: "pending" | "posted" | "cancelled";
  merchant_name: string | null;
  merchant_category: string | null;
  metadata: Record<string, any>;
  tags?: string[];
  ai_categorized?: boolean;
  ai_confidence?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

// Categories
export interface Category {
  id: string;
  name: string;
  slug: string;
  category_type: "income" | "expense";
  icon: string | null;
  color: string | null;
  parent: number | null;
  is_system: boolean;
  is_active: boolean;
  full_name?: string;
  subcategories?: Category[];
  transaction_count?: number;
  created_at: string;
  updated_at: string;
}

export interface CategoryRule {
  id: string;
  category: string;
  rule_type: "contains" | "equals" | "starts_with" | "ends_with" | "regex";
  field: "description" | "merchant_name" | "amount";
  value: string;
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Reports
export interface Report {
  id: string;
  title: string;
  report_type: string;
  period_start: string;
  period_end: string;
  file_format: string;
  is_generated: boolean;
  created_at: string;
  created_by_name?: string;
  file?: string;
  file_size?: number;
  generation_time?: number;
  error_message?: string;
  parameters?: Record<string, any>;
  filters?: Record<string, any>;
}

export interface ReportParameters {
  start_date?: string;
  end_date?: string;
  accounts?: string[];
  categories?: string[];
  account_ids?: string[];
  category_ids?: string[];
  comparison_period?: "previous_period" | "previous_year";
}

export interface ReportResult {
  id: string;
  report: string;
  generated_at: string;
  data: Record<string, any>;
  file_url: string | null;
}

// Notifications
export interface Notification {
  id: string;
  title: string;
  message: string;
  type: "info" | "warning" | "error" | "success";
  category: "transaction" | "account" | "system" | "security";
  is_read: boolean;
  action_url: string | null;
  created_at: string;
}

// Dashboard
export interface DashboardStats {
  total_balance: number;
  income_this_month: number;
  expenses_this_month: number;
  net_income: number;
  pending_transactions: number;
  accounts_count: number;
}

export interface CashFlowData {
  date: string;
  income: number;
  expenses: number;
  balance: number;
}

export interface CategorySpending {
  category: Category;
  amount: number;
  percentage: number;
  transaction_count: number;
}

// API Response Types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail?: string;
  message?: string;
  errors?: Record<string, string[]>;
}

// Form Types
export interface BankAccountForm {
  provider_id: string;
  account_name: string;
  account_number: string;
  account_type: "checking" | "savings" | "credit_card" | "investment";
  currency: string;
  initial_balance: number;
}

export interface CategoryForm {
  name: string;
  category_type: "income" | "expense";
  icon?: string;
  color?: string;
  parent?: number;
}

export interface TransactionFilter {
  account_id?: string;
  category_id?: string;
  start_date?: string;
  end_date?: string;
  min_amount?: number;
  max_amount?: number;
  transaction_type?: "debit" | "credit";
  search?: string;
}

// frontend/types/index.ts
// Add these types to your existing types file

// Report Types
export interface Report {
  id: string;
  title: string;
  report_type: 'monthly_summary' | 'quarterly_report' | 'annual_report' | 'cash_flow' | 'profit_loss' | 'category_analysis' | 'tax_report' | 'custom';
  period_start: string;
  period_end: string;
  file_format: 'pdf' | 'xlsx' | 'csv' | 'json';
  is_generated: boolean;
  file?: string;
  file_size?: number;
  generation_time?: number;
  error_message?: string;
  created_at: string;
  created_by_name?: string;
  parameters?: Record<string, any>;
  filters?: Record<string, any>;
}

export interface ReportParameters {
  start_date: string;
  end_date: string;
  account_ids?: string[];
  category_ids?: string[];
  title?: string;
  description?: string;
  file_format?: string;
  filters?: Record<string, any>;
}

export interface ScheduledReport {
  id: string;
  name: string;
  report_type: string;
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  is_active: boolean;
  send_email: boolean;
  email_recipients: string[];
  file_format: string;
  next_run_at: string;
  last_run_at?: string;
  parameters?: Record<string, any>;
  filters?: Record<string, any>;
  created_at: string;
  created_by_name?: string;
}

export interface AIInsights {
  insights: AIInsight[];
  predictions: AIPredictions;
  recommendations: AIRecommendation[];
  alerts?: AIAlert[];
  key_metrics?: AIKeyMetrics;
  summary?: AISummary;
  ai_generated: boolean;
  from_cache?: boolean;
  fallback_mode?: boolean;
  error?: string;
  generated_at?: string;
  confidence_level?: 'high' | 'medium' | 'low';
  version?: string;
}

export interface AIInsight {
  type: 'success' | 'warning' | 'info' | 'danger';
  title: string;
  description: string;
  value?: string;
  trend?: 'up' | 'down' | 'stable';
  priority?: 'high' | 'medium' | 'low';
  actionable?: boolean;
  category?: string;
  drill_down?: {
    label: string;
    url: string;
  };
}

export interface AIPredictions {
  next_month_income: number;
  next_month_expenses: number;
  projected_savings: number;
  growth_rate?: number;
  risk_score?: number;
  opportunities?: string[];
  threats?: string[];
  confidence?: 'high' | 'medium' | 'low';
}

export interface AIRecommendation {
  type: 'cost_reduction' | 'revenue_growth' | 'risk_mitigation' | 'efficiency';
  title: string;
  description: string;
  potential_impact: string;
  priority: 'high' | 'medium' | 'low';
  time_to_implement: 'imediato' | 'curto_prazo' | 'medio_prazo';
  difficulty?: 'easy' | 'medium' | 'hard';
  action_button?: {
    label: string;
    url: string;
  };
}

export interface AIAlert {
  severity: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  action_required?: string;
  urgency?: 'immediate' | 'urgent' | 'soon' | 'monitor';
}

export interface AIKeyMetrics {
  health_score: number;
  efficiency_score: number;
  growth_potential: number;
  overall_grade?: string;
}

export interface AISummary {
  overall_status: 'excellent' | 'healthy' | 'attention_needed' | 'critical';
  status_message: string;
  key_message: string;
  main_opportunity?: string;
  main_risk?: string;
  recommended_action?: string;
  executive_takeaway?: string;
}

// Account Types (if not already defined)
export interface Account {
  id: string;
  name: string;
  bank_provider: string;
  account_type: string;
  account_number: string;
  current_balance: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Category Types (if not already defined)
export interface Category {
  id: string;
  name: string;
  slug: string;
  icon: string;
  category_type: 'income' | 'expense' | 'both';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Chart Data Types
export interface CashFlowData {
  date: string;
  income: number;
  expenses: number;
  balance: number;
}

export interface CategorySpendingData {
  category: {
    name: string;
    icon: string;
  };
  amount: number;
  percentage: number;
  transaction_count: number;
}

export interface IncomeVsExpensesData {
  month: string;
  income: number;
  expenses: number;
  profit: number;
}