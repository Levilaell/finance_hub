// User and Authentication
export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  is_active: boolean;
  is_email_verified: boolean;
  is_phone_verified: boolean;
  avatar?: string;
  date_of_birth?: string;
  last_login_ip?: string;
  preferred_language: 'pt-br' | 'en';
  timezone: string;
  is_two_factor_enabled: boolean;
  two_factor_secret?: string;
  backup_codes: string[];
  payment_gateway?: 'stripe'; 
  created_at: string;
  updated_at: string;
  
  // Company relationship
  company?: Company;
  
  // Computed properties
  full_name?: string;
  initials?: string;
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
  owner: string; // User ID
  name: string;
  trade_name?: string;
  cnpj?: string;
  company_type: 'mei' | 'me' | 'epp' | 'ltda' | 'sa' | 'other';
  business_sector: 'retail' | 'services' | 'industry' | 'construction' | 'agriculture' | 'technology' | 'healthcare' | 'education' | 'food' | 'beauty' | 'automotive' | 'real_estate' | 'consulting' | 'other';
  
  // Contact information
  email?: string;
  phone?: string;
  
  
  // Business metrics
  monthly_revenue?: number;
  employee_count: number;
  
  // Subscription
  subscription_plan?: SubscriptionPlan;
  subscription_status: 'trial' | 'active' | 'past_due' | 'cancelled' | 'cancelling' | 'suspended' | 'expired';
  billing_cycle: 'monthly' | 'yearly';
  trial_ends_at?: string;
  next_billing_date?: string;
  subscription_id?: string;
  subscription_start_date?: string;
  subscription_end_date?: string;
  
  // Usage counters
  current_month_transactions: number;
  last_usage_reset: string;
  
  // Company settings
  logo?: string;
  primary_color: string;
  
  // Metadata
  created_at: string;
  updated_at: string;
  is_active: boolean;
  
  // Computed properties
  is_trial?: boolean;
  is_subscribed?: boolean;
  display_name?: string;
  days_until_trial_ends?: number;
  trial_has_expired?: boolean;
  active_bank_accounts_count?: number;
}

export interface SubscriptionPlan {
  id: number;
  name: string;
  slug: string;
  plan_type: 'starter' | 'professional' | 'enterprise';
  trial_days: number;
  stripe_price_id_monthly?: string;
  stripe_price_id_yearly?: string;
  // mercadopago_plan_id?: string; - Removed with MercadoPago integration
  price_monthly: number | string; // Django DecimalField serializes as string
  price_yearly: number | string;   // Django DecimalField serializes as string
  max_bank_accounts: number;
  display_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  
  // Computed method
  yearly_discount_percentage?: number;
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
}

// Banking - Pluggy Connector
export interface PluggyConnector {
  id: string;
  pluggy_id: number;
  name: string;
  institution_url?: string;
  image_url?: string;
  primary_color: string;
  type: string;
  country: string;
  has_mfa: boolean;
  has_oauth: boolean;
  is_open_finance: boolean;
  is_sandbox: boolean;
  products: string[];
  credentials: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Banking - Pluggy Item
export interface PluggyItem {
  id: string;
  pluggy_item_id: string;
  company: string; // Company ID
  connector: PluggyConnector;
  client_user_id?: string;
  webhook_url?: string;
  next_auto_sync_at?: string;
  products: string[];
  parameter?: Record<string, any>;
  status: 'LOGIN_IN_PROGRESS' | 'WAITING_USER_INPUT' | 'UPDATING' | 'UPDATED' | 'LOGIN_ERROR' | 'OUTDATED' | 'ERROR' | 'DELETED' | 'CONSENT_REVOKED';
  execution_status?: 'CREATED' | 'SUCCESS' | 'PARTIAL_SUCCESS' | 'LOGIN_ERROR' | 'INVALID_CREDENTIALS' | 'USER_INPUT_TIMEOUT' | 'USER_AUTHORIZATION_PENDING' | 'USER_AUTHORIZATION_NOT_GRANTED' | 'SITE_NOT_AVAILABLE' | 'ERROR';
  pluggy_created_at: string;
  pluggy_updated_at: string;
  last_successful_update?: string;
  error_code?: string;
  error_message?: string;
  status_detail?: Record<string, any>;
  consent_id?: string;
  consent_expires_at?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Banking - Bank Account
export interface BankAccount {
  id: string;
  pluggy_account_id: string;
  item: PluggyItem;
  company: string; // Company ID
  type: 'BANK' | 'CREDIT' | 'INVESTMENT' | 'LOAN' | 'OTHER';
  subtype?: 'CHECKING_ACCOUNT' | 'SAVINGS_ACCOUNT' | 'CREDIT_CARD' | 'PREPAID_CARD' | 'INVESTMENT_ACCOUNT' | 'LOAN_ACCOUNT' | 'OTHER';
  number?: string;
  name?: string;
  marketing_name?: string;
  owner?: string;
  tax_number?: string;
  balance: number;
  balance_in_account_currency?: number;
  balance_date?: string;
  currency_code: string;
  bank_data?: Record<string, any>;
  credit_data?: Record<string, any>;
  is_active: boolean;
  pluggy_created_at: string;
  pluggy_updated_at: string;
  created_at: string;
  updated_at: string;
  
  // Computed properties
  masked_number?: string;
  display_name?: string;
}

// Legacy Account interface for backward compatibility
export interface Account {
  id: string;
  name: string;
  account_type: "checking" | "savings" | "credit_card" | "investment";
  balance: number;
  currency: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Categories
export interface TransactionCategory {
  id: string;
  name: string;
  slug: string;
  type: 'income' | 'expense' | 'both';
  parent?: string; // UUID of parent category
  icon: string;
  color: string;
  is_system: boolean;
  is_active: boolean;
  order: number;
  company?: string; // Company ID
  created_at: string;
  updated_at: string;
  
  // Computed properties
  full_name?: string;
  subcategories?: TransactionCategory[];
  transaction_count?: number;
}

// Legacy Category interface for backward compatibility
export interface Category {
  id: string;
  name: string;
  slug: string;
  type: "income" | "expense";
  icon: string | null;
  color: string | null;
  parent: string | null;
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

// Transaction
export interface Transaction {
  id: string;
  pluggy_transaction_id: string;
  account: BankAccount;
  company: string; // Company ID
  type: 'DEBIT' | 'CREDIT';
  status: 'PENDING' | 'POSTED';
  description: string;
  description_raw?: string;
  amount: number;
  amount_in_account_currency?: number;
  balance?: number;
  currency_code: string;
  date: string;
  provider_code?: string;
  provider_id?: string;
  merchant?: Record<string, any>;
  payment_data?: Record<string, any>;
  pluggy_category_id?: string;
  pluggy_category_description?: string;
  category?: TransactionCategory;
  operation_type?: string;
  payment_method?: string;
  credit_card_metadata?: Record<string, any>;
  notes?: string;
  tags: string[];
  metadata?: Record<string, any>;
  pluggy_created_at: string;
  pluggy_updated_at: string;
  created_at: string;
  updated_at: string;
  
  // Computed properties
  amount_display?: string;
  is_income?: boolean;
  is_expense?: boolean;
  account_info?: {
    id: string;
    name: string;
    type: string;
  };
}

// Company User
export interface CompanyUser {
  id: string;
  company: string; // Company ID
  user: User;
  role: 'owner' | 'admin' | 'manager' | 'accountant' | 'viewer';
  permissions: Record<string, any>;
  is_active: boolean;
  invited_at: string;
  joined_at?: string;
}

// Payment Method
export interface PaymentMethod {
  id: string;
  company: string; // Company ID
  payment_type: 'credit_card' | 'debit_card' | 'pix' | 'bank_transfer';
  card_brand?: 'visa' | 'mastercard' | 'amex' | 'elo' | 'dinners' | 'discover';
  last_four?: string;
  exp_month?: number;
  exp_year?: number;
  cardholder_name?: string;
  stripe_payment_method_id?: string;
  // mercadopago_card_id?: string; - Removed with MercadoPago integration
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Payment History
export interface PaymentHistory {
  id: string;
  company: string; // Company ID
  payment_method?: PaymentMethod;
  subscription_plan?: SubscriptionPlan;
  transaction_type: 'subscription' | 'upgrade' | 'refund' | 'adjustment';
  amount: number;
  currency: string;
  status: 'pending' | 'paid' | 'failed' | 'canceled' | 'refunded' | 'partially_refunded';
  description: string;
  stripe_payment_intent_id?: string;
  stripe_invoice_id?: string;
  // mercadopago_payment_id?: string; - Removed with MercadoPago integration
  invoice_number?: string;
  invoice_url?: string;
  invoice_pdf_path?: string;
  transaction_date: string;
  due_date?: string;
  paid_at?: string;
  created_at: string;
  updated_at: string;
}

// Resource Usage
export interface ResourceUsage {
  id: string;
  company: string; // Company ID
  month: string; // First day of month
  transactions_count: number;
  reports_generated: number;
  created_at: string;
  updated_at: string;
  
  // Computed properties
  total_ai_usage?: number;
}

// Email Verification
export interface EmailVerification {
  id: string;
  user: string; // User ID
  token: string;
  is_used: boolean;
  created_at: string;
  expires_at: string;
}

// Password Reset
export interface PasswordReset {
  id: string;
  user: string; // User ID
  token: string;
  is_used: boolean;
  created_at: string;
  expires_at: string;
}

// Notification Preferences
export interface NotificationPreference {
  id: string;
  user: string; // User ID
  email_enabled: boolean;
  push_enabled: boolean;
  sms_enabled: boolean;
  type_preferences: Record<string, any>;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  send_daily_digest: boolean;
  send_weekly_digest: boolean;
  digest_time: string;
  low_balance_threshold: number;
  large_transaction_threshold: number;
  updated_at: string;
}

// Reports

// Notifications
export interface Notification {
  id: string;
  event: 'account_sync_failed' | 'payment_failed' | 'low_balance' | 'security_alert' | 'account_connected' | 'large_transaction' | 'report_ready' | 'payment_success' | 'sync_completed';
  event_display?: string;
  is_critical: boolean;
  title: string;
  message: string;
  metadata?: Record<string, any>;
  action_url?: string;
  is_read: boolean;
  read_at?: string;
  delivery_status?: 'pending' | 'delivered' | 'failed';
  created_at: string;
}

// Dashboard

// API Response Types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
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
  type: "income" | "expense";
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
  type?: 'DEBIT' | 'CREDIT';
  status?: 'PENDING' | 'POSTED';
  search?: string;
}

export interface Report {
  id: string;
  company: string; // Company ID
  report_type: 'monthly_summary' | 'quarterly_report' | 'annual_report' | 'cash_flow' | 'profit_loss' | 'category_analysis' | 'tax_report' | 'custom';
  title: string;
  description?: string;
  period_start: string;
  period_end: string;
  parameters: Record<string, any>;
  filters: Record<string, any>;
  file_format: 'pdf' | 'xlsx' | 'csv' | 'json';
  file?: string;
  file_size: number;
  is_generated: boolean;
  error_message?: string;
  created_at: string;
  created_by: string; // User ID
  
  // Computed properties
  created_by_name?: string;
}

// Report Template
export interface ReportTemplate {
  id: string;
  company: string; // Company ID
  name: string;
  description?: string;
  report_type: string;
  template_config: Record<string, any>;
  charts: any[];
  default_parameters: Record<string, any>;
  default_filters: Record<string, any>;
  is_public: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: string; // User ID
}

// AI Analysis
export interface AIAnalysis {
  id: string;
  company: string; // Company ID
  title: string;
  description?: string;
  analysis_type: 'financial_health' | 'cash_flow_prediction' | 'expense_optimization' | 'revenue_analysis' | 'risk_assessment' | 'investment_advice' | 'custom_query' | 'general_insights';
  period_start: string;
  period_end: string;
  analysis_config: Record<string, any>;
  input_parameters: Record<string, any>;
  filters: Record<string, any>;
  ai_response: Record<string, any>;
  insights: any[];
  recommendations: any[];
  predictions: Record<string, any>;
  summary: Record<string, any>;
  confidence_score: number;
  health_score?: number;
  risk_score?: number;
  is_processed: boolean;
  processing_time: number;
  error_message?: string;
  cache_key?: string;
  expires_at?: string;
  created_at: string;
  updated_at: string;
  created_by: string; // User ID
  is_public: boolean;
  is_favorite: boolean;
  tags: string[];
}

// AI Analysis Template
export interface AIAnalysisTemplate {
  id: string;
  company: string; // Company ID
  name: string;
  description?: string;
  analysis_type: string;
  template_config: Record<string, any>;
  prompt_template: string;
  default_parameters: Record<string, any>;
  default_filters: Record<string, any>;
  output_format: Record<string, any>;
  visualization_config: any[];
  is_active: boolean;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  created_by: string; // User ID
}

// Item Webhook
export interface ItemWebhook {
  id: string;
  item: PluggyItem;
  event_type: 'item.created' | 'item.updated' | 'item.error' | 'item.deleted' | 'item.login_succeeded' | 'item.waiting_user_input' | 'connector.status_updated' | 'transactions.created' | 'transactions.updated' | 'transactions.deleted' | 'consent.created' | 'consent.updated' | 'consent.revoked' | 'payment_intent.created' | 'payment_intent.completed' | 'payment_intent.waiting_payer_authorization' | 'payment_intent.error' | 'scheduled_payment.created' | 'scheduled_payment.completed' | 'scheduled_payment.error' | 'scheduled_payment.canceled' | 'payment_refund.completed' | 'payment_refund.error' | 'automatic_pix_payment.created' | 'automatic_pix_payment.completed' | 'automatic_pix_payment.error' | 'automatic_pix_payment.canceled';
  event_id: string;
  payload: Record<string, any>;
  processed: boolean;
  processed_at?: string;
  error?: string;
  created_at: string;
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

// Chart Data Types