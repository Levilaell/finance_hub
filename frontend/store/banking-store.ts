/**
 * Banking store using Zustand - Pluggy Integration
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import {
  PluggyConnector,
  PluggyItem,
  BankAccount,
  Transaction,
  TransactionCategory,
  TransactionFilters,
  BankingStoreState,
  SyncResponse,
} from '@/types/banking.types';
import { bankingService } from '@/services/banking.service';

interface BankingStore extends BankingStoreState {
  // ===== Actions - Connectors =====
  fetchConnectors: () => Promise<void>;
  
  // ===== Actions - Items =====
  fetchItems: () => Promise<void>;
  syncItem: (itemId: string) => Promise<void>;
  disconnectItem: (itemId: string) => Promise<void>;
  
  // ===== Actions - Accounts =====
  fetchAccounts: () => Promise<void>;
  selectAccount: (accountId: string | null) => void;
  syncAccount: (accountId: string) => Promise<SyncResponse>;
  
  // ===== Actions - Transactions =====
  fetchTransactions: (page?: number) => Promise<void>;
  updateTransaction: (id: string, data: Partial<Transaction>) => Promise<void>;
  bulkCategorizeTransactions: (transactionIds: string[], categoryId: string) => Promise<void>;
  setTransactionFilters: (filters: Partial<TransactionFilters>) => void;
  clearTransactionFilters: () => void;
  
  // ===== Actions - Categories =====
  fetchCategories: () => Promise<void>;
  createCategory: (data: Partial<TransactionCategory>) => Promise<void>;
  updateCategory: (id: string, data: Partial<TransactionCategory>) => Promise<void>;
  deleteCategory: (id: string) => Promise<void>;
  
  // ===== Connect State Actions =====
  setConnectState: (state: Partial<BankingStoreState['connectState']>) => void;
  addSyncError: (error: any) => void;
  clearSyncErrors: () => void;
  setSyncingAccount: (accountId: string, syncing: boolean) => void;
  
  // ===== Utility Actions =====
  reset: () => void;
}

const initialState: BankingStoreState = {
  // Data
  connectors: [],
  items: [],
  accounts: [],
  transactions: [],
  categories: [],
  
  // UI State
  selectedAccountId: null,
  transactionFilters: {},
  connectState: {
    isOpen: false,
    token: null,
    mode: 'connect',
  },
  
  // Loading states
  loadingConnectors: false,
  loadingItems: false,
  loadingAccounts: false,
  loadingTransactions: false,
  syncingAccounts: [],
  
  // Errors
  connectorsError: null,
  itemsError: null,
  accountsError: null,
  transactionsError: null,
  syncErrors: [],
  
  // Pagination
  transactionsPagination: {
    page: 1,
    pageSize: 50,
    totalCount: 0,
    totalPages: 0,
  },
};

export const useBankingStore = create<BankingStore>()(
  devtools(
    (set, get) => ({
      ...initialState,
      
      // ===== Actions - Connectors =====
      
      fetchConnectors: async () => {
        set({ loadingConnectors: true, connectorsError: null });
        
        try {
          const connectors = await bankingService.getConnectors();
          set({ connectors, loadingConnectors: false });
        } catch (error: any) {
          set({
            connectorsError: error.message || 'Failed to fetch connectors',
            loadingConnectors: false,
          });
        }
      },
      
      // ===== Actions - Items =====
      
      fetchItems: async () => {
        set({ loadingItems: true, itemsError: null });
        
        try {
          const response = await bankingService.getItems();
          set({ items: response.results, loadingItems: false });
        } catch (error: any) {
          set({
            itemsError: error.message || 'Failed to fetch items',
            loadingItems: false,
          });
        }
      },
      
      syncItem: async (itemId: string) => {
        try {
          await bankingService.syncItem(itemId);
          // Refresh items and accounts after sync
          await Promise.all([
            get().fetchItems(),
            get().fetchAccounts(),
          ]);
        } catch (error: any) {
          throw error;
        }
      },
      
      disconnectItem: async (itemId: string) => {
        try {
          await bankingService.disconnectItem(itemId);
          // Remove item and its accounts from state
          set((state) => ({
            items: state.items.filter((item) => item.id !== itemId),
            accounts: state.accounts.filter(
              (account) => account.item.id !== itemId
            ),
          }));
        } catch (error: any) {
          throw error;
        }
      },
      
      // ===== Actions - Accounts =====
      
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
      
      selectAccount: (accountId: string | null) => {
        set({ selectedAccountId: accountId });
        
        // Update transaction filter when selecting account
        if (accountId) {
          get().setTransactionFilters({ account_id: accountId });
        }
      },
      
      syncAccount: async (accountId: string) => {
        // Add account to syncing list
        get().setSyncingAccount(accountId, true);
        
        try {
          const response = await bankingService.syncAccount(accountId);
          
          // If successful, refresh account data
          if (response.success) {
            await get().fetchAccounts();
            
            // If transactions were synced, refresh them too
            if (response.data?.sync_stats?.transactions_synced) {
              await get().fetchTransactions();
            }
          } else if (response.reconnection_required) {
            // Add sync error if reconnection required
            get().addSyncError({
              accountId,
              accountName: get().accounts.find(a => a.id === accountId)?.name || 'Unknown',
              message: response.message || 'Reconnection required',
              requiresReconnect: true,
              errorCode: response.error_code
            });
          }
          
          return response;
        } catch (error: any) {
          console.error('Failed to sync account:', error);
          get().addSyncError({
            accountId,
            accountName: get().accounts.find(a => a.id === accountId)?.name || 'Unknown',
            message: error.message || 'Sync failed',
            requiresReconnect: false
          });
          throw error;
        } finally {
          // Remove account from syncing list
          get().setSyncingAccount(accountId, false);
        }
      },
      
      // ===== Actions - Transactions =====
      
      fetchTransactions: async (page = 1) => {
        const { transactionFilters, transactionsPagination } = get();
        
        set({ loadingTransactions: true, transactionsError: null });
        
        try {
          const response = await bankingService.getTransactions({
            ...transactionFilters,
            page,
            page_size: transactionsPagination.pageSize,
          });
          
          set({
            transactions: response.results,
            transactionsPagination: {
              ...transactionsPagination,
              page,
              totalCount: response.count,
              totalPages: Math.ceil(response.count / transactionsPagination.pageSize),
            },
            loadingTransactions: false,
          });
        } catch (error: any) {
          set({
            transactionsError: error.message || 'Failed to fetch transactions',
            loadingTransactions: false,
          });
        }
      },
      
      updateTransaction: async (id: string, data: Partial<Transaction>) => {
        try {
          const updated = await bankingService.updateTransaction(id, {
            category: data.category,
            notes: data.notes,
            tags: data.tags,
          });
          
          // Update transaction in state
          set((state) => ({
            transactions: state.transactions.map((t) =>
              t.id === id ? { ...t, ...updated } : t
            ),
          }));
        } catch (error: any) {
          console.error('Failed to update transaction:', error);
          throw error;
        }
      },
      
      bulkCategorizeTransactions: async (
        transactionIds: string[],
        categoryId: string
      ) => {
        try {
          const response = await bankingService.bulkCategorize({
            transaction_ids: transactionIds,
            category_id: categoryId,
          });
          
          if (response.success) {
            // Update transactions in state
            set((state) => ({
              transactions: state.transactions.map((t) =>
                transactionIds.includes(t.id)
                  ? { ...t, category: categoryId }
                  : t
              ),
            }));
          }
        } catch (error: any) {
          console.error('Failed to bulk categorize:', error);
          throw error;
        }
      },
      
      setTransactionFilters: (filters: Partial<TransactionFilters>) => {
        set((state) => ({
          transactionFilters: { ...state.transactionFilters, ...filters },
        }));
        
        // Fetch transactions with new filters
        get().fetchTransactions(1);
      },
      
      clearTransactionFilters: () => {
        set({ transactionFilters: {} });
        get().fetchTransactions(1);
      },
      
      // ===== Actions - Categories =====
      
      fetchCategories: async () => {
        try {
          const categories = await bankingService.getCategories();
          set({ categories });
        } catch (error: any) {
          console.error('Failed to fetch categories:', error);
        }
      },
      
      createCategory: async (data: Partial<TransactionCategory>) => {
        try {
          const category = await bankingService.createCategory(data);
          set((state) => ({
            categories: [...state.categories, category],
          }));
        } catch (error: any) {
          console.error('Failed to create category:', error);
          throw error;
        }
      },
      
      updateCategory: async (id: string, data: Partial<TransactionCategory>) => {
        try {
          const updated = await bankingService.updateCategory(id, data);
          set((state) => ({
            categories: state.categories.map((c) =>
              c.id === id ? updated : c
            ),
          }));
        } catch (error: any) {
          console.error('Failed to update category:', error);
          throw error;
        }
      },
      
      deleteCategory: async (id: string) => {
        try {
          await bankingService.deleteCategory(id);
          set((state) => ({
            categories: state.categories.filter((c) => c.id !== id),
          }));
        } catch (error: any) {
          console.error('Failed to delete category:', error);
          throw error;
        }
      },
      
      // ===== Connect State Actions =====
      
      setConnectState: (newState: Partial<BankingStoreState['connectState']>) => {
        set((state) => ({
          connectState: { ...state.connectState, ...newState }
        }));
      },
      
      addSyncError: (error: any) => {
        set((state) => ({
          syncErrors: [...state.syncErrors.filter(e => e.accountId !== error.accountId), error]
        }));
      },
      
      clearSyncErrors: () => {
        set({ syncErrors: [] });
      },
      
      setSyncingAccount: (accountId: string, syncing: boolean) => {
        set((state) => ({
          syncingAccounts: syncing 
            ? [...state.syncingAccounts.filter(id => id !== accountId), accountId]
            : state.syncingAccounts.filter(id => id !== accountId)
        }));
      },
      
      // ===== Utility Actions =====
      
      reset: () => {
        set(initialState);
      },
    }),
    {
      name: 'banking-store',
    }
  )
);