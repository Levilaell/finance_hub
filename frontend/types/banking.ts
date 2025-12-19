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
  is_credit_card: boolean;
  available_credit_limit?: number;
  credit_limit?: number;
  credit_data?: Record<string, any>;
  last_synced_at?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Transaction Types
export type TransactionType = 'CREDIT' | 'DEBIT';

// Linked Bill Summary (embedded in Transaction)
export interface LinkedBillSummary {
  id: string;
  description: string;
  amount: string;
  due_date: string;
  type: BillType;
}

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
  // Category information
  category?: string;
  user_category_id?: string | null;
  pluggy_category?: string;
  category_color?: string | null;
  category_icon?: string | null;
  // Subcategory information
  subcategory?: string | null;
  user_subcategory_id?: string | null;
  subcategory_color?: string | null;
  subcategory_name?: string | null;
  // Other fields
  merchant_name?: string;
  is_income: boolean;
  is_expense: boolean;
  created_at: string;
  // Linked bill information
  linked_bill?: LinkedBillSummary | null;
  has_linked_bill?: boolean;
}

// Category Types
export type CategoryType = 'income' | 'expense';

// Category
export interface Category {
  id: string;
  name: string;
  type: CategoryType;
  color: string;
  icon: string;
  is_system: boolean;
  parent?: string | null;
  subcategories?: Category[];
  created_at: string;
  updated_at: string;
}

// Create/Update Category Request
export interface CategoryRequest {
  name: string;
  type: CategoryType;
  color?: string;
  icon?: string;
  parent?: string | null;
}

// Create Connection Request
export interface CreateConnectionRequest {
  pluggy_item_id?: string;
  connector_id?: number;
  credentials?: Record<string, string>;
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
  limit?: number;
  offset?: number;
  page?: number;
  page_size?: number;
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

// Bill Types
export type BillType = 'payable' | 'receivable';

export type BillStatus = 'pending' | 'partially_paid' | 'paid' | 'cancelled';

export type BillRecurrence = 'once' | 'monthly' | 'weekly' | 'yearly';

// Linked Transaction Summary (embedded in Bill)
export interface LinkedTransactionSummary {
  id: string;
  description: string;
  amount: string;
  date: string;
  account_name?: string;
}

// Bill
export interface Bill {
  id: string;
  type: BillType;
  description: string;
  amount: number;
  amount_paid: number;
  amount_remaining: number;
  payment_percentage: number;
  currency_code: string;
  due_date: string;
  paid_at?: string;
  status: BillStatus;
  is_overdue: boolean;
  category?: string;
  category_name?: string;
  category_color?: string;
  category_icon?: string;
  recurrence: BillRecurrence;
  parent_bill?: string;
  installment_number?: number;
  customer_supplier?: string;
  notes?: string;
  linked_transaction?: string;
  // Linked transaction details (legacy)
  linked_transaction_details?: LinkedTransactionSummary | null;
  has_linked_transaction?: boolean;
  // Pagamentos parciais (novo sistema)
  payments?: BillPayment[];
  payments_count?: number;
  can_add_payment?: boolean;
  created_at: string;
  updated_at: string;
}

// BillPayment - Pagamento individual de uma bill
export interface BillPayment {
  id: string;
  amount: number;
  payment_date: string;
  notes: string;
  transaction?: string;
  transaction_details?: LinkedTransactionSummary | null;
  has_transaction: boolean;
  created_at: string;
  updated_at: string;
}

// Request para criar pagamento
export interface BillPaymentCreateRequest {
  amount: number;
  transaction_id?: string;
  notes?: string;
}

// Resposta de transações sugeridas para pagamento parcial
export interface PartialPaymentSuggestionsResponse {
  remaining_amount: string;
  transactions: PartialPaymentSuggestion[];
}

// Sugestão de transação para pagamento parcial
export interface PartialPaymentSuggestion {
  id: string;
  description: string;
  amount: number;
  date: string;
  type: TransactionType;
  account_name: string;
  merchant_name?: string;
  relevance_score: number;
  would_complete_bill: boolean;
}

// Bill Request
export interface BillRequest {
  type: BillType;
  description: string;
  amount: number;
  due_date: string;
  category?: string;
  recurrence?: BillRecurrence;
  customer_supplier?: string;
  notes?: string;
}

// Register Payment Request
export interface RegisterPaymentRequest {
  amount: number;
  notes?: string;
}

// Bills Summary
export interface BillsSummary {
  total_receivable: number;
  total_receivable_month: number;
  total_payable: number;
  total_payable_month: number;
  total_overdue: number;
  overdue_count: number;
  receivable_count: number;
  payable_count: number;
}

// Bill Filter
export interface BillFilter {
  type?: BillType;
  status?: BillStatus;
  date_from?: string;
  date_to?: string;
  category?: string;
  is_overdue?: boolean;
}

// Cash Flow Projection
export interface CashFlowProjection {
  month: string;
  month_name: string;
  receivable: number;
  payable: number;
  net: number;
  // For actual cash flow (what was paid)
  receivable_paid?: number;
  payable_paid?: number;
}

// ============================================================
// Transaction-Bill Linking Types
// ============================================================

// Transaction Suggestion (for linking to bills)
export interface TransactionSuggestion {
  id: string;
  description: string;
  amount: number;
  date: string;
  type: TransactionType;
  account_name: string;
  merchant_name?: string;
  relevance_score: number;
}

// Bill Suggestion (for linking to transactions)
export interface BillSuggestion {
  id: string;
  description: string;
  amount: number;
  due_date: string;
  type: BillType;
  customer_supplier?: string;
  category_name?: string;
  category_icon?: string;
  relevance_score: number;
}

// Bill Suggestion Extended (for manual linking with amount info)
export interface BillSuggestionExtended extends BillSuggestion {
  amount_match: boolean;
  amount_diff: number;
  would_overpay: boolean;
  amount_remaining: number;
}

// Link Transaction Request
export interface LinkTransactionRequest {
  transaction_id: string;
}

// Link Bill Request
export interface LinkBillRequest {
  bill_id: string;
}

// Auto Match Result (from sync)
export interface AutoMatchResult {
  matched: Array<{
    transaction_id: string;
    transaction_description: string;
    bill_id: string;
    bill_description: string;
    amount: number;
  }>;
  ambiguous: Array<{
    transaction_id: string;
    transaction_description: string;
    amount: number;
    matching_bills_count: number;
  }>;
  matched_count: number;
  ambiguous_count: number;
}

// ============================================================
// User Settings Types
// ============================================================

export interface UserSettings {
  auto_match_transactions: boolean;
}

// ============================================================
// Category Rule Types
// ============================================================

export type CategoryRuleMatchType = 'prefix' | 'contains' | 'fuzzy';

export interface CategoryRule {
  id: string;
  pattern: string;
  match_type: CategoryRuleMatchType;
  match_type_display: string;
  category: string;
  category_name: string;
  category_color: string;
  category_icon: string;
  is_active: boolean;
  applied_count: number;
  created_at: string;
  updated_at: string;
}

export interface CategoryRuleRequest {
  pattern: string;
  match_type: CategoryRuleMatchType;
  category: string;
}

export interface CategoryRuleStats {
  total_rules: number;
  active_rules: number;
  inactive_rules: number;
  total_times_applied: number;
}

// Similar Transaction (for batch categorization)
export interface SimilarTransaction {
  id: string;
  description: string;
  merchant_name: string;
  amount: string;
  date: string;
  match_type: 'merchant' | 'prefix' | 'fuzzy';
  score: number;
}

export interface SimilarTransactionsResponse {
  count: number;
  transactions: SimilarTransaction[];
  suggested_pattern: string;
  suggested_match_type: CategoryRuleMatchType;
}

// Extended transaction update with batch operations
export interface TransactionCategoryUpdateRequest {
  user_category_id: string | null;
  user_subcategory_id?: string | null;
  apply_to_similar?: boolean;
  create_rule?: boolean;
  similar_transaction_ids?: string[];
}

export interface TransactionCategoryUpdateResponse extends Transaction {
  applied_to_similar: number;
  rule_created: boolean;
}