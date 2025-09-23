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
  drill_down?: {
    label: string;
    url: string;
  };
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

// Note: Removed unused types: ReportTemplate, ChartConfig, DashboardStats, AnalyticsData