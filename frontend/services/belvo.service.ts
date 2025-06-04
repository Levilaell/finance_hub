import { apiClient } from '@/lib/api-client';

export interface BelvoInstitution {
  id: string;
  name: string;
  type: string;
  logo: string;
  country: string;
  primary_color: string;
}

export interface BelvoWidgetToken {
  access_token: string;
  widget_url: string;
}

export interface BelvoConnection {
  connection_id: number;
  accounts: Array<{
    id: number;
    bank_name: string;
    account_type: string;
    account_number: string;
    current_balance: number;
    currency: string;
  }>;
}

class BelvoService {
  async getInstitutions(): Promise<BelvoInstitution[]> {
    const response = await apiClient.get('/api/banking/belvo/institutions/');
    return response.data;
  }

  async createWidgetToken(): Promise<BelvoWidgetToken> {
    const response = await apiClient.post('/api/banking/belvo/widget-token/');
    return response.data;
  }

  async createConnection(data: {
    institution: string;
    username: string;
    password: string;
  }): Promise<BelvoConnection> {
    const response = await apiClient.post('/api/banking/belvo/connect/', data);
    return response.data;
  }

  async syncBankData(): Promise<{ message: string; transactions_synced: number }> {
    const response = await apiClient.post('/api/banking/belvo/sync/');
    return response.data;
  }

  async disconnectBank(connectionId: number): Promise<{ message: string }> {
    const response = await apiClient.delete(`/api/banking/belvo/disconnect/${connectionId}/`);
    return response.data;
  }
}

export const belvoService = new BelvoService();