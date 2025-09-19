export interface DateRange {
  start_date: string;
  end_date: string;
}

export interface ReportData {
  reports: Report[];
  accounts: any[];
  categories: any[];
}

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
  file_size_mb?: number;
  error_message?: string;
  company?: string;
  parameters?: Record<string, any>;
  filters?: Record<string, any>;
}

export interface ReportParameters {
  start_date?: string;
  end_date?: string;
  account_ids?: string[];
  category_ids?: string[];
  title?: string;
  description?: string;
  filters?: Record<string, any>;
}

export interface ScheduledReport {
  id: string;
  name: string;
  report_type: string;
  frequency: string;
  next_run?: string;
  last_run?: string;
  is_active: boolean;
  email_recipients: string[];
  file_format: string;
  parameters?: Record<string, any>;
  filters?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface AIInsights {
  insights: AIInsight[];
  predictions?: {
    next_month_income: number;
    next_month_expenses: number;
    projected_savings: number;
  };
  recommendations?: AIRecommendation[];
  key_metrics?: {
    health_score: number;
    efficiency_score: number;
    growth_potential: number;
  };
  ai_generated: boolean;
  fallback_mode?: boolean;
  error?: string;
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
}

export interface AIRecommendation {
  id: string;
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  effort: 'high' | 'medium' | 'low';
  category: string;
  actions?: string[];
}

export interface ReportTemplate {
  id: string;
  name: string;
  description?: string;
  report_type: string;
  template_config: Record<string, any>;
  charts?: ChartConfig[];
  default_parameters?: Record<string, any>;
  default_filters?: Record<string, any>;
  is_public: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by_name?: string;
}

export interface ChartConfig {
  type: 'line' | 'bar' | 'pie' | 'area' | 'composed';
  dataKey: string;
  title: string;
  config?: Record<string, any>;
}

export interface DashboardStats {
  total_balance: number;
  income_this_month: number;
  expenses_this_month: number;
  net_income: number;
  pending_transactions: number;
  accounts_count: number;
}

export interface AnalyticsData {
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
  summary: {
    total_income: number;
    total_expenses: number;
    net_result: number;
    transaction_count: number;
    daily_avg_income: number;
    daily_avg_expense: number;
  };
  top_income_sources: Array<{
    counterpart_name: string;
    total: number;
    count: number;
  }>;
  top_expense_categories: Array<{
    category__name: string;
    category__icon?: string;
    total: number;
    count: number;
    avg: number;
  }>;
  weekly_trend: Array<{
    week_start: string;
    week_end: string;
    income: number;
    expenses: number;
    net: number;
  }>;
  insights: Array<{
    type: string;
    title: string;
    message: string;
  }>;
}