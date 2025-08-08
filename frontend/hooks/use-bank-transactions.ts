// Hook for managing bank transactions

import { useState, useCallback, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { bankingService } from '@/services/banking.service';
import type { Transaction, TransactionFilters } from '@/types/banking.types';

export function useBankTransactions(initialFilters?: TransactionFilters) {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<TransactionFilters>(initialFilters || {});
  const [selectedTransactions, setSelectedTransactions] = useState<Set<string>>(new Set());

  // Fetch transactions
  const {
    data: transactionsData,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['bankTransactions', filters],
    queryFn: async () => {
      const response = await bankingService.getTransactions(filters);
      return response;
    },
    staleTime: 30 * 1000, // 30 seconds
  });

  // Fetch statistics
  const {
    data: statistics,
    isLoading: isLoadingStats
  } = useQuery({
    queryKey: ['transactionStatistics', filters],
    queryFn: async () => {
      // Placeholder - this method doesn't exist in the service yet
      return {
        total_income: 0,
        total_expense: 0,
        balance: 0,
        transaction_count: 0,
        by_category: []
      };
    },
    staleTime: 60 * 1000,
  });

  // Update transaction
  const updateTransaction = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<Transaction> }) => 
      bankingService.updateTransaction(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] });
      queryClient.invalidateQueries({ queryKey: ['transactionStatistics'] });
      toast.success('Transação atualizada');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Erro ao atualizar transação');
    }
  });

  // Bulk categorize
  const bulkCategorize = useMutation({
    mutationFn: bankingService.bulkCategorize,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] });
      queryClient.invalidateQueries({ queryKey: ['transactionStatistics'] });
      toast.success(`${data.updated} transações categorizadas`);
      setSelectedTransactions(new Set());
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Erro ao categorizar transações');
    }
  });

  // AI categorize
  const aiCategorize = useMutation({
    mutationFn: async (data: any) => {
      // Placeholder - this method doesn't exist in the service yet
      return { message: 'AI categorization not implemented' };
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] });
      queryClient.invalidateQueries({ queryKey: ['transactionStatistics'] });
      toast.success(data.message);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Erro ao categorizar com IA');
    }
  });

  // Filter actions
  const updateFilters = useCallback((newFilters: Partial<TransactionFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({});
  }, []);

  // Selection actions
  const toggleTransaction = useCallback((id: string) => {
    setSelectedTransactions(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  }, []);

  const selectAll = useCallback(() => {
    if (transactionsData?.results) {
      setSelectedTransactions(new Set(transactionsData.results.map(t => t.id)));
    }
  }, [transactionsData]);

  const clearSelection = useCallback(() => {
    setSelectedTransactions(new Set());
  }, []);

  // Computed values
  const hasFilters = useMemo(() => {
    return Object.values(filters).some(value => 
      value !== undefined && value !== null && value !== ''
    );
  }, [filters]);

  const selectedTransactionsList = useMemo(() => {
    return transactionsData?.results.filter(t => selectedTransactions.has(t.id)) || [];
  }, [transactionsData, selectedTransactions]);

  return {
    // Data
    transactions: transactionsData?.results || [],
    pagination: {
      count: transactionsData?.count || 0,
      next: transactionsData?.next || null,
      previous: transactionsData?.previous || null,
    },
    statistics,
    filters,
    selectedTransactions,
    selectedTransactionsList,

    // States
    isLoading: isLoading || isLoadingStats,
    error,
    hasFilters,

    // Actions
    updateFilters,
    clearFilters,
    toggleTransaction,
    selectAll,
    clearSelection,
    updateTransaction: updateTransaction.mutate,
    bulkCategorize: bulkCategorize.mutate,
    aiCategorize: aiCategorize.mutate,
    refetch,

    // Loading states
    isUpdating: updateTransaction.isPending,
    isCategorizing: bulkCategorize.isPending || aiCategorize.isPending,
  };
}