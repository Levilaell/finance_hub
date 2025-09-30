import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { reportsService } from '@/services/reports.service';
import type {
  CashFlowReport,
  CategoryBreakdownReport,
  AccountBalancesReport,
  MonthlySummaryReport,
  TrendAnalysisReport,
  ComparisonReport,
  DashboardSummaryData,
} from '@/services/reports.service';

interface ReportParams {
  start_date?: string;
  end_date?: string;
  granularity?: 'daily' | 'weekly' | 'monthly' | 'yearly';
}

interface CategoryParams extends ReportParams {
  transaction_type?: 'DEBIT' | 'CREDIT';
}

interface AccountParams extends ReportParams {
  account_ids?: string[];
}

interface MonthlyParams {
  month: number;
  year: number;
}

interface TrendParams {
  months?: number;
  end_date?: string;
}

interface ComparisonParams {
  period1_start: string;
  period1_end: string;
  period2_start: string;
  period2_end: string;
}

/**
 * Hook for fetching cash flow report
 */
export function useCashFlowReport(
  params?: ReportParams,
  enabled = true
): UseQueryResult<CashFlowReport> {
  return useQuery({
    queryKey: ['reports', 'cash-flow', params],
    queryFn: () => reportsService.getCashFlow(params),
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook for fetching category breakdown report
 */
export function useCategoryBreakdown(
  params?: CategoryParams,
  enabled = true
): UseQueryResult<CategoryBreakdownReport> {
  return useQuery({
    queryKey: ['reports', 'category-breakdown', params],
    queryFn: () => reportsService.getCategoryBreakdown(params),
    enabled,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook for fetching account balances evolution
 */
export function useAccountBalances(
  params?: AccountParams,
  enabled = true
): UseQueryResult<AccountBalancesReport> {
  return useQuery({
    queryKey: ['reports', 'account-balances', params],
    queryFn: () => reportsService.getAccountBalances(params),
    enabled,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook for fetching monthly summary
 */
export function useMonthlySummary(
  month: number,
  year: number,
  enabled = true
): UseQueryResult<MonthlySummaryReport> {
  return useQuery({
    queryKey: ['reports', 'monthly-summary', { month, year }],
    queryFn: () => reportsService.getMonthlySummary(month, year),
    enabled,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook for fetching trend analysis
 */
export function useTrendAnalysis(
  params?: TrendParams,
  enabled = true
): UseQueryResult<TrendAnalysisReport> {
  return useQuery({
    queryKey: ['reports', 'trend-analysis', params],
    queryFn: () => reportsService.getTrendAnalysis(params),
    enabled,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook for fetching comparison report
 */
export function useComparisonReport(
  params: ComparisonParams,
  enabled = true
): UseQueryResult<ComparisonReport> {
  return useQuery({
    queryKey: ['reports', 'comparison', params],
    queryFn: () => reportsService.getComparison(params),
    enabled,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook for fetching dashboard summary
 */
export function useDashboardSummary(
  enabled = true
): UseQueryResult<DashboardSummaryData> {
  return useQuery({
    queryKey: ['reports', 'dashboard-summary'],
    queryFn: () => reportsService.getDashboardSummary(),
    enabled,
    staleTime: 2 * 60 * 1000, // 2 minutes (more frequent for dashboard)
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook for fetching multiple reports at once
 */
export function useBulkReports(
  reports: Array<'cash_flow' | 'category_breakdown' | 'account_balances' | 'monthly_summary' | 'trend_analysis'>,
  params?: ReportParams,
  enabled = true
): UseQueryResult<any> {
  return useQuery({
    queryKey: ['reports', 'bulk', { reports, ...params }],
    queryFn: () => reportsService.getBulkReports({ reports, ...params }),
    enabled,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook for fetching available reports metadata
 */
export function useAvailableReports(): UseQueryResult<any> {
  return useQuery({
    queryKey: ['reports', 'available'],
    queryFn: () => reportsService.getAvailableReports(),
    staleTime: 30 * 60 * 1000, // 30 minutes (metadata rarely changes)
    refetchOnWindowFocus: false,
  });
}

/**
 * Helper hook to get date ranges for common periods
 */
export function useReportDateRanges() {
  const getCurrentMonth = () => {
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth(), 1);
    const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    return {
      start_date: start.toISOString().split('T')[0],
      end_date: end.toISOString().split('T')[0],
    };
  };

  const getPreviousMonth = () => {
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const end = new Date(now.getFullYear(), now.getMonth(), 0);
    return {
      start_date: start.toISOString().split('T')[0],
      end_date: end.toISOString().split('T')[0],
    };
  };

  const getLastNDays = (days: number) => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);
    return {
      start_date: start.toISOString().split('T')[0],
      end_date: end.toISOString().split('T')[0],
    };
  };

  const getQuarter = () => {
    const now = new Date();
    const quarter = Math.floor((now.getMonth() + 3) / 3);
    const start = new Date(now.getFullYear(), (quarter - 1) * 3, 1);
    const end = new Date(now.getFullYear(), quarter * 3, 0);
    return {
      start_date: start.toISOString().split('T')[0],
      end_date: end.toISOString().split('T')[0],
    };
  };

  const getYearToDate = () => {
    const now = new Date();
    const start = new Date(now.getFullYear(), 0, 1);
    return {
      start_date: start.toISOString().split('T')[0],
      end_date: now.toISOString().split('T')[0],
    };
  };

  return {
    getCurrentMonth,
    getPreviousMonth,
    getLastNDays,
    getQuarter,
    getYearToDate,
  };
}