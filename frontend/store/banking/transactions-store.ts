/**
 * Transactions store - handles transaction state management
 */
import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { bankingService } from '@/services/banking.service';
import { BankingCache } from '@/utils/banking-cache';
import type { 
  Transaction, 
  TransactionFilters, 
  PaginatedResponse,
  TransactionCategory 
} from '@/types/banking.types';

interface TransactionsState {
  // Data
  transactions: Transaction[];
  categories: TransactionCategory[];
  
  // Filters and pagination
  filters: TransactionFilters;
  currentPage: number;
  pageSize: number;
  totalCount: number;
  totalPages: number;

  // Selection
  selectedTransactionIds: Set<string>;

  // Loading states
  isLoading: boolean;
  isLoadingCategories: boolean;
  isUpdating: Record<string, boolean>; // transactionId -> isUpdating

  // Error states
  error: Error | null;

  // Actions
  fetchTransactions: (page?: number, forceRefresh?: boolean) => Promise<void>;
  fetchCategories: (forceRefresh?: boolean) => Promise<void>;
  setFilters: (filters: Partial<TransactionFilters>) => void;
  clearFilters: () => void;
  updateTransaction: (id: string, data: Partial<Transaction>) => Promise<void>;
  bulkCategorize: (transactionIds: string[], categoryId: string) => Promise<void>;
  selectTransaction: (id: string, selected: boolean) => void;
  selectAllTransactions: (selected: boolean) => void;
  clearSelection: () => void;
  reset: () => void;
}

const initialState: Omit<TransactionsState, 
  'fetchTransactions' | 'fetchCategories' | 'setFilters' | 'clearFilters' | 
  'updateTransaction' | 'bulkCategorize' | 'selectTransaction' | 
  'selectAllTransactions' | 'clearSelection' | 'reset'
> = {
  transactions: [],
  categories: [],
  filters: {},
  currentPage: 1,
  pageSize: 50,
  totalCount: 0,
  totalPages: 0,
  selectedTransactionIds: new Set(),
  isLoading: false,
  isLoadingCategories: false,
  isUpdating: {},
  error: null,
};

export const useTransactionsStore = create<TransactionsState>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      ...initialState,

      fetchTransactions: async (page = 1, forceRefresh = false) => {
        const { filters, pageSize } = get();
        const cacheKey = BankingCache.createKey(
          'transactions',
          JSON.stringify({ ...filters, page, pageSize })
        );

        // Check cache first
        if (!forceRefresh) {
          const cached = BankingCache.get<PaginatedResponse<Transaction>>(cacheKey);
          if (cached) {
            set({
              transactions: cached.results,
              currentPage: page,
              totalCount: cached.count,
              totalPages: Math.ceil(cached.count / pageSize),
              isLoading: false,
            });
            return;
          }
        }

        set({ isLoading: true, error: null });

        try {
          const response = await bankingService.getTransactions({
            ...filters,
            page,
            page_size: pageSize,
          });

          // Cache the data
          BankingCache.set(cacheKey, response, 5 * 60 * 1000); // 5 minutes

          set({
            transactions: response.results,
            currentPage: page,
            totalCount: response.count,
            totalPages: Math.ceil(response.count / pageSize),
            isLoading: false,
          });
        } catch (error) {
          set({ error: error as Error, isLoading: false });
          throw error;
        }
      },

      fetchCategories: async (forceRefresh = false) => {
        const cacheKey = BankingCache.createKey('categories');

        // Check cache first
        if (!forceRefresh) {
          const cached = BankingCache.get<TransactionCategory[]>(cacheKey);
          if (cached) {
            set({ categories: cached, isLoadingCategories: false });
            return;
          }
        }

        set({ isLoadingCategories: true });

        try {
          const categories = await bankingService.getCategories();
          
          // Cache the data
          BankingCache.set(cacheKey, categories);
          
          set({ categories, isLoadingCategories: false });
        } catch (error) {
          set({ isLoadingCategories: false });
          throw error;
        }
      },

      setFilters: (newFilters: Partial<TransactionFilters>) => {
        const currentFilters = get().filters;
        const updatedFilters = { ...currentFilters, ...newFilters };
        
        set({ filters: updatedFilters });
        
        // Fetch with new filters
        get().fetchTransactions(1, true);
      },

      clearFilters: () => {
        set({ filters: {} });
        get().fetchTransactions(1, true);
      },

      updateTransaction: async (id: string, data: Partial<Transaction>) => {
        // Set updating state
        set((state) => ({
          isUpdating: { ...state.isUpdating, [id]: true }
        }));

        try {
          const updated = await bankingService.updateTransaction(id, data);
          
          // Update in state
          set((state) => ({
            transactions: state.transactions.map((t) =>
              t.id === id ? { ...t, ...updated } : t
            ),
          }));
          
          // Clear relevant cache
          const { filters, currentPage, pageSize } = get();
          const cacheKey = BankingCache.createKey(
            'transactions',
            JSON.stringify({ ...filters, page: currentPage, pageSize })
          );
          BankingCache.remove(cacheKey);
        } finally {
          // Clear updating state
          set((state) => {
            const { [id]: _, ...rest } = state.isUpdating;
            return { isUpdating: rest };
          });
        }
      },

      bulkCategorize: async (transactionIds: string[], categoryId: string) => {
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
              selectedTransactionIds: new Set(), // Clear selection
            }));

            // Clear cache
            BankingCache.clear();
          }
        } catch (error) {
          throw error;
        }
      },

      selectTransaction: (id: string, selected: boolean) => {
        set((state) => {
          const newSelection = new Set(state.selectedTransactionIds);
          if (selected) {
            newSelection.add(id);
          } else {
            newSelection.delete(id);
          }
          return { selectedTransactionIds: newSelection };
        });
      },

      selectAllTransactions: (selected: boolean) => {
        set((state) => ({
          selectedTransactionIds: selected
            ? new Set(state.transactions.map((t) => t.id))
            : new Set(),
        }));
      },

      clearSelection: () => {
        set({ selectedTransactionIds: new Set() });
      },

      reset: () => {
        set(initialState);
        // Clear related cache
        BankingCache.clear();
      },
    })),
    {
      name: 'transactions-store',
    }
  )
);

// Selectors
export const getSelectedTransactions = (state: TransactionsState) =>
  state.transactions.filter((t) => state.selectedTransactionIds.has(t.id));

export const getTransactionsByCategory = (state: TransactionsState, categoryId: string) =>
  state.transactions.filter((t) => t.category === categoryId);

export const getUncategorizedTransactions = (state: TransactionsState) =>
  state.transactions.filter((t) => !t.category);

export const isTransactionSelected = (state: TransactionsState, id: string) =>
  state.selectedTransactionIds.has(id);

export const getTransactionCategories = (state: TransactionsState) => {
  const categoryMap = new Map<string, number>();
  
  state.transactions.forEach((transaction) => {
    if (transaction.category) {
      categoryMap.set(
        transaction.category,
        (categoryMap.get(transaction.category) || 0) + 1
      );
    }
  });
  
  return Array.from(categoryMap.entries()).map(([categoryId, count]) => ({
    categoryId,
    count,
    category: state.categories.find((c) => c.id === categoryId),
  }));
};