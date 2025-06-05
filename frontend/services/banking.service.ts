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
  // Bank Providers
  async getProviders(): Promise<BankProvider[]> {
    return apiClient.get<BankProvider[]>("/api/banking/providers/");
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
    return apiClient.post(`/api/banking/accounts/${id}/sync/`);
  }

  async syncBankAccount(id: string): Promise<{ message: string }> {
    return apiClient.post(`/api/banking/accounts/${id}/sync/`);
  }

  // Transactions
  async getTransactions(
    params?: TransactionFilter & { page?: number; page_size?: number }
  ): Promise<PaginatedResponse<BankTransaction>> {
    return apiClient.get<PaginatedResponse<BankTransaction>>("/api/banking/transactions/", params);
  }

  async getTransaction(id: string): Promise<BankTransaction> {
    return apiClient.get<BankTransaction>(`/api/banking/transactions/${id}/`);
  }

  async updateTransaction(
    id: string,
    data: { category_id?: string; notes?: string }
  ): Promise<BankTransaction> {
    return apiClient.patch<BankTransaction>(`/api/banking/transactions/${id}/`, data);
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

  // Open Banking Connection
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

  async connectBankAccount(data: {
    bank_code: string;
    authorization_code?: string;
    consent_id?: string;
    use_pluggy?: boolean;
  }): Promise<{
    status: string;
    consent_id?: string;
    authorization_url?: string;
    message: string;
    account_id?: string;
    account_name?: string;
    balance?: number;
    connection_type?: string;
    data?: any;
  }> {
    const response = await apiClient.post("/api/banking/connect/", data);
    
    // Handle both response formats (direct response or wrapped in data)
    if ((response as any).success !== undefined && (response as any).data) {
      // Pluggy response format
      return {
        ...(response as any).data,
        data: (response as any).data
      };
    }
    
    return response as any;
  }
}

export const bankingService = new BankingService();