import { create } from "zustand";
import { BankAccount, BankTransaction, TransactionFilter } from "@/types";
import { bankingService } from "@/services/banking.service";

interface BankProvider {
  id: number;
  name: string;
  code: string;
  logo?: string;
  color?: string;
  is_open_banking: boolean;
  supports_pix: boolean;
  supports_ted: boolean;
}

interface BankingState {
  // Accounts
  accounts: BankAccount[];
  providers: BankProvider[];
  selectedAccountId: string | null;
  loading: boolean;
  error: string | null;
  isLoadingAccounts: boolean;
  accountsError: string | null;

  // Transactions
  transactions: BankTransaction[];
  transactionFilters: TransactionFilter;
  totalTransactions: number;
  currentPage: number;
  pageSize: number;
  isLoadingTransactions: boolean;
  transactionsError: string | null;

  // Actions - Accounts
  fetchAccounts: () => Promise<void>;
  fetchProviders: () => Promise<void>;
  selectAccount: (accountId: string | null) => void;
  syncAccount: (accountId: string) => Promise<void>;
  deleteAccount: (accountId: string) => Promise<void>;
  
  // Actions - Transactions
  fetchTransactions: (page?: number) => Promise<void>;
  setTransactionFilters: (filters: Partial<TransactionFilter>) => void;
  clearTransactionFilters: () => void;
  updateTransaction: (id: string, data: Partial<BankTransaction>) => void;
  setPageSize: (size: number) => void;
}

const defaultFilters: TransactionFilter = {
  account_id: undefined,
  category_id: undefined,
  start_date: undefined,
  end_date: undefined,
  min_amount: undefined,
  max_amount: undefined,
  transaction_type: undefined,
  search: undefined,
};

export const useBankingStore = create<BankingState>((set, get) => ({
  // Initial state - Accounts
  accounts: [],
  providers: [],
  selectedAccountId: null,
  loading: false,
  error: null,
  isLoadingAccounts: false,
  accountsError: null,

  // Initial state - Transactions
  transactions: [],
  transactionFilters: defaultFilters,
  totalTransactions: 0,
  currentPage: 1,
  pageSize: 20,
  isLoadingTransactions: false,
  transactionsError: null,

  // Actions - Accounts
  fetchAccounts: async () => {
    set({ loading: true, error: null });
    try {
      const { bankingService } = await import('@/services/banking.service');
      const data = await bankingService.getBankAccounts();
      
      // Handle both paginated and direct array responses
      const accounts = data.results || (Array.isArray(data) ? data : []);
      set({ accounts, loading: false });
    } catch (error: any) {
      set({
        error: error.message || "Failed to fetch accounts",
        loading: false,
      });
    }
  },

  fetchProviders: async () => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      
      // Try to fetch from API first if we have a token
      if (token) {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/banking/providers/`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          const data = await response.json();
          set({ providers: Array.isArray(data) ? data : [] });
          return;
        }
      }
      
      // Always fallback to local data (works even without authentication)
      const mockProviders = await import('@/data/bank-providers.json');
      set({ providers: Array.isArray(mockProviders.default) ? mockProviders.default : [] });
    } catch (error: any) {
      // Use mock data as fallback
      try {
        const mockProviders = await import('@/data/bank-providers.json');
        set({ providers: Array.isArray(mockProviders.default) ? mockProviders.default : [] });
      } catch (fallbackError) {
        set({ providers: [] });
      }
    }
  },

  selectAccount: (accountId) => {
    set({ selectedAccountId: accountId });
    // When selecting an account, update the filter and fetch transactions
    if (accountId) {
      get().setTransactionFilters({ account_id: accountId });
    }
  },

  syncAccount: async (accountId) => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      if (!token) throw new Error('Authentication required');

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/banking/pluggy/accounts/${accountId}/sync/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      // Tentar fazer parse do JSON apenas se for JSON válido
      let data;
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        // Se não for JSON (provavelmente HTML de erro), criar estrutura de erro
        data = {
          error: 'Invalid response format',
          message: 'Server returned non-JSON response'
        };
      }
      
      if (!response.ok) {
        // Se for 403, provavelmente precisa reconectar
        if (response.status === 403) {
          return {
            success: false,
            error_code: data.error_code || 'WAITING_USER_ACTION',
            message: data.message || 'Reautenticação necessária',
            reconnection_required: true,
            data: data
          };
        }
        
        // Outros erros
        return {
          success: false,
          error_code: data.error_code,
          message: data.message || data.error || 'Failed to sync account',
          reconnection_required: data.reconnection_required,
          data: data
        };
      }
      
      // Refresh accounts after successful sync
      await get().fetchAccounts();
      
      // Retornar dados de sucesso
      return {
        success: true,
        data: data.data || data,
        message: data.message
      };
    } catch (error: any) {
      console.error('Sync account error:', error);
      return {
        success: false,
        message: error.message || 'Network error',
        error: error
      };
    }
  },

  deleteAccount: async (accountId) => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      if (!token) throw new Error('Authentication required');

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/banking/accounts/${accountId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) throw new Error('Failed to delete account');
      
      // Refresh accounts after deletion
      await get().fetchAccounts();
    } catch (error: any) {
      throw error;
    }
  },

  // Actions - Transactions
  fetchTransactions: async (page = 1) => {
    const { transactionFilters, pageSize } = get();
    set({ isLoadingTransactions: true, transactionsError: null, currentPage: page });
    
    try {
      const response = await bankingService.getTransactions({
        ...transactionFilters,
        page,
        page_size: pageSize,
      });
      
      set({
        transactions: response.results,
        totalTransactions: response.count,
        isLoadingTransactions: false,
      });
    } catch (error: any) {
      set({
        transactionsError: error.message || "Failed to fetch transactions",
        isLoadingTransactions: false,
      });
    }
  },

  setTransactionFilters: (filters) => {
    set((state) => ({
      transactionFilters: { ...state.transactionFilters, ...filters },
    }));
    // Fetch transactions with new filters
    get().fetchTransactions(1);
  },

  clearTransactionFilters: () => {
    set({ transactionFilters: defaultFilters });
    get().fetchTransactions(1);
  },

  updateTransaction: (id, data) => {
    set((state) => ({
      transactions: state.transactions.map((transaction) =>
        transaction.id === id ? { ...transaction, ...data } : transaction
      ),
    }));
  },

  setPageSize: (size) => {
    set({ pageSize: size });
    get().fetchTransactions(1);
  },
}));