/**
 * Banking types following Pluggy API structure
 */

// ===== Pluggy API Types =====

export interface PluggyConnector {
  pluggy_id: number;
  name: string;
  institution_url?: string;
  image_url?: string;
  primary_color: string;
  type: 'PERSONAL_BANK' | 'BUSINESS_BANK' | 'INVESTMENT' | 'OTHER';
  country: string;
  has_mfa: boolean;
  has_oauth: boolean;
  is_open_finance: boolean;
  is_sandbox: boolean;
  products: string[];
  credentials: PluggyCredential[];
}

export interface DisconnectItemResponse {
  success: boolean;
  message: string;
  deleted_transactions?: number;
}

export interface PluggyCredential {
  name: string;
  type: string;
  required: boolean;
  validation?: string;
}

export interface PluggyItem {
  id: string;
  pluggy_item_id: string;
  company: string;
  connector: PluggyConnector;
  client_user_id?: string;
  webhook_url?: string;
  next_auto_sync_at?: string;
  products: string[];
  parameter?: Record<string, any>;
  status: PluggyItemStatus;
  execution_status?: PluggyExecutionStatus;
  pluggy_created_at: string;
  pluggy_updated_at: string;
  last_successful_update?: string;
  error_code?: string;
  error_message?: string;
  status_detail?: Record<string, any>;
  consent_id?: string;
  consent_expires_at?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
  
  // Computed properties
  accounts_count?: number;
}

export type PluggyItemStatus = 
  | 'LOGIN_IN_PROGRESS'
  | 'WAITING_USER_INPUT'
  | 'UPDATING'
  | 'UPDATED'
  | 'LOGIN_ERROR'
  | 'OUTDATED'
  | 'ERROR'
  | 'DELETED'
  | 'CONSENT_REVOKED';

export type PluggyExecutionStatus =
  | 'CREATED'
  | 'SUCCESS'
  | 'PARTIAL_SUCCESS'
  | 'LOGIN_ERROR'
  | 'INVALID_CREDENTIALS'
  | 'USER_INPUT_TIMEOUT'
  | 'USER_AUTHORIZATION_PENDING'
  | 'USER_AUTHORIZATION_NOT_GRANTED'
  | 'SITE_NOT_AVAILABLE'
  | 'ERROR';

// ===== Bank Account Types =====

export interface BankAccount {
  id: string;
  pluggy_account_id: string;
  item: PluggyItem;
  company: string;
  type: BankAccountType;
  subtype?: BankAccountSubtype;
  number?: string;
  name?: string;
  marketing_name?: string;
  owner?: string;
  tax_number?: string;
  balance: number;
  balance_in_account_currency?: number;
  balance_date?: string;
  currency_code: string;
  bank_data?: BankData;
  credit_data?: CreditData;
  is_active: boolean;
  pluggy_created_at: string;
  pluggy_updated_at: string;
  created_at: string;
  updated_at: string;
  
  // Computed fields
  connector?: {
    id: number;
    name: string;
    image_url?: string;
    primary_color?: string;
    is_open_finance: boolean;
  };
  item_status?: PluggyItemStatus;
  display_name?: string;
  masked_number?: string;
}

export type BankAccountType = 'BANK' | 'CREDIT' | 'INVESTMENT' | 'LOAN' | 'OTHER';

export type BankAccountSubtype = 
  | 'CHECKING_ACCOUNT'
  | 'SAVINGS_ACCOUNT'
  | 'CREDIT_CARD'
  | 'PREPAID_CARD'
  | 'INVESTMENT_ACCOUNT'
  | 'LOAN_ACCOUNT'
  | 'OTHER';

export interface BankData {
  transferNumber?: string;
  closingBalance?: number;
  automaticallyInvestedBalance?: number;
  overdraftLimit?: number;
  overdraftUsedLimit?: number;
}

export interface CreditData {
  level?: string;
  brand?: string;
  balanceCloseDate?: string;
  balanceDueDate?: string;
  availableCreditLimit?: number;
  creditLimit?: number;
  minimumPayment?: number;
  statementTotalAmount?: number;
}

// ===== Transaction Types =====

export interface Transaction {
  id: string;
  pluggy_transaction_id: string;
  account: BankAccount;
  company: string;
  type: 'DEBIT' | 'CREDIT';
  status: 'PENDING' | 'POSTED';
  description: string;
  description_raw?: string;
  amount: number;
  amount_in_account_currency?: number;
  balance?: number;
  currency_code: string;
  date: string;
  
  // Provider information
  provider_code?: string;
  provider_id?: string;
  
  // Merchant info
  merchant?: {
    name?: string;
    businessName?: string;
    cnpj?: string;
  };
  
  // Payment data (Open Finance)
  payment_data?: {
    payer?: PaymentParty;
    receiver?: PaymentParty;
    reason?: string;
  };
  
  // Categories
  pluggy_category_id?: string;
  pluggy_category_description?: string;
  category?: string;  // Internal category ID
  category_detail?: TransactionCategory;
  
  // Additional fields
  operation_type?: string;
  payment_method?: string;
  credit_card_metadata?: {
    installmentNumber?: number;
    totalInstallments?: number;
    totalAmount?: number;
    billId?: string;
  };
  
  // User fields
  notes?: string;
  tags: string[];
  
  // Metadata
  metadata?: Record<string, any>;
  pluggy_created_at: string;
  pluggy_updated_at: string;
  created_at: string;
  updated_at: string;
  
  // Computed fields
  account_info?: {
    id: string;
    name: string;
    type: BankAccountType;
  };
  amount_display?: string;
  is_income?: boolean;
  is_expense?: boolean;
}

export interface PaymentParty {
  name?: string;
  taxNumber?: string;
  accountNumber?: string;
  agencyNumber?: string;
  bankNumber?: string;
  ispb?: string;
}

export interface TransactionCategory {
  id: string;
  name: string;
  slug: string;
  type: 'income' | 'expense' | 'both';
  parent?: string;
  icon?: string;
  color?: string;
  is_system: boolean;
  is_active: boolean;
  order: number;
  full_name?: string;
}

// ===== Filter and Request Types =====

export interface TransactionFilters {
  account_id?: string;
  category_id?: string;
  start_date?: string;
  end_date?: string;
  min_amount?: number;
  max_amount?: number;
  type?: 'DEBIT' | 'CREDIT';
  status?: 'PENDING' | 'POSTED';
  search?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
  totals?: {
    income: number;
    expenses: number;
    balance: number;
    filtered_count: number;
  };
}

export interface ConnectTokenRequest {
  item_id?: string;
  client_user_id?: string;
  webhook_url?: string;
}

export interface ConnectTokenResponse {
  success: boolean;
  data?: {
    connect_token: string;
    connect_url: string;
  };
  error?: string;
}

export interface CallbackRequest {
  item_id: string;
  status?: string;
  error?: string;
}

export interface CallbackResponse {
  success: boolean;
  data?: {
    item: PluggyItem;
    accounts: BankAccount[];
    sync_scheduled?: boolean;
    message: string;
  };
  error?: string;
  warning?: string;
}

export interface SyncRequest {
  force?: boolean;
  from_date?: string;
  to_date?: string;
}

export interface SyncResponse {
  success: boolean;
  message?: string;
  error_code?: string;
  reconnection_required?: boolean;
  data?: {
    item?: PluggyItem;
    accounts?: BankAccount[];
    sync_stats?: {
      transactions_synced?: number;
      accounts_synced?: number;
      sync_from?: string;
      sync_to?: string;
      days_searched?: number;
    };
  };
}

export interface BulkCategorizeRequest {
  transaction_ids: string[];
  category_id: string;
}

export interface BulkCategorizeResponse {
  success: boolean;
  updated: number;
}

// ===== Dashboard Types =====

export interface DashboardData {
  total_balance: number;
  total_accounts: number;
  active_accounts: number;
  
  current_month: MonthlyStats;
  previous_month: MonthlyStats;
  
  recent_transactions: Transaction[];
  category_breakdown: CategoryBreakdown[];
  accounts_summary: AccountSummary[];
}

export interface MonthlyStats {
  income: number;
  expenses: number;
  net: number;
}

export interface CategoryBreakdown {
  category__name: string;
  category__icon?: string;
  category__color?: string;
  total: number;
  count: number;
}

export interface AccountSummary {
  id: string;
  name: string;
  type: BankAccountType;
  balance: number;
  connector: {
    name: string;
    image_url?: string;
  };
  transactions_count: number;
  last_update?: string;
}

// ===== UI State Types =====

export interface PluggyConnectState {
  isOpen: boolean;
  token: string | null;
  mode: 'connect' | 'update';
  itemId?: string;
  accountId?: string;
}

export interface SyncError {
  accountId: string;
  accountName: string;
  errorCode?: string;
  message: string;
  requiresReconnect: boolean;
}

export interface DisconnectItemResponse {
  success: boolean;
  message: string;
  deleted_transactions?: number;
}

// ===== Store State Types =====

export interface BankingStoreState {
  // Data
  connectors: PluggyConnector[];
  items: PluggyItem[];
  accounts: BankAccount[];
  transactions: Transaction[];
  categories: TransactionCategory[];
  
  // UI State
  selectedAccountId: string | null;
  transactionFilters: TransactionFilters;
  connectState: PluggyConnectState;
  
  // Loading states
  loadingConnectors: boolean;
  loadingItems: boolean;
  loadingAccounts: boolean;
  loadingTransactions: boolean;
  syncingAccounts: string[]; // Array of account IDs being synced
  
  // Errors
  connectorsError: string | null;
  itemsError: string | null;
  accountsError: string | null;
  transactionsError: string | null;
  syncErrors: SyncError[];
  
  // Pagination
  transactionsPagination: {
    page: number;
    pageSize: number;
    totalCount: number;
    totalPages: number;
  };
}

// Pluggy Category
export interface PluggyCategory {
  id: string;
  description: string;
  parent_id?: string;
  parent_description?: string;
  internal_category?: string;
}



export interface PluggyConnectOptions {
  connectToken: string;
  includeSandbox?: boolean;
  connectorTypes?: string[];
  connectorIds?: number[];
  products?: string[];
  clientUserId?: string;
  webhookUrl?: string;
  language?: 'en' | 'es' | 'pt';
  updateMode?: 'add' | 'replace';
  skipSelectConnector?: boolean;
  skipSuccessScreen?: boolean;
  onSuccess: (itemData: PluggyConnectSuccessData) => void;
  onError: (error: PluggyConnectError) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onEvent?: (eventName: string, metadata: any) => void;
}

export interface PluggyConnectSuccessData {
  item: {
    id: string;
    connector: {
      id: number;
      name: string;
    };
  };
}

export interface PluggyConnectError {
  type: string;
  code?: string;
  message: string;
}

