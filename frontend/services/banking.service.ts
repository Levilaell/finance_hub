import apiClient from "@/lib/api-client";
import {
  BankAccount,
  BankTransaction,
  BankProvider,
  PaginatedResponse,
  TransactionFilter,
  BankAccountForm,
} from "@/types";

import { PluggyCallbackResponse } from '@/types/banking.types';


interface PluggyConnectTokenResponse {
  success: boolean;
  data: {
    connect_token: string;
    connect_url: string;
    sandbox_mode: boolean;
    expires_at?: string;
    sandbox_credentials?: {
      user: string;
      password: string;
      token: string;
    };
  };
}

interface SyncResult {
  success: boolean;
  error_code?: string;
  message?: string;
  reconnection_required?: boolean;
  warning?: string;
  data?: {
    sync_stats?: {
      transactions_synced?: number;
      bank_requires_mfa?: boolean;
    };
    [key: string]: any;
  };
}

class BankingService {
  // ===== PROVIDERS =====
  async getProviders(): Promise<BankProvider[]> {
    const response = await apiClient.get<{
      success: boolean;
      data: BankProvider[];
    }>("/api/banking/pluggy/banks/");
    return response.data || [];
  }

  // ===== ACCOUNTS =====
  async getAccounts(): Promise<BankAccount[]> {
    return apiClient.get<BankAccount[]>("/api/banking/accounts/");
  }

  async getAccount(id: string): Promise<BankAccount> {
    return apiClient.get<BankAccount>(`/api/banking/accounts/${id}/`);
  }

  async createAccount(data: BankAccountForm): Promise<BankAccount> {
    return apiClient.post<BankAccount>("/api/banking/accounts/", data);
  }

  async updateAccount(id: string, data: Partial<BankAccountForm>): Promise<BankAccount> {
    return apiClient.patch<BankAccount>(`/api/banking/accounts/${id}/`, data);
  }

  async deleteAccount(id: string): Promise<void> {
    return apiClient.delete(`/api/banking/accounts/${id}/`);
  }

  async syncAccount(id: string): Promise<SyncResult> {
    // Em vez de Promise<{ message: string }>
    const response = await apiClient.post<{
      success: boolean;
      error_code?: string;
      message?: string;
      reconnection_required?: boolean;
      warning?: string;
      data?: {
        sync_stats?: {
          transactions_synced?: number;
          bank_requires_mfa?: boolean;
        };
        [key: string]: any;
      };
    }>(`/api/banking/pluggy/accounts/${id}/sync/`);
    
    return response;
  }

  // ===== TRANSACTIONS =====
  async getTransactions(params?: TransactionFilter & { page?: number; page_size?: number }): Promise<PaginatedResponse<BankTransaction>> {
    return apiClient.get<PaginatedResponse<BankTransaction>>("/api/banking/transactions/", params);
  }

  async getTransaction(id: string): Promise<BankTransaction> {
    return apiClient.get<BankTransaction>(`/api/banking/transactions/${id}/`);
  }

  async createTransaction(data: { /* ... */ }): Promise<BankTransaction> {
    return apiClient.post<BankTransaction>("/api/banking/transactions/", data);
  }

  async updateTransaction(id: string, data: { category?: string; notes?: string }): Promise<BankTransaction> {
    const payload: any = {};
    if (data.category !== undefined) payload.category = data.category || null;
    if (data.notes !== undefined) payload.notes = data.notes;
    return apiClient.patch<BankTransaction>(`/api/banking/transactions/${id}/`, payload);
  }

  // ===== PLUGGY INTEGRATION =====
  async getPluggyBanks(): Promise<{ /* ... */ }> {
    return apiClient.get("/api/banking/pluggy/banks/");
  }

  async createPluggyConnectToken(itemId?: string): Promise<{
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
    try {
      const response = await apiClient.post<{
        connect_token: string;
        connect_url: string;
        sandbox_mode: boolean;
        expires_at?: string;
        sandbox_credentials?: {
          user: string;
          password: string;
          token: string;
        };
      }>("/api/banking/pluggy/connect-token/", {
        item_id: itemId
      });
      
      // Wrap na estrutura esperada
      return {
        success: true,
        data: response
      };
    } catch (error: any) {
      return {
        success: false,
        message: error.message || 'Erro ao criar token'
      };
    }
  }

  async handlePluggyCallback(itemId: string): Promise<PluggyCallbackResponse> {
    return apiClient.post<PluggyCallbackResponse>("/api/banking/pluggy/callback/", {
      item_id: itemId
    });
  }

  async syncPluggyAccount(accountId: string): Promise<{ /* ... */ }> {
    return apiClient.post(`/api/banking/pluggy/accounts/${accountId}/sync/`);
  }

  async disconnectPluggyAccount(accountId: string): Promise<{ /* ... */ }> {
    return apiClient.delete(`/api/banking/pluggy/accounts/${accountId}/disconnect/`);
  }

  async getPluggyAccountStatus(accountId: string): Promise<{ /* ... */ }> {
    return apiClient.get(`/api/banking/pluggy/accounts/${accountId}/status/`);
  }

  async reconnectPluggyAccount(accountId: string): Promise<{
    success: boolean;
    data?: {
      connect_token: string;
      connect_url: string;
      item_id: string;
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
    try {
      // 1. Buscar a conta
      const account = await this.getAccount(accountId);
      
      // 2. Verificar se tem pluggy_item_id
      if (!account.pluggy_item_id) {
        return {
          success: false,
          message: 'Conta não conectada via Pluggy'
        };
      }
      
      // 3. Criar token de reconexão
      const tokenResponse = await this.createPluggyConnectToken(account.pluggy_item_id);
      
      // 4. Verificar sucesso e montar resposta
      if (tokenResponse.success && tokenResponse.data) {
        return {
          success: true,
          data: {
            connect_token: tokenResponse.data.connect_token,
            connect_url: tokenResponse.data.connect_url,
            sandbox_mode: tokenResponse.data.sandbox_mode,
            item_id: account.pluggy_item_id, // ← IMPORTANTE
            expires_at: tokenResponse.data.expires_at,
            message: tokenResponse.data.message,
            sandbox_credentials: tokenResponse.data.sandbox_credentials
          }
        };
      }
      
      // 5. Retornar erro se falhou
      return {
        success: false,
        message: tokenResponse.message || 'Erro ao criar token de reconexão'
      };
      
    } catch (error: any) {
      return {
        success: false,
        message: error.message || 'Erro ao reconectar conta'
      };
    }
  }

  // ===== UTILITIES =====
  async bulkCategorize(data: { /* ... */ }): Promise<{ updated: number }> {
    return apiClient.post("/api/banking/transactions/bulk-categorize/", data);
  }

  async importTransactions(accountId: string, file: File): Promise<{ /* ... */ }> {
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
}

export const bankingService = new BankingService();