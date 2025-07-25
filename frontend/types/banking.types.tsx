export interface PluggyCallbackResponse {
  success: boolean;
  message?: string;
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
}

export interface SyncResult {
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

export interface PluggyConnectState {
  isOpen: boolean;
  token: string | null;
  mode: 'connect' | 'reconnect';
  accountId?: string;
  itemId?: string;
}

export interface SyncError {
  accountId: string;
  accountName: string;
  errorCode?: string;
  message?: string;
  requiresReconnect?: boolean;
}

// types/banking.types.ts

export interface BankAccount {
  id: string;
  account_name: string;
  account_number: string;
  account_type: 'checking' | 'savings' | 'credit_card' | 'investment' | 'other';
  current_balance: number;
  available_balance: number;
  status: 'active' | 'inactive' | 'error' | 'sync_error' | 'expired' | 'consent_revoked';
  last_sync_at: string | null;
  created_at: string;
  updated_at: string;

  // ✅ Altere para "provider" aqui:
  provider?: {
    id: string;
    name: string;
    logo_url?: string;
    code: string;
  };

  pluggy_item_id?: string;
  pluggy_account_id?: string;
  metadata?: Record<string, any>;
}

export interface BankTransaction {
  id: string;
  description: string;
  amount: number;
  transaction_type: 'credit' | 'debit';
  transaction_date: string;
  posted_date?: string;
  
  // Relações
  bank_account: string; // ID da conta
  category?: {
    id: string;
    name: string;
    color?: string;
    icon?: string;
  };
  category_detail?: {
    id: string;
    name: string;
    color?: string;
    icon?: string;
  };
  
  // Campos adicionais
  merchant_name?: string;
  notes?: string;
  tags?: string[];
  
  // IA
  ai_categorized?: boolean;
  ai_confidence?: number;
  
  // Metadados
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface TransactionFilter {
  account_id?: string;
  category_id?: string;
  start_date?: string;
  end_date?: string;
  min_amount?: number;
  max_amount?: number;
  transaction_type?: 'credit' | 'debit';
  search?: string;
}

export interface Category {
  id: string;
  name: string;
  color?: string;
  icon?: string;
  type: 'income' | 'expense' | 'both';
  description?: string;
  parent_category?: string;
  created_at: string;
  updated_at: string;
}

export interface BankProvider {
  id: string;
  name: string;
  code: string;
  logo_url?: string;
  color?: string;
  is_open_banking: boolean;
  supports_pix: boolean;
  supports_ted: boolean;
  connector_id?: number; // ID do conector no Pluggy
}