// Hook for managing bank accounts

import { useQuery } from '@tanstack/react-query';
import { bankingService } from '@/services/banking.service';
import type { BankAccount, AccountSummary } from '@/types/banking.types';

interface UseAccountsOptions {
  type?: string;
  subtype?: string;
  isActive?: boolean;
}

export function useBankAccounts(options?: UseAccountsOptions) {
  // Fetch all accounts
  const {
    data: accountsData,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['bankAccounts', options],
    queryFn: async () => {
      const response = await bankingService.getAccounts();
      return response;
    },
    staleTime: 60 * 1000, // 1 minute
  });

  // Fetch account summary
  const {
    data: summary,
    isLoading: isLoadingSummary
  } = useQuery({
    queryKey: ['accountSummary'],
    queryFn: bankingService.getAccountsSummary,
    staleTime: 60 * 1000,
  });

  // Group accounts by type
  const accountsByType = accountsData?.reduce((acc, account) => {
    const key = account.type === 'BANK' ? 'bank' : 'credit';
    if (!acc[key]) acc[key] = [];
    acc[key].push(account);
    return acc;
  }, {} as Record<string, BankAccount[]>) || {};

  // Calculate totals
  const totals = {
    bankBalance: accountsByType.bank?.reduce((sum: number, acc: BankAccount) => sum + acc.balance, 0) || 0,
    creditBalance: accountsByType.credit?.reduce((sum: number, acc: BankAccount) => sum + acc.balance, 0) || 0,
    creditLimit: accountsByType.credit?.reduce((sum: number, acc: BankAccount) => sum + (acc.credit_data?.creditLimit || 0), 0) || 0,
    availableCredit: accountsByType.credit?.reduce((sum: number, acc: BankAccount) => sum + (acc.credit_data?.availableCreditLimit || 0), 0) || 0,
  };

  return {
    // Data
    accounts: accountsData || [],
    accountsByType,
    summary,
    totals,
    
    // States
    isLoading: isLoading || isLoadingSummary,
    error,

    // Actions
    refetch,
  };
}

// Hook for single account
export function useBankAccount(id: string) {
  const {
    data: account,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['bankAccount', id],
    queryFn: () => bankingService.getAccount(id),
    enabled: !!id,
  });

  // Fetch balance history
  const {
    data: balanceHistory,
    isLoading: isLoadingHistory
  } = useQuery({
    queryKey: ['accountBalanceHistory', id],
    queryFn: async () => {
      // Placeholder - this method doesn't exist in the service yet
      return [];
    },
    enabled: !!id,
  });

  return {
    account,
    balanceHistory,
    isLoading: isLoading || isLoadingHistory,
    error,
    refetch,
  };
}