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
  
  async syncConnectors(): Promise<{
    success: boolean;
    message: string;
    created: number;
    updated: number;
  }> {
    return apiClient.post('/api/banking/connectors/sync/');
  }
  
  // ===== Items (Connections) =====
  
  async getItems(): Promise<PaginatedResponse<PluggyItem>> {
    return apiClient.get<PaginatedResponse<PluggyItem>>('/api/banking/items/');
  }
  
  async getWaitingItems(): Promise<{ success: boolean; data: PluggyItem[] }> {
    try {
      const response = await apiClient.get<PaginatedResponse<PluggyItem>>('/api/banking/items/', {
        status: 'WAITING_USER_INPUT'
      });
      return {
        success: true,
        data: response.results || []
      };
    } catch (error) {
      return {
        success: false,
        data: []
      };
    }
  }
  
  async getItem(id: string): Promise<PluggyItem> {
    return apiClient.get<PluggyItem>(`/api/banking/items/${id}/`);
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
  
  async getMFAStatus(id: string): Promise<{
    data: {
      requires_mfa: boolean;
      status: string;
      parameter?: {
        name: string;
        type: string;
        label: string;
        placeholder: string;
        validation?: any;
        assistiveText?: string;
        optional?: boolean;
      };
      connector?: {
        id: string;
        name: string;
        image_url: string;
      };
      message?: string;
    };
  }> {
    const response = await apiClient.get<{
      requires_mfa: boolean;
      status: string;
      parameter?: {
        name: string;
        type: string;
        label: string;
        placeholder: string;
        validation?: any;
        assistiveText?: string;
        optional?: boolean;
      };
      connector?: {
        id: string;
        name: string;
        image_url: string;
      };
      message?: string;
    }>(`/api/banking/items/${id}/mfa_status/`);
    return { data: response };
  }
  
  async sendMFA(id: string, data: { 
    value?: string;
    token?: string;
    code?: string;
    [key: string]: any;
  }): Promise<{
    data: {
      success: boolean;
      message: string;
      item_status: string;
      execution_status?: string;
      requires_additional_mfa?: boolean;
    };
  }> {
    const response = await apiClient.post<{
      success: boolean;
      message: string;
      item_status: string;
      execution_status?: string;
      requires_additional_mfa?: boolean;
    }>(`/api/banking/items/${id}/send_mfa/`, data);
    return { data: response };
  }
  
  // ===== Accounts =====
  
  async getAccounts(): Promise<BankAccount[]> {
    const response = await apiClient.get<BankAccount[]>('/api/banking/accounts/');
    return response;
  }
  
  async getAccount(id: string): Promise<BankAccount> {
    return apiClient.get<BankAccount>(`/api/banking/accounts/${id}/`);
  }
  
  async getAccountsSummary(): Promise<{
    total_balance: number;
    total_accounts: number;
    by_type: Array<{
      type: string;
      count: number;
      total_balance: number;
    }>;
    last_update?: string;
  }> {
    return apiClient.get('/api/banking/accounts/summary/');
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
  
  async getTransaction(id: string): Promise<Transaction> {
    return apiClient.get<Transaction>(`/api/banking/transactions/${id}/`);
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
  
  async getCategory(id: string): Promise<TransactionCategory> {
    return apiClient.get<TransactionCategory>(`/api/banking/categories/${id}/`);
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
  
  // ===== Dashboard =====
  
  async getDashboard(): Promise<DashboardData> {
    return apiClient.get<DashboardData>('/api/banking/dashboard/');
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

  async sendItemMFA(
    itemId: string,
    mfaData: Record<string, string>
  ): Promise<{
    success: boolean;
    message?: string;
    item_status?: PluggyItemStatus;
    error?: string;
  }> {
    try {
      return await apiClient.post(`/api/banking/items/${itemId}/send_mfa/`, mfaData);
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to send MFA',
      };
    }
  }
  
  /**
   * Format currency value (delegates to shared utility)
   */
  formatCurrency(value: number, currency: string = 'BRL'): string {
    return formatCurrency(value, currency);
  }
  
  /**
   * Format date for display
   */
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) {
      return 'Hoje';
    } else if (diffInDays === 1) {
      return 'Ontem';
    } else if (diffInDays < 7) {
      return `${diffInDays} dias atrás`;
    } else {
      return date.toLocaleDateString('pt-BR');
    }
  }
}

export const bankingService = new BankingService();