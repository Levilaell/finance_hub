/**
 * Banking Service - API integration for Pluggy banking
 * Ref: https://docs.pluggy.ai/reference
 */

import apiClient from "@/lib/api-client";
import {
  Connector,
  BankConnection,
  BankAccount,
  Transaction,
  CreateConnectionRequest,
  ConnectTokenResponse,
  SyncLog,
  FinancialSummary,
  TransactionFilter,
  CategorySummary,
  PaginatedResponse
} from "@/types/banking";

class BankingService {
  // Connectors
  async getConnectors(country: string = 'BR', type?: string): Promise<Connector[]> {
    const params: Record<string, string> = { country };
    if (type) params.type = type;

    const response = await apiClient.get<PaginatedResponse<Connector>>(
      "/api/banking/connectors/",
      params
    );
    return response.results;
  }

  async syncConnectors(): Promise<{ message: string; count: number }> {
    return apiClient.post("/api/banking/connectors/sync/");
  }

  // Bank Connections
  async getConnections(): Promise<BankConnection[]> {
    const response = await apiClient.get<PaginatedResponse<BankConnection>>(
      "/api/banking/connections/"
    );
    return response.results;
  }

  async getConnection(id: string): Promise<BankConnection> {
    return apiClient.get<BankConnection>(`/api/banking/api/connections/${id}/`);
  }

  async createConnection(data: CreateConnectionRequest): Promise<BankConnection> {
    return apiClient.post<BankConnection>("/api/banking/connections/", data);
  }

  async deleteConnection(id: string): Promise<void> {
    return apiClient.delete(`/api/banking/connections/${id}/`);
  }

  async refreshConnectionStatus(id: string): Promise<BankConnection> {
    return apiClient.post<BankConnection>(
      `/api/banking/api/connections/${id}/refresh_status/`
    );
  }

  async syncConnectionAccounts(id: string): Promise<{ message: string; count: number }> {
    return apiClient.post(
      `/api/banking/api/connections/${id}/sync_accounts/`
    );
  }

  async syncConnectionTransactions(id: string): Promise<{
    message: string;
    results: Record<string, number>;
    total: number;
  }> {
    return apiClient.post(
      `/api/banking/api/connections/${id}/sync_transactions/`
    );
  }

  async getConnectToken(): Promise<ConnectTokenResponse> {
    return apiClient.get<ConnectTokenResponse>(
      "/api/banking/connections/connect_token/"
    );
  }

  // Bank Accounts
  async getAccounts(): Promise<BankAccount[]> {
    const response = await apiClient.get<PaginatedResponse<BankAccount>>(
      "/api/banking/accounts/"
    );
    return response.results;
  }

  async getAccount(id: string): Promise<BankAccount> {
    return apiClient.get<BankAccount>(`/api/banking/api/accounts/${id}/`);
  }

  async syncAccountTransactions(
    id: string,
    daysBack: number = 365
  ): Promise<{ message: string; count: number }> {
    return apiClient.post(
      `/api/banking/accounts/${id}/sync_transactions/`,
      { days_back: daysBack }
    );
  }

  // Transactions
  async getTransactions(filters?: TransactionFilter): Promise<Transaction[]> {
    const response = await apiClient.get<PaginatedResponse<Transaction>>(
      "/api/banking/transactions/",
      filters
    );
    return response.results;
  }

  async getTransaction(id: string): Promise<Transaction> {
    return apiClient.get<Transaction>(`/api/banking/api/transactions/${id}/`);
  }

  async getTransactionsSummary(
    dateFrom?: string,
    dateTo?: string
  ): Promise<FinancialSummary> {
    const params: Record<string, string> = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;

    return apiClient.get<FinancialSummary>(
      "/api/banking/transactions/summary/",
      params
    );
  }

  async getTransactionsByCategory(
    dateFrom?: string,
    dateTo?: string
  ): Promise<CategorySummary> {
    const params: Record<string, string> = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;

    return apiClient.get<CategorySummary>(
      "/api/banking/transactions/by_category/",
      params
    );
  }

  // Sync Logs
  async getSyncLogs(): Promise<SyncLog[]> {
    const response = await apiClient.get<PaginatedResponse<SyncLog>>(
      "/api/banking/sync-logs/"
    );
    return response.results;
  }

  // Financial Summary
  async getFinancialSummary(): Promise<FinancialSummary> {
    return apiClient.get<FinancialSummary>("/api/banking/transactions/summary/");
  }

  // Category Summary (calculated from transactions)
  async getCategorySummary(): Promise<CategorySummary> {
    try {
      // Get current month's transactions
      const now = new Date();
      const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
      const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0);

      const transactions = await this.getTransactions({
        date_from: startOfMonth.toISOString().split('T')[0],
        date_to: endOfMonth.toISOString().split('T')[0]
      });

      // Calculate category totals
      const categoryTotals: CategorySummary = {};
      transactions.forEach(transaction => {
        const category = transaction.category || 'Sem categoria';
        if (transaction.type === 'DEBIT') {
          categoryTotals[category] = (categoryTotals[category] || 0) + Math.abs(transaction.amount);
        }
      });

      return categoryTotals;
    } catch (error) {
      console.error('Error calculating category summary:', error);
      return {};
    }
  }

  // Utility methods for UI
  formatCurrency(amount: number, currencyCode: string = 'BRL'): string {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: currencyCode,
    }).format(amount);
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('pt-BR');
  }

  getAccountIcon(type: string): string {
    const icons: Record<string, string> = {
      CHECKING: '💳',
      SAVINGS: '🏦',
      CREDIT_CARD: '💳',
      LOAN: '📄',
      INVESTMENT: '📈',
    };
    return icons[type] || '🏦';
  }

  getStatusColor(status: string): string {
    const colors: Record<string, string> = {
      UPDATED: 'text-green-500',
      UPDATING: 'text-blue-500',
      LOGIN_ERROR: 'text-red-500',
      WAITING_USER_INPUT: 'text-orange-500',
      OUTDATED: 'text-gray-500',
      ERROR: 'text-red-500',
    };
    return colors[status] || 'text-gray-500';
  }

  getStatusBadgeClass(status: string): string {
    const classes: Record<string, string> = {
      UPDATED: 'bg-green-100 text-green-800',
      UPDATING: 'bg-blue-100 text-blue-800',
      LOGIN_ERROR: 'bg-red-100 text-red-800',
      WAITING_USER_INPUT: 'bg-orange-100 text-orange-800',
      OUTDATED: 'bg-gray-100 text-gray-800',
      ERROR: 'bg-red-100 text-red-800',
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  }
}

export const bankingService = new BankingService();