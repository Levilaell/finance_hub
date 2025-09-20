/**
 * Banking service following Pluggy API structure
 */
import apiClient from '@/lib/api-client';
import { formatCurrency } from '@/lib/utils';
import {
  PluggyConnector,
  PluggyItem,
  PluggyItemStatus,
  BankAccount,
  Transaction,
  TransactionCategory,
  TransactionFilters,
  PaginatedResponse,
  ConnectTokenRequest,
  ConnectTokenResponse,
  CallbackRequest,
  CallbackResponse,
  SyncRequest,
  SyncResponse,
  BulkCategorizeRequest,
  BulkCategorizeResponse,
  DashboardData,
  DisconnectItemResponse,
} from '@/types/banking.types';

class BankingService {
  // ===== Connectors (Banks) =====
  
  async getConnectors(params?: {
    type?: string;
    is_open_finance?: boolean;
    country?: string;
  }): Promise<PluggyConnector[]> {
    const response = await apiClient.get<PluggyConnector[]>(
      '/api/banking/connectors/',
      params
    );
    return response;
  }
  

  // ===== Items (Connections) =====
  
  async getItems(): Promise<PaginatedResponse<PluggyItem>> {
    return apiClient.get<PaginatedResponse<PluggyItem>>('/api/banking/items/');
  }
  

  async syncItem(id: string): Promise<{
    success: boolean;
    message: string;
    task_id?: string;
  }> {
    return apiClient.post(`/api/banking/items/${id}/sync/`);
  }
  
  async disconnectItem(id: string): Promise<DisconnectItemResponse> {
    return apiClient.delete<DisconnectItemResponse>(`/api/banking/items/${id}/disconnect/`);
  }
  

  // ===== Accounts =====
  
  async getAccounts(): Promise<BankAccount[]> {
    const response = await apiClient.get<BankAccount[]>('/api/banking/accounts/');
    return response;
  }
  

  // ===== Transactions =====
  
  async getTransactions(
    params?: TransactionFilters & { page?: number; page_size?: number }
  ): Promise<PaginatedResponse<Transaction>> {
    return apiClient.get<PaginatedResponse<Transaction>>(
      '/api/banking/transactions/',
      params
    );
  }
  
  async createTransaction(data: {
    account: string;
    type: 'DEBIT' | 'CREDIT';
    amount: number;
    description: string;
    date: string;
    category?: string;
    notes?: string;
    tags?: string[];
  }): Promise<Transaction> {
    return apiClient.post<Transaction>('/api/banking/transactions/', data);
  }

  async updateTransaction(
    id: string,
    data: { category?: string; notes?: string; tags?: string[] }
  ): Promise<Transaction> {
    return apiClient.patch<Transaction>(`/api/banking/transactions/${id}/`, data);
  }
  
  async bulkCategorize(
    data: BulkCategorizeRequest
  ): Promise<BulkCategorizeResponse> {
    return apiClient.post<BulkCategorizeResponse>(
      '/api/banking/transactions/bulk_categorize/',
      data
    );
  }
  
  async exportTransactions(filters?: TransactionFilters): Promise<Blob> {
    const response = await apiClient.get(
      '/api/banking/transactions/export/',
      {
        ...filters,
        responseType: 'blob',
      }
    );
    return response as unknown as Blob;
  }
  
  // ===== Categories =====
  
  async getCategories(): Promise<TransactionCategory[]> {
    const response = await apiClient.get<TransactionCategory[]>(
      '/api/banking/categories/'
    );
    return response;
  }
  

  async createCategory(
    data: Partial<TransactionCategory>
  ): Promise<TransactionCategory> {
    return apiClient.post<TransactionCategory>('/api/banking/categories/', data);
  }
  
  async updateCategory(
    id: string,
    data: Partial<TransactionCategory>
  ): Promise<TransactionCategory> {
    return apiClient.patch<TransactionCategory>(
      `/api/banking/categories/${id}/`,
      data
    );
  }
  
  async deleteCategory(id: string): Promise<void> {
    return apiClient.delete(`/api/banking/categories/${id}/`);
  }
  
  // ===== Pluggy Connect =====
  
  async createConnectToken(
    data?: ConnectTokenRequest
  ): Promise<ConnectTokenResponse> {
    try {
      const response = await apiClient.post<ConnectTokenResponse>(
        '/api/banking/pluggy/connect-token/',
        data || {}
      );
      return response;
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to create connect token',
      };
    }
  }
  
  async handleCallback(data: CallbackRequest): Promise<CallbackResponse> {
    try {
      const response = await apiClient.post<CallbackResponse>(
        '/api/banking/pluggy/callback/',
        data
      );
      return response;
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to process callback',
      };
    }
  }
  
  // ===== Account Sync =====
  
  async syncAccount(
    accountId: string,
    data?: SyncRequest
  ): Promise<SyncResponse> {
    try {
      const response = await apiClient.post<SyncResponse>(
        `/api/banking/accounts/${accountId}/sync/`,
        data || {}
      );
      return response;
    } catch (error: any) {
      // Handle specific error cases
      if (error.response?.data) {
        return error.response.data;
      }
      
      return {
        success: false,
        message: error.message || 'Failed to sync account',
      };
    }
  }
  

  // ===== Utility Methods =====
  
  /**
   * Get a connect token for updating an existing item
   */
  async getUpdateToken(itemId: string): Promise<ConnectTokenResponse> {
    return this.createConnectToken({ item_id: itemId });
  }
  
  /**
   * Check if an account needs reconnection
   */
  needsReconnection(account: BankAccount): boolean {
    const errorStatuses: PluggyItemStatus[] = [
      'LOGIN_ERROR',
      'ERROR',
      'OUTDATED',
      'WAITING_USER_INPUT',
    ];
    
    return account.item_status ? errorStatuses.includes(account.item_status) : false;
  }


  /**
   * Format currency value (delegates to shared utility)
   */
  formatCurrency(value: number, currency: string = 'BRL'): string {
    return formatCurrency(value, currency);
  }
}

export const bankingService = new BankingService();