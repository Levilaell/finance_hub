/**
 * Reports service for fetching financial reports data
 */

import apiClient from '@/lib/api-client';
import { AxiosError } from 'axios';

export interface ChartDataset {
  label: string;
  data: number[];
  borderColor?: string;
  backgroundColor?: string;
  tension?: number;
  fill?: boolean;
  borderWidth?: number;
}

export interface ReportSummary {
  total_income: number;
  total_expenses: number;
  net_cash_flow: number;
  period: string;
  granularity?: string;
  total_amount?: number;
  categories_count?: number;
  transaction_type?: string;
  accounts_count?: number;
}

export interface CashFlowReport {
  labels: string[];
  datasets: ChartDataset[];
  summary: ReportSummary;
}

export interface CategoryBreakdownReport {
  labels: string[];
  datasets: ChartDataset[];
  percentages: number[];
  summary: ReportSummary;
}

export interface AccountBalancesReport {
  labels: string[];
  datasets: ChartDataset[];
  summary: {
    accounts_count: number;
    period: string;
  };
}

export interface MonthlySummaryReport {
  month: string;
  income: {
    total: number;
    count: number;
    daily_avg: number;
  };
  expenses: {
    total: number;
    count: number;
    daily_avg: number;
  };
  net_savings: number;
  top_expenses: Array<{
    description: string;
    amount: number;
    category: string;
    date: string;
    merchant: string;
  }>;
  top_income: Array<{
    description: string;
    amount: number;
    category: string;
    date: string;
    merchant: string;
  }>;
  daily_chart: {
    labels: string[];
    datasets: ChartDataset[];
  };
}

export interface TrendAnalysis {
  income_trend_percentage: number;
  expense_trend_percentage: number;
  income_direction: 'up' | 'down' | 'stable';
  expense_direction: 'up' | 'down' | 'stable';
  avg_monthly_income: number;
  avg_monthly_expenses: number;
  months_analyzed: number;
}

export interface TrendAnalysisReport {
  labels: string[];
  datasets: ChartDataset[];
  analysis: TrendAnalysis;
}

export interface PeriodSummary {
  income: number;
  expenses: number;
  net: number;
  transactions_count: number;
  top_categories: Array<{
    name: string;
    amount: number;
  }>;
  period: string;
}

export interface ComparisonReport {
  period1: PeriodSummary;
  period2: PeriodSummary;
  changes: {
    income: {
      absolute: number;
      percentage: number;
    };
    expenses: {
      absolute: number;
      percentage: number;
    };
    net: {
      absolute: number;
      percentage: number;
    };
  };
  comparison_chart: {
    labels: string[];
    datasets: ChartDataset[];
  };
}

export interface DashboardSummaryData {
  generated_at: string;
  summary: {
    current_month_income: number;
    current_month_expenses: number;
    net_cash_flow: number;
    top_expense_category: string;
    income_trend: 'up' | 'down' | 'stable';
    expense_trend: 'up' | 'down' | 'stable';
  };
  charts: {
    cash_flow: CashFlowReport;
    expenses_by_category: CategoryBreakdownReport;
    trend: {
      labels: string[];
      datasets: ChartDataset[];
    };
  };
}

class ReportsService {
  /**
   * Get cash flow report
   */
  async getCashFlow(params?: {
    start_date?: string;
    end_date?: string;
    granularity?: 'daily' | 'weekly' | 'monthly' | 'yearly';
  }): Promise<CashFlowReport> {
    try {
      const response = await apiClient.get<CashFlowReport>('/api/reports/cash_flow/', params);
      return response;
    } catch (error) {
      console.error('Error fetching cash flow report:', error);
      throw error;
    }
  }

  /**
   * Get category breakdown report
   */
  async getCategoryBreakdown(params?: {
    start_date?: string;
    end_date?: string;
    transaction_type?: 'DEBIT' | 'CREDIT';
  }): Promise<CategoryBreakdownReport> {
    try {
      const response = await apiClient.get<CategoryBreakdownReport>('/api/reports/category_breakdown/', params);
      return response;
    } catch (error) {
      console.error('Error fetching category breakdown:', error);
      throw error;
    }
  }

  /**
   * Get account balances evolution
   */
  async getAccountBalances(params?: {
    start_date?: string;
    end_date?: string;
    account_ids?: string[];
  }): Promise<AccountBalancesReport> {
    try {
      const queryParams = {
        ...params,
        account_ids: params?.account_ids?.join(',')
      };
      const response = await apiClient.get<AccountBalancesReport>('/api/reports/account_balances/', queryParams);
      return response;
    } catch (error) {
      console.error('Error fetching account balances:', error);
      throw error;
    }
  }

  /**
   * Get monthly summary
   */
  async getMonthlySummary(month: number, year: number): Promise<MonthlySummaryReport> {
    try {
      const params = { month, year };
      const response = await apiClient.get<MonthlySummaryReport>('/api/reports/monthly_summary/', params);
      return response;
    } catch (error) {
      console.error('Error fetching monthly summary:', error);
      throw error;
    }
  }

  /**
   * Get trend analysis
   */
  async getTrendAnalysis(params?: {
    months?: number;
    end_date?: string;
  }): Promise<TrendAnalysisReport> {
    try {
      const response = await apiClient.get<TrendAnalysisReport>('/api/reports/trend_analysis/', params);
      return response;
    } catch (error) {
      console.error('Error fetching trend analysis:', error);
      throw error;
    }
  }

  /**
   * Get period comparison
   */
  async getComparison(params: {
    period1_start: string;
    period1_end: string;
    period2_start: string;
    period2_end: string;
  }): Promise<ComparisonReport> {
    try {
      const response = await apiClient.post<any>('/api/reports/comparison/', params);
      return response.data as ComparisonReport;
    } catch (error) {
      console.error('Error fetching comparison report:', error);
      throw error;
    }
  }

  /**
   * Get dashboard summary (optimized for initial load)
   */
  async getDashboardSummary(): Promise<DashboardSummaryData> {
    try {
      const response = await apiClient.get<DashboardSummaryData>('/api/reports/dashboard_summary/');
      return response;
    } catch (error) {
      console.error('Error fetching dashboard summary:', error);
      throw error;
    }
  }

  /**
   * Get bulk reports
   */
  async getBulkReports(params: {
    reports: Array<'cash_flow' | 'category_breakdown' | 'account_balances' | 'monthly_summary' | 'trend_analysis'>;
    start_date?: string;
    end_date?: string;
    granularity?: 'daily' | 'weekly' | 'monthly' | 'yearly';
  }): Promise<any> {
    try {
      const response = await apiClient.post<any>('/api/reports/bulk/', params);
      return response.data;
    } catch (error) {
      console.error('Error fetching bulk reports:', error);
      throw error;
    }
  }

  /**
   * Get available reports metadata
   */
  async getAvailableReports(): Promise<any> {
    try {
      const response = await apiClient.get<any>('/api/reports/available/');
      return response;
    } catch (error) {
      console.error('Error fetching available reports:', error);
      throw error;
    }
  }

  /**
   * Format date for API
   */
  formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  /**
   * Get date range for last N days
   */
  getDateRange(days: number): { start_date: string; end_date: string } {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);
    return {
      start_date: this.formatDate(start),
      end_date: this.formatDate(end),
    };
  }

  /**
   * Get current month date range
   */
  getCurrentMonthRange(): { start_date: string; end_date: string } {
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth(), 1);
    const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    return {
      start_date: this.formatDate(start),
      end_date: this.formatDate(end),
    };
  }

  /**
   * Get previous month date range
   */
  getPreviousMonthRange(): { start_date: string; end_date: string } {
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const end = new Date(now.getFullYear(), now.getMonth(), 0);
    return {
      start_date: this.formatDate(start),
      end_date: this.formatDate(end),
    };
  }
}

export const reportsService = new ReportsService();