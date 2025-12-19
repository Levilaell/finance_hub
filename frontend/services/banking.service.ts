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
  PaginatedResponse,
  Category,
  CategoryRequest,
  Bill,
  BillSuggestion,
  BillSuggestionExtended,
  CategoryRule,
  CategoryRuleRequest,
  CategoryRuleStats,
  SimilarTransactionsResponse,
  TransactionCategoryUpdateRequest,
  TransactionCategoryUpdateResponse
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
    sync_status: string;
    item_status: string;
    requires_action: boolean;
  }> {
    return apiClient.post(
      `/api/banking/connections/${id}/sync_transactions/`
    );
  }

  async checkConnectionStatus(id: string): Promise<{
    status: string;
    execution_status: string;
    is_syncing: boolean;
    sync_complete: boolean;
    requires_action: boolean;
    error_message?: string;
    last_updated_at: string;
  }> {
    return apiClient.get(
      `/api/banking/connections/${id}/check_status/`
    );
  }

  async getConnectToken(): Promise<ConnectTokenResponse> {
    return apiClient.get<ConnectTokenResponse>(
      "/api/banking/connections/connect_token/"
    );
  }

  async getReconnectToken(connectionId: string): Promise<ConnectTokenResponse & { item_id: string }> {
    return apiClient.get<ConnectTokenResponse & { item_id: string }>(
      `/api/banking/connections/${connectionId}/reconnect_token/`
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
    // Performance otimização: estratégia inteligente baseada nos filtros

    // 1. Se tem limit específico, fazer apenas 1 requisição
    if (filters?.limit) {
      const response = await apiClient.get<PaginatedResponse<Transaction>>(
        "/api/banking/transactions/",
        {
          ...filters,
          page_size: filters.limit,
          page: filters.page || 1
        }
      );
      return response.results;
    }

    // 2. Se tem filtros de data, buscar todas as páginas (max_page_size do backend é 1000)
    if (filters?.date_from || filters?.date_to) {
      const allTransactions: Transaction[] = [];
      let page = 1;
      let hasMore = true;
      const pageSize = 1000; // Máximo permitido pelo backend

      while (hasMore) {
        const response = await apiClient.get<PaginatedResponse<Transaction>>(
          "/api/banking/transactions/",
          {
            ...filters,
            page_size: pageSize,
            page: page
          }
        );

        allTransactions.push(...response.results);
        hasMore = response.results.length === pageSize;
        page++;

        // Proteção contra loop infinito
        if (page > 50) {
          console.warn('⚠️ Limite de 50 páginas atingido (50.000 transações)');
          break;
        }
      }

      return allTransactions;
    }

    // 3. Sem filtros: buscar todas as transações em batches (para /transactions page)
    const allTransactions: Transaction[] = [];
    let page = 1;
    let hasMore = true;
    const pageSize = 500; // Batch de 500 por vez para melhor performance

    while (hasMore) {
      const params = {
        ...filters,
        page_size: pageSize,
        page: page
      };

      const response = await apiClient.get<PaginatedResponse<Transaction>>(
        "/api/banking/transactions/",
        params
      );

      allTransactions.push(...response.results);

      // Verifica se há mais páginas
      hasMore = response.results.length === pageSize;
      page++;

      // Proteção contra loop infinito (máximo 20 páginas = 10.000 transações)
      if (page > 20) {
        console.warn('⚠️ Limite de 20 páginas atingido (10.000 transações)');
        break;
      }
    }

    return allTransactions;
  }

  async getTransaction(id: string): Promise<Transaction> {
    return apiClient.get<Transaction>(`/api/banking/api/transactions/${id}/`);
  }

  async updateTransactionCategory(
    id: string,
    categoryId: string | null,
    subcategoryId?: string | null
  ): Promise<Transaction> {
    const data: Record<string, string | null> = { user_category_id: categoryId };
    if (subcategoryId !== undefined) {
      data.user_subcategory_id = subcategoryId;
    }
    return apiClient.patch<Transaction>(
      `/api/banking/transactions/${id}/`,
      data
    );
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

      // Calculate category totals (only expenses)
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

  // Categories
  async getCategories(type?: string): Promise<Category[]> {
    const params: Record<string, string> = {};
    if (type) params.type = type;

    // Fetch all pages of categories (similar to getTransactions)
    const allCategories: Category[] = [];
    let page = 1;
    let hasMore = true;

    while (hasMore) {
      const response = await apiClient.get<PaginatedResponse<Category>>(
        "/api/banking/categories/",
        { ...params, page }
      );

      allCategories.push(...response.results);
      hasMore = response.next !== null && response.next !== undefined;
      page++;

      // Safety limit
      if (page > 10) {
        console.warn('⚠️ Category pagination limit reached (10 pages)');
        break;
      }
    }

    return allCategories;
  }

  async getCategory(id: string): Promise<Category> {
    return apiClient.get<Category>(`/api/banking/categories/${id}/`);
  }

  async createCategory(data: CategoryRequest): Promise<Category> {
    return apiClient.post<Category>("/api/banking/categories/", data);
  }

  async updateCategory(id: string, data: Partial<CategoryRequest>): Promise<Category> {
    return apiClient.patch<Category>(`/api/banking/categories/${id}/`, data);
  }

  async deleteCategory(id: string): Promise<void> {
    return apiClient.delete(`/api/banking/categories/${id}/`);
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

  // ============================================================
  // Bill Linking Methods
  // ============================================================

  /**
   * Get suggested bills for linking to a transaction
   */
  async getSuggestedBills(transactionId: string): Promise<BillSuggestion[]> {
    return apiClient.get<BillSuggestion[]>(
      `/api/banking/transactions/${transactionId}/suggested_bills/`
    );
  }

  /**
   * Link a bill to a transaction
   */
  async linkBill(transactionId: string, billId: string): Promise<Transaction> {
    return apiClient.post<Transaction>(
      `/api/banking/transactions/${transactionId}/link_bill/`,
      { bill_id: billId }
    );
  }

  /**
   * Get ALL pending bills for manual linking (no amount filter)
   * Returns bills with match info (amount_match, amount_diff, would_overpay)
   */
  async getAllPendingBills(transactionId: string): Promise<BillSuggestionExtended[]> {
    return apiClient.get<BillSuggestionExtended[]>(
      `/api/banking/transactions/${transactionId}/all_pending_bills/`
    );
  }

  /**
   * Manually link a bill to a transaction (allows different amounts)
   * Creates a BillPayment with min(transaction.amount, bill.amount_remaining)
   */
  async linkBillManual(transactionId: string, billId: string): Promise<{
    transaction: Transaction;
    bill: Bill;
    message: string;
  }> {
    return apiClient.post(
      `/api/banking/transactions/${transactionId}/link_bill_manual/`,
      { bill_id: billId }
    );
  }

  // ============================================================
  // Category Rules Methods
  // ============================================================

  /**
   * Get all category rules for the current user
   */
  async getCategoryRules(): Promise<CategoryRule[]> {
    const response = await apiClient.get<PaginatedResponse<CategoryRule>>(
      "/api/banking/category-rules/"
    );
    return response.results;
  }

  /**
   * Create a new category rule
   * @param data Rule data including pattern, match_type, and category
   * @param applyToExisting If true, applies the rule to existing transactions
   */
  async createCategoryRule(
    data: CategoryRuleRequest,
    applyToExisting: boolean = false
  ): Promise<CategoryRule & { apply_result?: { matched_count: number; updated_count: number } }> {
    return apiClient.post<CategoryRule & { apply_result?: { matched_count: number; updated_count: number } }>(
      "/api/banking/category-rules/",
      { ...data, apply_to_existing: applyToExisting }
    );
  }

  /**
   * Update a category rule (toggle active, change category, etc)
   */
  async updateCategoryRule(id: string, data: Partial<CategoryRule>): Promise<CategoryRule> {
    return apiClient.patch<CategoryRule>(`/api/banking/category-rules/${id}/`, data);
  }

  /**
   * Delete a category rule
   */
  async deleteCategoryRule(id: string): Promise<void> {
    return apiClient.delete(`/api/banking/category-rules/${id}/`);
  }

  /**
   * Apply a category rule to existing transactions
   * @param id Rule ID
   * @returns Result with matched and updated counts
   */
  async applyCategoryRule(id: string): Promise<{
    success: boolean;
    matched_count: number;
    updated_count: number;
    message: string;
  }> {
    return apiClient.post(`/api/banking/category-rules/${id}/apply/`);
  }

  /**
   * Get category rules statistics
   */
  async getCategoryRulesStats(): Promise<CategoryRuleStats> {
    return apiClient.get<CategoryRuleStats>("/api/banking/category-rules/stats/");
  }

  // ============================================================
  // Similar Transactions Methods
  // ============================================================

  /**
   * Get similar transactions for batch categorization
   */
  async getSimilarTransactions(transactionId: string): Promise<SimilarTransactionsResponse> {
    return apiClient.get<SimilarTransactionsResponse>(
      `/api/banking/transactions/${transactionId}/similar/`
    );
  }

  /**
   * Update transaction category with optional batch operations
   * - apply_to_similar: Apply the same category to similar transactions
   * - create_rule: Create a rule for future transactions
   * - similar_transaction_ids: IDs of similar transactions to update
   */
  async updateTransactionCategoryWithRule(
    id: string,
    data: TransactionCategoryUpdateRequest
  ): Promise<TransactionCategoryUpdateResponse> {
    return apiClient.patch<TransactionCategoryUpdateResponse>(
      `/api/banking/transactions/${id}/`,
      data
    );
  }
}

export const bankingService = new BankingService();