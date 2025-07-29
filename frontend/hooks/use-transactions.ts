import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { bankingService } from '@/services/banking.service';
import { Transaction, TransactionFilters, PaginatedResponse, BulkCategorizeResponse } from '@/types/banking.types';

interface UseTransactionsOptions {
  filters?: TransactionFilters;
  page?: number;
  queryOptions?: UseQueryOptions<PaginatedResponse<Transaction>>;
}

export function useTransactions({ filters, page = 1, queryOptions }: UseTransactionsOptions = {}) {
  return useQuery({
    queryKey: ['transactions', filters, page],
    queryFn: () => bankingService.getTransactions({ ...filters, page }),
    ...queryOptions,
  });
}

export function useCategorizeTransaction(
  options?: UseMutationOptions<Transaction, Error, { transactionId: string; categoryId: number }>
) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ transactionId, categoryId }) => 
      bankingService.updateTransaction(transactionId, { category: categoryId.toString() }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
    ...options,
  });
}

export function useBulkCategorize(
  options?: UseMutationOptions<BulkCategorizeResponse, Error, { transactionIds: string[]; categoryId: string }>
) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ transactionIds, categoryId }) => 
      bankingService.bulkCategorize({ transaction_ids: transactionIds, category_id: categoryId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
    ...options,
  });
}