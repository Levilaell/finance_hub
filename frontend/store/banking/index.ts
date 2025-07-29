/**
 * Banking store exports - consolidated banking state management
 */

// Export individual stores
export * from './accounts-store';
export * from './transactions-store';
export * from './connections-store';

// Export a hook to use all banking stores together
import { useAccountsStore } from './accounts-store';
import { useTransactionsStore } from './transactions-store';
import { useConnectionsStore } from './connections-store';

export function useBankingStores() {
  const accounts = useAccountsStore();
  const transactions = useTransactionsStore();
  const connections = useConnectionsStore();

  return {
    accounts,
    transactions,
    connections,
  };
}

// Export a function to reset all banking stores
export function resetAllBankingStores() {
  useAccountsStore.getState().reset();
  useTransactionsStore.getState().reset();
  useConnectionsStore.getState().reset();
}