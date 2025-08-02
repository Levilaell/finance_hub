/**
 * Tests for banking service
 */
import { bankingService } from '@/services/banking.service';
import { apiClient } from '@/lib/api-client';
import { 
  PluggyConnector, 
  PluggyItem, 
  BankAccount, 
  Transaction,
  TransactionCategory 
} from '@/types/banking.types';

// Mock the API client
jest.mock('@/lib/api-client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  },
}));

describe('bankingService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getConnectors', () => {
    it('should fetch connectors', async () => {
      const mockConnectors: PluggyConnector[] = [
        {
          pluggy_id: 1,
          name: 'Test Bank',
          institution_url: 'https://testbank.com',
          image_url: 'https://testbank.com/logo.png',
          primary_color: '#000000',
          type: 'PERSONAL_BANK',
          country: 'BR',
          has_mfa: true,
          has_oauth: false,
          is_open_finance: true,
          is_sandbox: false,
          products: ['ACCOUNTS', 'TRANSACTIONS'],
          credentials: [],
        },
      ];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockConnectors });

      const result = await bankingService.getConnectors();

      expect(apiClient.get).toHaveBeenCalledWith('/banking/connectors/');
      expect(result).toEqual(mockConnectors);
    });

    it('should handle fetch error', async () => {
      (apiClient.get as jest.Mock).mockRejectedValue(new Error('Network error'));

      await expect(bankingService.getConnectors()).rejects.toThrow('Network error');
    });
  });

  describe('getBankAccounts', () => {
    it('should fetch bank accounts', async () => {
      const mockAccounts: BankAccount[] = [
        {
          id: '1',
          pluggy_account_id: 'pluggy_1',
          type: 'BANK',
          subtype: 'CHECKING_ACCOUNT',
          name: 'Test Account',
          display_name: 'Test Account',
          masked_number: '****1234',
          balance: 1000,
          currency_code: 'BRL',
          is_active: true,
          item_id: 'item_1',
          item_pluggy_id: 'pluggy_item_1',
          item: {
            id: 'item_1',
            pluggy_item_id: 'pluggy_item_1',
            status: 'UPDATED',
          },
          connector: {
            id: 1,
            name: 'Test Bank',
            image_url: 'https://testbank.com/logo.png',
            primary_color: '#000000',
            is_open_finance: false,
          },
          balance_date: new Date().toISOString(),
          pluggy_created_at: new Date().toISOString(),
          pluggy_updated_at: new Date().toISOString(),
        },
      ];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockAccounts });

      const result = await bankingService.getBankAccounts();

      expect(apiClient.get).toHaveBeenCalledWith('/banking/accounts/');
      expect(result).toEqual(mockAccounts);
    });
  });

  describe('syncAccount', () => {
    it('should sync account', async () => {
      const mockResponse = { success: true, task_id: 'task-123' };
      (apiClient.post as jest.Mock).mockResolvedValue({ data: mockResponse });

      const result = await bankingService.syncAccount('account-123');

      expect(apiClient.post).toHaveBeenCalledWith('/banking/accounts/account-123/sync/');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('createConnectToken', () => {
    it('should create connect token', async () => {
      const mockResponse = { 
        accessToken: 'test-token', 
        connectUrl: 'https://pluggy.ai/connect/test-token' 
      };
      (apiClient.post as jest.Mock).mockResolvedValue({ data: mockResponse });

      const options = {
        connector_ids: [1, 2],
        country_codes: ['BR'],
      };

      const result = await bankingService.createConnectToken(options);

      expect(apiClient.post).toHaveBeenCalledWith('/banking/connect/token/', options);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getTransactions', () => {
    it('should fetch transactions with filters', async () => {
      const mockTransactions = {
        count: 2,
        next: null,
        previous: null,
        results: [
          {
            id: '1',
            pluggy_transaction_id: 'txn_1',
            type: 'DEBIT',
            amount: 100,
            description: 'Test transaction',
            date: new Date().toISOString(),
            account_info: {
              id: 'acc_1',
              name: 'Test Account',
              type: 'BANK',
            },
          },
          {
            id: '2',
            pluggy_transaction_id: 'txn_2',
            type: 'CREDIT',
            amount: 200,
            description: 'Test credit',
            date: new Date().toISOString(),
            account_info: {
              id: 'acc_1',
              name: 'Test Account',
              type: 'BANK',
            },
          },
        ],
      };

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockTransactions });

      const filters = {
        account_id: 'acc_1',
        start_date: '2024-01-01',
        end_date: '2024-01-31',
        type: 'DEBIT',
      };

      const result = await bankingService.getTransactions(filters);

      expect(apiClient.get).toHaveBeenCalledWith('/banking/transactions/', {
        params: filters,
      });
      expect(result).toEqual(mockTransactions);
    });

    it('should fetch transactions without filters', async () => {
      const mockTransactions = {
        count: 0,
        next: null,
        previous: null,
        results: [],
      };

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockTransactions });

      const result = await bankingService.getTransactions();

      expect(apiClient.get).toHaveBeenCalledWith('/banking/transactions/', {
        params: {},
      });
      expect(result).toEqual(mockTransactions);
    });
  });

  describe('updateTransaction', () => {
    it('should update transaction', async () => {
      const mockUpdatedTransaction = {
        id: '1',
        pluggy_transaction_id: 'txn_1',
        category: 'cat_1',
        notes: 'Updated notes',
      };

      (apiClient.patch as jest.Mock).mockResolvedValue({ data: mockUpdatedTransaction });

      const updates = {
        category: 'cat_1',
        notes: 'Updated notes',
      };

      const result = await bankingService.updateTransaction('1', updates);

      expect(apiClient.patch).toHaveBeenCalledWith('/banking/transactions/1/', updates);
      expect(result).toEqual(mockUpdatedTransaction);
    });
  });

  describe('bulkCategorizeTransactions', () => {
    it('should bulk categorize transactions', async () => {
      const mockResponse = { updated: 3 };
      (apiClient.post as jest.Mock).mockResolvedValue({ data: mockResponse });

      const transactionIds = ['1', '2', '3'];
      const categoryId = 'cat_1';

      const result = await bankingService.bulkCategorizeTransactions(
        transactionIds,
        categoryId
      );

      expect(apiClient.post).toHaveBeenCalledWith('/banking/transactions/bulk-categorize/', {
        transaction_ids: transactionIds,
        category_id: categoryId,
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getCategories', () => {
    it('should fetch categories', async () => {
      const mockCategories: TransactionCategory[] = [
        {
          id: '1',
          name: 'Food',
          slug: 'food',
          type: 'expense',
          icon: '🍔',
          color: '#FF0000',
          is_system: false,
          is_active: true,
          order: 0,
        },
        {
          id: '2',
          name: 'Salary',
          slug: 'salary',
          type: 'income',
          icon: '💰',
          color: '#00FF00',
          is_system: true,
          is_active: true,
          order: 1,
        },
      ];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockCategories });

      const result = await bankingService.getCategories();

      expect(apiClient.get).toHaveBeenCalledWith('/banking/categories/');
      expect(result).toEqual(mockCategories);
    });
  });

  describe('createCategory', () => {
    it('should create category', async () => {
      const mockCategory: TransactionCategory = {
        id: '1',
        name: 'New Category',
        slug: 'new-category',
        type: 'expense',
        icon: '📦',
        color: '#0000FF',
        is_system: false,
        is_active: true,
        order: 0,
      };

      (apiClient.post as jest.Mock).mockResolvedValue({ data: mockCategory });

      const categoryData = {
        name: 'New Category',
        type: 'expense' as const,
        icon: '📦',
        color: '#0000FF',
      };

      const result = await bankingService.createCategory(categoryData);

      expect(apiClient.post).toHaveBeenCalledWith('/banking/categories/', categoryData);
      expect(result).toEqual(mockCategory);
    });
  });

  describe('deleteAccount', () => {
    it('should delete account', async () => {
      (apiClient.delete as jest.Mock).mockResolvedValue({ data: { success: true } });

      const result = await bankingService.deleteAccount('account-123');

      expect(apiClient.delete).toHaveBeenCalledWith('/banking/accounts/account-123/');
      expect(result).toEqual({ success: true });
    });
  });

  describe('disconnectItem', () => {
    it('should disconnect item', async () => {
      (apiClient.delete as jest.Mock).mockResolvedValue({ data: { success: true } });

      const result = await bankingService.disconnectItem('item-123');

      expect(apiClient.delete).toHaveBeenCalledWith('/banking/items/item-123/disconnect/');
      expect(result).toEqual({ success: true });
    });
  });

  describe('exportTransactions', () => {
    it('should export transactions', async () => {
      const mockBlob = new Blob(['csv data'], { type: 'text/csv' });
      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockBlob });

      const filters = {
        start_date: '2024-01-01',
        end_date: '2024-01-31',
        format: 'csv' as const,
      };

      const result = await bankingService.exportTransactions(filters);

      expect(apiClient.get).toHaveBeenCalledWith('/banking/transactions/export/', {
        params: filters,
        responseType: 'blob',
      });
      expect(result).toEqual(mockBlob);
    });
  });

  describe('needsReconnection', () => {
    it('should return true for error statuses', () => {
      const errorStatuses = ['LOGIN_ERROR', 'OUTDATED', 'ERROR'];
      
      errorStatuses.forEach(status => {
        expect(bankingService.needsReconnection(status)).toBe(true);
      });
    });

    it('should return false for normal statuses', () => {
      const normalStatuses = ['UPDATED', 'UPDATING', 'LOGIN_IN_PROGRESS'];
      
      normalStatuses.forEach(status => {
        expect(bankingService.needsReconnection(status)).toBe(false);
      });
    });

    it('should return false for undefined status', () => {
      expect(bankingService.needsReconnection(undefined)).toBe(false);
    });
  });

  describe('getDashboardData', () => {
    it('should fetch dashboard data', async () => {
      const mockDashboardData = {
        summary: {
          total_balance: 1000,
          total_income: 5000,
          total_expenses: 4000,
          accounts_count: 3,
        },
        recent_transactions: [],
        account_balances: [],
      };

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockDashboardData });

      const result = await bankingService.getDashboardData();

      expect(apiClient.get).toHaveBeenCalledWith('/banking/dashboard/');
      expect(result).toEqual(mockDashboardData);
    });
  });
});