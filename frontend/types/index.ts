// User and Authentication
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  company: Company;
  role: "owner" | "admin" | "member";
  is_active: boolean;
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
  company_type: string;
  business_sector: string;
  phone?: string;
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
  subscription_plan: SubscriptionPlan;
  subscription_status: "active" | "trialing" | "past_due" | "canceled" | "unpaid";
  trial_ends_at: string | null;
  next_billing_date: string | null;
  subscription_start_date: string | null;
  subscription_end_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  slug: string;
  plan_type: string;
  price_monthly: number;
  price_yearly: number;
  max_transactions: number;
  max_bank_accounts: number;
  max_users: number;
  has_ai_categorization: boolean;
  has_advanced_reports: boolean;
  has_api_access: boolean;
  has_accountant_access: boolean;
  // Legacy fields for backward compatibility
  price?: number;
  currency?: string;
  interval?: "month" | "year";
  features?: string[];
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
  last_synced: string | null;
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
  name: string;
  report_type: "income_statement" | "cash_flow" | "balance_sheet" | "custom";
  frequency: "daily" | "weekly" | "monthly" | "quarterly" | "yearly";
  parameters: ReportParameters;
  last_generated: string | null;
  created_at: string;
  updated_at: string;
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