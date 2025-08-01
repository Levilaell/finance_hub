import { useQuery } from '@tanstack/react-query';
import { reportsService } from '@/services/reports.service';
import { useState, useEffect, useCallback } from 'react';

interface DateRange {
  start_date: Date | null;
  end_date: Date | null;
}

export const useReportData = (initialPeriod?: DateRange) => {
  const [selectedPeriod, setSelectedPeriod] = useState<DateRange>(
    initialPeriod || {
      start_date: null,
      end_date: null,
    }
  );

  // Set default dates on client side
  useEffect(() => {
    if (!selectedPeriod.start_date && !selectedPeriod.end_date) {
      const now = new Date();
      const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
      setSelectedPeriod({
        start_date: startOfMonth,
        end_date: now,
      });
    }
  }, []);

  // Cash flow data
  const cashFlowQuery = useQuery({
    queryKey: ['cash-flow', selectedPeriod],
    queryFn: () => {
      if (!selectedPeriod.start_date || !selectedPeriod.end_date) return null;
      return reportsService.getCashFlowData({
        start_date: selectedPeriod.start_date,
        end_date: selectedPeriod.end_date,
      });
    },
    enabled: !!selectedPeriod.start_date && !!selectedPeriod.end_date,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });

  // Category spending data
  const categorySpendingQuery = useQuery({
    queryKey: ['category-spending', selectedPeriod],
    queryFn: () => {
      if (!selectedPeriod.start_date || !selectedPeriod.end_date) return null;
      return reportsService.getCategorySpending({
        start_date: selectedPeriod.start_date,
        end_date: selectedPeriod.end_date,
      });
    },
    enabled: !!selectedPeriod.start_date && !!selectedPeriod.end_date,
    staleTime: 5 * 60 * 1000,
    cacheTime: 10 * 60 * 1000,
  });

  // Income vs expenses data
  const incomeVsExpensesQuery = useQuery({
    queryKey: ['income-vs-expenses', selectedPeriod],
    queryFn: () => {
      if (!selectedPeriod.start_date || !selectedPeriod.end_date) return null;
      return reportsService.getIncomeVsExpenses({
        start_date: selectedPeriod.start_date,
        end_date: selectedPeriod.end_date,
      });
    },
    enabled: !!selectedPeriod.start_date && !!selectedPeriod.end_date,
    staleTime: 5 * 60 * 1000,
    cacheTime: 10 * 60 * 1000,
  });

  // Analytics data
  const analyticsQuery = useQuery({
    queryKey: ['analytics', selectedPeriod],
    queryFn: () => {
      if (!selectedPeriod.start_date || !selectedPeriod.end_date) return null;
      const days = Math.ceil(
        (selectedPeriod.end_date.getTime() - selectedPeriod.start_date.getTime()) / 
        (1000 * 60 * 60 * 24)
      );
      return reportsService.getAnalytics(days);
    },
    enabled: !!selectedPeriod.start_date && !!selectedPeriod.end_date,
    staleTime: 5 * 60 * 1000,
    cacheTime: 10 * 60 * 1000,
  });

  // Quick period selection
  const handleQuickPeriod = useCallback((periodId: string) => {
    const now = new Date();
    let start: Date;
    let end: Date = now;

    switch (periodId) {
      case 'current_month':
        start = new Date(now.getFullYear(), now.getMonth(), 1);
        break;
      case 'last_month':
        start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        end = new Date(now.getFullYear(), now.getMonth(), 0);
        break;
      case 'quarterly':
        const quarter = Math.floor(now.getMonth() / 3);
        start = new Date(now.getFullYear(), quarter * 3, 1);
        break;
      case 'year_to_date':
        start = new Date(now.getFullYear(), 0, 1);
        break;
      default:
        start = new Date(now.getFullYear(), now.getMonth(), 1);
    }

    setSelectedPeriod({ start_date: start, end_date: end });
  }, []);

  // Refresh all data
  const refreshData = useCallback(() => {
    cashFlowQuery.refetch();
    categorySpendingQuery.refetch();
    incomeVsExpensesQuery.refetch();
    analyticsQuery.refetch();
  }, [cashFlowQuery, categorySpendingQuery, incomeVsExpensesQuery, analyticsQuery]);

  return {
    selectedPeriod,
    setSelectedPeriod,
    handleQuickPeriod,
    refreshData,
    cashFlow: {
      data: cashFlowQuery.data,
      isLoading: cashFlowQuery.isLoading,
      error: cashFlowQuery.error,
    },
    categorySpending: {
      data: categorySpendingQuery.data,
      isLoading: categorySpendingQuery.isLoading,
      error: categorySpendingQuery.error,
    },
    incomeVsExpenses: {
      data: incomeVsExpensesQuery.data,
      isLoading: incomeVsExpensesQuery.isLoading,
      error: incomeVsExpensesQuery.error,
    },
    analytics: {
      data: analyticsQuery.data,
      isLoading: analyticsQuery.isLoading,
      error: analyticsQuery.error,
    },
    isLoading: 
      cashFlowQuery.isLoading || 
      categorySpendingQuery.isLoading || 
      incomeVsExpensesQuery.isLoading ||
      analyticsQuery.isLoading,
  };
};