import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { bankingService } from '@/services/banking.service';
import { BankAccount } from '@/types/banking.types';

export function useAccounts(options?: UseQueryOptions<BankAccount[]>) {
  return useQuery({
    queryKey: ['accounts'],
    queryFn: () => bankingService.getAccounts(),
    ...options,
  });
}

export function useBankAccounts(options?: UseQueryOptions<BankAccount[]>) {
  return useQuery({
    queryKey: ['bank-accounts'],
    queryFn: () => bankingService.getAccounts(),
    ...options,
  });
}