import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { bankingService } from '@/services/banking.service';
import { Transaction, TransactionFilters } from '@/types/banking.types';

interface TransactionsResponse {
  results: Transaction[];
  count: number;
  next: string | null;
  previous: string | null;
}

interface UseTransactionsOptions {
  filters?: TransactionFilters;
  page?: number;
  queryOptions?: UseQueryOptions<TransactionsResponse>;
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
      bankingService.categorizeTransaction(transactionId, categoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
    ...options,
  });
}

export function useBulkCategorize(
  options?: UseMutationOptions<void, Error, { transactionIds: string[]; categoryId: number }>
) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ transactionIds, categoryId }) => 
      bankingService.bulkCategorize(transactionIds, categoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
    ...options,
  });
}