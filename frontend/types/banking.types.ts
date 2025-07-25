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