/**
 * Banking store using Zustand - Simplified version
 * Only maintaining actively used functionality
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { BankAccount, SyncResponse } from '@/types/banking.types';
import { bankingService } from '@/services/banking.service';

interface BankingStore {
  // Data
  accounts: BankAccount[];

  // Loading states
  loadingAccounts: boolean;

  // Errors
  accountsError: string | null;

  // Actions
  fetchAccounts: () => Promise<void>;
  syncAccount: (accountId: string) => Promise<SyncResponse>;
}

export const useBankingStore = create<BankingStore>()(
  devtools(
    (set, get) => ({
      // Data
      accounts: [],

      // Loading states
      loadingAccounts: false,

      // Errors
      accountsError: null,

      // Actions
      fetchAccounts: async () => {
        set({ loadingAccounts: true, accountsError: null });

        try {
          const accounts = await bankingService.getAccounts();
          set({ accounts, loadingAccounts: false });
        } catch (error: any) {
          set({
            accountsError: error.message || 'Failed to fetch accounts',
            loadingAccounts: false,
          });
        }
      },

      syncAccount: async (accountId: string) => {
        try {
          const response = await bankingService.syncAccount(accountId);

          // If successful, refresh account data
          if (response.success) {
            await get().fetchAccounts();
          }

          return response;
        } catch (error: any) {
          console.error('Failed to sync account:', error);
          throw error;
        }
      },
    }),
    {
      name: 'banking-store',
    }
  )
);