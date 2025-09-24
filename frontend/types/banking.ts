/**
 * Banking types for Pluggy integration
 * Ref: https://docs.pluggy.ai/docs/data-structure
 */

// Connector (Bank/Financial Institution)
export interface Connector {
  id: string;
  pluggy_id: number;
  name: string;
  institution_name: string;
  institution_url?: string;
  country: string;
  primary_color?: string;
  logo_url?: string;
  type: 'PERSONAL_BANK' | 'BUSINESS_BANK' | 'INVESTMENT' | 'CREDIT';
  credentials_schema: Record<string, any>;
  supports_mfa: boolean;
  is_sandbox: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Bank Connection Status
export type ConnectionStatus =
  | 'UPDATING'
  | 'UPDATED'
  | 'LOGIN_ERROR'
  | 'WAITING_USER_INPUT'
  | 'OUTDATED'
  | 'ERROR';

// Bank Connection (Item in Pluggy)
export interface BankConnection {
  id: string;
  connector: Connector;
  connector_id?: number;
  accounts?: BankAccount[];
  status: ConnectionStatus;
  status_detail?: Record<string, any>;
  last_updated_at?: string;
  execution_status?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Account Types
export type AccountType =
  | 'CHECKING'
  | 'SAVINGS'
  | 'CREDIT_CARD'
  | 'LOAN'
  | 'INVESTMENT';

// Bank Account
export interface BankAccount {
  id: string;
  connection_id: string;
  institution_name: string;
  type: AccountType;
  subtype?: string;
  name: string;
  number?: string;
  balance: number;
  currency_code: string;
  last_synced_at?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Transaction Types
export type TransactionType = 'CREDIT' | 'DEBIT';

// Transaction
export interface Transaction {
  id: string;
  account_name: string;
  account_type: AccountType;
  type: TransactionType;
  description: string;
  amount: number;
  currency_code: string;
  date: string;
  category?: string;
  merchant_name?: string;
  is_income: boolean;
  is_expense: boolean;
  created_at: string;
}

// Create Connection Request
export interface CreateConnectionRequest {
  connector_id: number;
  credentials: Record<string, string>;
}

// Connect Token Response
export interface ConnectTokenResponse {
  token: string;
  expires_at: string;
}

// Sync Status
export type SyncStatus =
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'SUCCESS'
  | 'FAILED';

// Sync Log
export interface SyncLog {
  id: string;
  connection_name?: string;
  sync_type: 'CONNECTORS' | 'ACCOUNTS' | 'TRANSACTIONS' | 'FULL';
  status: SyncStatus;
  started_at: string;
  completed_at?: string;
  records_synced: number;
  error_message?: string;
}

// Financial Summary
export interface FinancialSummary {
  income: number;
  expenses: number;
  balance: number;
  period_start: string;
  period_end: string;
  accounts_count: number;
  transactions_count: number;
}

// Transaction Filter
export interface TransactionFilter {
  account_id?: string;
  date_from?: string;
  date_to?: string;
  type?: TransactionType;
  category?: string;
}

// Category Summary
export interface CategorySummary {
  [key: string]: number;
}

// API Response Types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  results: T[];
  count: number;
  next?: string;
  previous?: string;
}

// Pluggy Connect Config
export interface PluggyConnectConfig {
  token: string;
  onSuccess?: (itemId: string) => void;
  onError?: (error: Error) => void;
  onExit?: () => void;
}