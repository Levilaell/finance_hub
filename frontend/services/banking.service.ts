import apiClient from "@/lib/api-client";
import {
  BankAccount,
  BankTransaction,
  BankProvider,
  PaginatedResponse,
  TransactionFilter,
  BankAccountForm,
} from "@/types";

class BankingService {
  // Bank Providers - USAR PLUGGY
  async getProviders(): Promise<BankProvider[]> {
    // ✅ CORRIGIDO: Usar endpoint Pluggy para providers
    const response = await apiClient.get<{
      success: boolean;
      data: BankProvider[];
    }>("/api/banking/pluggy/banks/");
    
    return response.data || [];
  }

  async createTransaction(data: {
    bank_account: string;
    amount: number;
    description: string;
    transaction_type: 'credit' | 'debit';
    category?: string;
    transaction_date: string;
    notes?: string;
    tags?: string[];
  }): Promise<BankTransaction> {
    return apiClient.post<BankTransaction>("/api/banking/transactions/", data);
  }

  async getBankProviders(): Promise<PaginatedResponse<BankProvider>> {
    return apiClient.get<PaginatedResponse<BankProvider>>("/api/banking/providers/");
  }

  // Bank Accounts
  async getAccounts(): Promise<BankAccount[]> {
    return apiClient.get<BankAccount[]>("/api/banking/accounts/");
  }

  async getBankAccounts(): Promise<PaginatedResponse<BankAccount>> {
    return apiClient.get<PaginatedResponse<BankAccount>>("/api/banking/accounts/");
  }

  async getAccount(id: string): Promise<BankAccount> {
    return apiClient.get<BankAccount>(`/api/banking/accounts/${id}/`);
  }

  async createAccount(data: BankAccountForm): Promise<BankAccount> {
    return apiClient.post<BankAccount>("/api/banking/accounts/", data);
  }

  async createBankAccount(data: BankAccountForm): Promise<BankAccount> {
    return apiClient.post<BankAccount>("/api/banking/accounts/", data);
  }

  async updateAccount(id: string, data: Partial<BankAccountForm>): Promise<BankAccount> {
    return apiClient.patch<BankAccount>(`/api/banking/accounts/${id}/`, data);
  }

  async deleteAccount(id: string): Promise<void> {
    return apiClient.delete(`/api/banking/accounts/${id}/`);
  }

  async deleteBankAccount(id: string): Promise<void> {
    return apiClient.delete(`/api/banking/accounts/${id}/`);
  }

  async syncAccount(id: string): Promise<{ message: string }> {
    // ✅ CORRIGIDO: Usar endpoint Pluggy para sync
    return apiClient.post(`/api/banking/pluggy/accounts/${id}/sync/`);
  }

  async syncBankAccount(id: string): Promise<{ message: string }> {
    return apiClient.post(`/api/banking/accounts/${id}/sync/`);
  }

  // Transactions
  async getTransactions(
    params?: TransactionFilter & { page?: number; page_size?: number }
  ): Promise<PaginatedResponse<BankTransaction>> {
    console.log('🔄 BankingService.getTransactions - Parâmetros recebidos:', params);
    return apiClient.get<PaginatedResponse<BankTransaction>>("/api/banking/transactions/", params);
  }

  async getTransaction(id: string): Promise<BankTransaction> {
    return apiClient.get<BankTransaction>(`/api/banking/transactions/${id}/`);
  }

  async updateTransaction(
    id: string,
    data: { category?: string; notes?: string }
  ): Promise<BankTransaction> {
    // Mapear category para category_id se necessário
    const payload: any = {};
    
    if (data.category !== undefined) {
      payload.category = data.category || null; // null para remover categoria
    }
    
    if (data.notes !== undefined) {
      payload.notes = data.notes;
    }
    
    return apiClient.patch<BankTransaction>(`/api/banking/transactions/${id}/`, payload);
  }

  async bulkCategorize(data: {
    transaction_ids: string[];
    category_id: string;
  }): Promise<{ updated: number }> {
    return apiClient.post("/api/banking/transactions/bulk-categorize/", data);
  }

  async importTransactions(accountId: string, file: File): Promise<{
    imported: number;
    skipped: number;
    errors: string[];
  }> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("account_id", accountId);
    return apiClient.upload("/api/banking/transactions/import/", formData);
  }

  async exportTransactions(params: TransactionFilter): Promise<Blob> {
    const response = await apiClient.get("/api/banking/transactions/export/", {
      ...params,
      responseType: "blob",
    });
    return response as unknown as Blob;
  }

  // ===== PLUGGY INTEGRATION (CORRIGIDO) =====

  /**
   * Get available banks from Pluggy
   */
  async getPluggyBanks(): Promise<{
    success: boolean;
    data: BankProvider[];
    total: number;
    sandbox_mode: boolean;
  }> {
    return apiClient.get("/api/banking/pluggy/banks/");
  }

  /**
   * Create Pluggy Connect Token for widget
   */
  async createPluggyConnectToken(itemId?: string): Promise<{
    success: boolean;
    data: {
      connect_token: string;
      connect_url: string;
      sandbox_mode: boolean;
      expires_at?: string;
      message?: string;
      sandbox_credentials?: {
        user: string;
        password: string;
        token: string;
      };
    };
  }> {
    return apiClient.post("/api/banking/pluggy/connect-token/", {
      item_id: itemId
    });
  }

  /**
   * Handle Pluggy callback after successful connection
   */
  async handlePluggyCallback(itemId: string): Promise<{
    success: boolean;
    data?: {
      accounts: Array<{
        id: number;
        name: string;
        balance: number;
        account_type: string;
        created: boolean;
      }>;
      message: string;
      sandbox_mode?: boolean;
      item_id: string;
    };
    message?: string;
  }> {
    return apiClient.post("/api/banking/pluggy/callback/", {
      item_id: itemId
    });
  }

  /**
   * Sync Pluggy account transactions
   */
  async syncPluggyAccount(accountId: string): Promise<{
    success: boolean;
    data: {
      message: string;
      transactions_synced: number;
      status: string;
      sandbox_mode: boolean;
    };
  }> {
    return apiClient.post(`/api/banking/pluggy/accounts/${accountId}/sync/`);
  }

  /**
   * Disconnect Pluggy account
   */
  async disconnectPluggyAccount(accountId: string): Promise<{
    success: boolean;
    message: string;
  }> {
    return apiClient.delete(`/api/banking/pluggy/accounts/${accountId}/disconnect/`);
  }

  /**
   * Get Pluggy account status
   */
  async getPluggyAccountStatus(accountId: string): Promise<{
    success: boolean;
    data: {
      account_id: number;
      external_id: string;
      status: string;
      last_sync: string | null;
      balance: number;
      pluggy_status: string;
      last_update: string;
      sandbox_mode: boolean;
    };
  }> {
    return apiClient.get(`/api/banking/pluggy/accounts/${accountId}/status/`);
  }

  // ===== NOVA FUNÇÃO PARA CONECTAR BANCO VIA PLUGGY =====
  
  /**
   * Connect bank account using Pluggy (replaces old connectBankAccount)
   */
  async connectBankAccount(data: {
    bank_code: string;
    use_pluggy?: boolean;
  }): Promise<{
    success: boolean;
    data?: {
      connect_token: string;
      connect_url: string;
      sandbox_mode: boolean;
      expires_at?: string;
      message?: string;
      sandbox_credentials?: {
        user: string;
        password: string;
        token: string;
      };
    };
    message?: string;
  }> {
    console.log('🔗 Connecting bank account via Pluggy with data:', data);
    
    // ✅ SEMPRE usar Pluggy para conexão bancária
    const response = await this.createPluggyConnectToken();
    
    console.log('🔗 Pluggy connect token response:', response);
    
    return response;
  }

  // ===== LEGACY OPEN BANKING (MANTER PARA COMPATIBILIDADE) =====

  async initiateOpenBankingConnection(bankCode: string): Promise<{
    status: string;
    consent_id?: string;
    authorization_url?: string;
    message: string;
  }> {
    return apiClient.post("/api/banking/connect/", { bank_code: bankCode });
  }

  async completeOpenBankingConnection(
    bankCode: string,
    authorizationCode: string,
    consentId?: string
  ): Promise<{
    status: string;
    message: string;
    account_id: string;
    account_name: string;
    balance: number;
    connection_type: string;
  }> {
    return apiClient.post("/api/banking/connect/", {
      bank_code: bankCode,
      authorization_code: authorizationCode,
      consent_id: consentId,
    });
  }

  async handleOAuthCallback(
    authorizationCode: string,
    bankCode: string,
    state?: string
  ): Promise<{
    status: string;
    message: string;
    account_id: string;
    account_name: string;
    balance: number;
  }> {
    return apiClient.post("/api/banking/oauth/callback/", {
      code: authorizationCode,
      bank_code: bankCode,
      state: state,
    });
  }

  async refreshAccountToken(accountId: string): Promise<{
    status: string;
    message: string;
    expires_in: number;
  }> {
    return apiClient.post(`/api/banking/refresh-token/${accountId}/`);
  }
}

export const bankingService = new BankingService();