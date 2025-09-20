// User and Authentication - Actively Used Types
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
  company?: any; // Simplified reference

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

export interface LoginResponse {
  user: User;
  tokens: {
    access: string;
    refresh: string;
  };
  requires_2fa?: boolean;
}

export interface TwoFactorVerifyResponse {
  user: User;
  tokens: {
    access: string;
    refresh: string;
  };
}

// Categories - Used by categories service and pages
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

export interface CategoryForm {
  name: string;
  type: "income" | "expense";
  icon?: string;
  color?: string;
  parent?: number;
}

// Reports - Core Types (Others in reports.ts)
export interface Report {
  id: string;
  company: string;
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
  created_by: string;
  created_by_name?: string;
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

// AI Insights - Used in reports (main interface here, details in reports.ts)
export interface AIInsights {
  insights: any[]; // Import from reports.ts for detailed type
  predictions: {
    next_month_income: number;
    next_month_expenses: number;
    projected_savings: number;
  };
  recommendations: any[]; // Import from reports.ts for detailed type
  alerts?: any[];
  key_metrics?: {
    health_score: number;
    efficiency_score: number;
    growth_potential: number;
  };
  summary?: any;
  ai_generated: boolean;
  from_cache?: boolean;
  fallback_mode?: boolean;
  error?: string;
  generated_at?: string;
  confidence_level?: 'high' | 'medium' | 'low';
  version?: string;
}

// Banking Types - Use imports from banking.types.ts instead
export type {
  BankAccount,
  PluggyConnector,
  PluggyItem,
  Transaction,
  TransactionCategory,
  PaginatedResponse,
  TransactionFilters
} from './banking.types';

// AI Types - Use imports from reports.ts instead
export type {
  AIInsight,
  AIRecommendation
} from './reports';