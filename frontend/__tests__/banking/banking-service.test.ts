/**
 * Tests for banking service
 */
import { bankingService } from '@/services/banking.service';
import apiClient from '@/lib/api-client';

// Mock the API client
jest.mock('@/lib/api-client');

describe('BankingService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getConnectors', () => {
    it('should fetch connectors successfully', async () => {
      const mockConnectors = [
        { pluggy_id: 1, name: 'Bank A', type: 'PERSONAL_BANK' },
        { pluggy_id: 2, name: 'Bank B', type: 'PERSONAL_BANK' },
      ];

      (apiClient.get as jest.Mock).mockResolvedValue(mockConnectors);

      const result = await bankingService.getConnectors();

      expect(apiClient.get).toHaveBeenCalledWith('/api/banking/connectors/', undefined);
      expect(result).toEqual(mockConnectors);
    });

    it('should handle connector filtering', async () => {
      const params = { type: 'PERSONAL_BANK', is_open_finance: true };
      
      await bankingService.getConnectors(params);

      expect(apiClient.get).toHaveBeenCalledWith('/api/banking/connectors/', params);
    });
  });

  describe('createConnectToken', () => {
    it('should create connect token successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          connect_token: 'test-token-123',
          connect_url: 'https://connect.pluggy.ai?token=test-token-123',
        },
      };

      (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

      const result = await bankingService.createConnectToken();

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/banking/pluggy/connect-token/',
        {}
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle connect token errors', async () => {
      const mockError = new Error('Failed to create token');
      (apiClient.post as jest.Mock).mockRejectedValue(mockError);

      const result = await bankingService.createConnectToken();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Failed to create connect token');
    });
  });

  describe('syncAccount', () => {
    it('should sync account successfully', async () => {
      const accountId = 'account-123';
      const mockResponse = {
        success: true,
        message: 'Sync started',
        data: {
          account: { id: accountId, balance: 1000 },
        },
      };

      (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

      const result = await bankingService.syncAccount(accountId);

      expect(apiClient.post).toHaveBeenCalledWith(
        `/api/banking/accounts/${accountId}/sync/`,
        {}
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle sync errors', async () => {
      const accountId = 'account-123';
      const mockError = {
        response: {
          data: {
            success: false,
            error: {
              code: 'invalid_credentials',
              message: 'Invalid credentials',
            },
          },
        },
      };

      (apiClient.post as jest.Mock).mockRejectedValue(mockError);

      const result = await bankingService.syncAccount(accountId);

      expect(result.success).toBe(false);
      expect(result).toEqual(mockError.response.data);
    });
  });

  describe('updateTransaction', () => {
    it('should update transaction successfully', async () => {
      const transactionId = 'trans-123';
      const updateData = {
        category: 'cat-456',
        notes: 'Updated notes',
      };
      const mockResponse = {
        id: transactionId,
        ...updateData,
      };

      (apiClient.patch as jest.Mock).mockResolvedValue(mockResponse);

      const result = await bankingService.updateTransaction(transactionId, updateData);

      expect(apiClient.patch).toHaveBeenCalledWith(
        `/api/banking/transactions/${transactionId}/`,
        updateData
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('formatCurrency', () => {
    it('should format BRL currency correctly', () => {
      const result = bankingService.formatCurrency(1234.56);
      expect(result).toBe('R$ 1.234,56');
    });

    it('should format USD currency correctly', () => {
      const result = bankingService.formatCurrency(1234.56, 'USD');
      expect(result).toMatch(/1[,.]234[,.]56/); // Format may vary by locale
    });
  });

  describe('formatDate', () => {
    it('should format today\'s date', () => {
      const today = new Date();
      const result = bankingService.formatDate(today.toISOString());
      expect(result).toBe('Hoje');
    });

    it('should format yesterday\'s date', () => {
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const result = bankingService.formatDate(yesterday.toISOString());
      expect(result).toBe('Ontem');
    });

    it('should format dates within a week', () => {
      const daysAgo = new Date();
      daysAgo.setDate(daysAgo.getDate() - 5);
      const result = bankingService.formatDate(daysAgo.toISOString());
      expect(result).toBe('5 dias atrás');
    });

    it('should format older dates', () => {
      const oldDate = new Date('2024-01-01');
      const result = bankingService.formatDate(oldDate.toISOString());
      expect(result).toMatch(/\d{2}\/\d{2}\/\d{4}/);
    });
  });

  describe('needsReconnection', () => {
    it('should return true for error statuses', () => {
      const errorStatuses = ['LOGIN_ERROR', 'ERROR', 'OUTDATED', 'WAITING_USER_INPUT'];
      
      errorStatuses.forEach(status => {
        const account = { item_status: status } as any;
        expect(bankingService.needsReconnection(account)).toBe(true);
      });
    });

    it('should return false for valid statuses', () => {
      const validStatuses = ['UPDATED', 'UPDATING', 'LOGIN_IN_PROGRESS'];
      
      validStatuses.forEach(status => {
        const account = { item_status: status } as any;
        expect(bankingService.needsReconnection(account)).toBe(false);
      });
    });

    it('should return false for accounts without status', () => {
      const account = {} as any;
      expect(bankingService.needsReconnection(account)).toBe(false);
    });
  });
});