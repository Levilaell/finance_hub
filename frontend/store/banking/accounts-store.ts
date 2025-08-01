/**
 * Accounts store - handles bank account state management
 */
import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { bankingService } from '@/services/banking.service';
import { BankingCache } from '@/utils/banking-cache';
import type { BankAccount } from '@/types/banking.types';

interface AccountsSummaryData {
  total_balance: number;
  total_accounts: number;
  by_type: Array<{
    type: string;
    count: number;
    total_balance: number;
  }>;
  last_update?: string;
}

interface AccountsState {
  // Data
  accounts: BankAccount[];
  selectedAccountId: string | null;
  summary: AccountsSummaryData | null;

  // Loading states
  isLoading: boolean;
  isSyncing: Record<string, boolean>; // accountId -> isSyncing

  // Error states
  error: Error | null;

  // Actions
  fetchAccounts: (forceRefresh?: boolean) => Promise<void>;
  fetchAccountsSummary: (forceRefresh?: boolean) => Promise<void>;
  selectAccount: (accountId: string | null) => void;
  syncAccount: (accountId: string) => Promise<void>;
  reset: () => void;
}

const initialState: Omit<AccountsState, 'fetchAccounts' | 'fetchAccountsSummary' | 'selectAccount' | 'syncAccount' | 'reset'> = {
  accounts: [],
  selectedAccountId: null,
  summary: null,
  isLoading: false,
  isSyncing: {},
  error: null,
};

export const useAccountsStore = create<AccountsState>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      ...initialState,

      fetchAccounts: async (forceRefresh = false) => {
        const cacheKey = BankingCache.createKey('accounts');
        
        // Check cache first
        if (!forceRefresh) {
          const cached = BankingCache.get<BankAccount[]>(cacheKey);
          if (cached) {
            set({ accounts: cached, isLoading: false });
            return;
          }
        }

        set({ isLoading: true, error: null });

        try {
          const accounts = await bankingService.getAccounts();
          
          // Cache the data
          BankingCache.set(cacheKey, accounts);
          
          set({ accounts, isLoading: false });
        } catch (error) {
          set({ error: error as Error, isLoading: false });
          throw error;
        }
      },

      fetchAccountsSummary: async (forceRefresh = false) => {
        const cacheKey = BankingCache.createKey('accounts', 'summary');
        
        // Check cache first
        if (!forceRefresh) {
          const cached = BankingCache.get<AccountsSummaryData>(cacheKey);
          if (cached) {
            set({ summary: cached });
            return;
          }
        }

        try {
          const summary = await bankingService.getAccountsSummary();
          
          // Cache the data
          BankingCache.set(cacheKey, summary);
          
          set({ summary });
        } catch (error) {
          // Error is handled silently - summary remains unchanged
        }
      },

      selectAccount: (accountId: string | null) => {
        set({ selectedAccountId: accountId });
      },

      syncAccount: async (accountId: string) => {
        // Set syncing state
        set((state) => ({
          isSyncing: { ...state.isSyncing, [accountId]: true }
        }));

        try {
          const response = await bankingService.syncAccount(accountId);
          
          if (response.success) {
            // Refresh accounts after sync
            await get().fetchAccounts(true);
            
            // Clear specific cache entries
            BankingCache.remove(BankingCache.createKey('transactions', accountId));
          }
        } finally {
          // Clear syncing state
          set((state) => {
            const { [accountId]: _, ...rest } = state.isSyncing;
            return { isSyncing: rest };
          });
        }
      },

      reset: () => {
        set(initialState);
        // Clear related cache
        BankingCache.remove(BankingCache.createKey('accounts'));
        BankingCache.remove(BankingCache.createKey('accounts', 'summary'));
      },
    })),
    {
      name: 'accounts-store',
    }
  )
);

// Selectors
export const getSelectedAccount = (state: AccountsState) => 
  state.accounts.find(account => account.id === state.selectedAccountId);

export const getAccountsByType = (state: AccountsState, type: string) =>
  state.accounts.filter(account => account.type === type);

export const getActiveAccounts = (state: AccountsState) =>
  state.accounts.filter(account => account.is_active);

export const isAccountSyncing = (state: AccountsState, accountId: string) =>
  state.isSyncing[accountId] || false;