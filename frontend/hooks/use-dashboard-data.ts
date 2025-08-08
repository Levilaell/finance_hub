import { useState, useEffect, useCallback } from 'react';
import { dashboardService, DashboardData } from '@/services/dashboard.service';
import { bankingService } from '@/services/banking.service';
import apiClient from '@/lib/api-client';
import { requestManager } from '@/lib/request-manager';

interface UseDashboardDataReturn {
  dashboardData: DashboardData | null;
  subscriptionStatus: any | null;
  accounts: any[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export function useDashboardData(): UseDashboardDataReturn {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [subscriptionStatus, setSubscriptionStatus] = useState<any | null>(null);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchDashboardData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Batch all dashboard-related requests
      const results = await requestManager.batchRequests([
        {
          key: 'dashboard-data',
          fn: () => dashboardService.getDashboardData(),
          transform: (data) => data,
        },
        {
          key: 'subscription-status',
          fn: () => apiClient.get('/api/companies/subscription-status/'),
          transform: (data) => data,
        },
        {
          key: 'bank-accounts',
          fn: () => bankingService.getAccounts(),
          transform: (data) => data,
        },
      ]);

      const [dashboard, subscription, accountsData] = results;
      
      setDashboardData(dashboard);
      setSubscriptionStatus(subscription);
      setAccounts(accountsData);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError(err instanceof Error ? err : new Error('Failed to fetch dashboard data'));
      
      // Set default values on error
      setDashboardData({
        current_balance: 0,
        monthly_income: 0,
        monthly_expenses: 0,
        monthly_net: 0,
        recent_transactions: [],
        top_categories: [],
        accounts_count: 0,
        transactions_count: 0,
      });
      setAccounts([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Listen for subscription updates
  useEffect(() => {
    const handleUpdate = () => {
      fetchDashboardData();
    };
    
    window.addEventListener('subscription-updated', handleUpdate);
    return () => window.removeEventListener('subscription-updated', handleUpdate);
  }, [fetchDashboardData]);

  return {
    dashboardData,
    subscriptionStatus,
    accounts,
    isLoading,
    error,
    refetch: fetchDashboardData,
  };
}