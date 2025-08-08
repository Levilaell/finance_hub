/**
 * Test Helper Utilities
 * 
 * This file contains utilities to help with consistent test ID implementation
 * across the application for E2E testing with Playwright.
 */

/**
 * Generates a data-testid attribute object for consistent test ID implementation
 * @param id - The test ID to apply
 * @returns Object with data-testid attribute
 * 
 * @example
 * <Input {...testId('email-input')} />
 */
export const testId = (id: string) => ({
  'data-testid': id
});

/**
 * Generates a test ID for list items with index
 * @param baseId - The base test ID
 * @param index - The item index
 * @returns Object with data-testid attribute
 * 
 * @example
 * <div {...testIdWithIndex('transaction-item', index)} />
 */
export const testIdWithIndex = (baseId: string, index: number) => ({
  'data-testid': `${baseId}-${index}`
});

/**
 * Common test ID constants for consistency across the application
 */
export const TEST_IDS = {
  // Authentication
  auth: {
    emailInput: 'email-input',
    passwordInput: 'password-input',
    password2Input: 'password2-input',
    loginSubmit: 'login-submit',
    registerSubmit: 'register-submit',
    forgotPasswordSubmit: 'reset-submit',
    firstNameInput: 'first-name-input',
    lastNameInput: 'last-name-input',
    phoneInput: 'phone-input',
    companyNameInput: 'company-name-input',
    companyCnpjInput: 'company-cnpj-input',
    companyTypeSelect: 'company-type-select',
    businessSectorInput: 'business-sector-input',
    loginLink: 'login-link',
    registerLink: 'register-link',
    forgotPasswordLink: 'forgot-password-link',
    errorMessage: 'error-message',
    successMessage: 'success-message',
    userMenu: 'user-menu',
    logoutButton: 'logout-button',
    verificationBanner: 'verification-banner',
    resendVerification: 'resend-verification',
  },
  
  // Banking
  banking: {
    connectBankButton: 'connect-bank-button',
    bankProviderCard: 'bank-provider-card',
    accountCard: 'bank-account-card',
    syncButton: 'sync-account',
    deleteAccountButton: 'delete-account',
    transactionList: 'transaction-list',
    transactionItem: 'transaction-item',
    filterCategory: 'filter-category',
    filterDateRange: 'filter-date-range',
    exportButton: 'export-button',
    noAccountsMessage: 'no-accounts-message',
    accountBalance: 'account-balance',
    accountNumber: 'account-number',
    accountStatus: 'account-status',
    accountsList: 'accounts-list',
  },
  
  // AI Insights
  aiInsights: {
    chatInput: 'chat-input',
    sendMessageButton: 'send-message-button',
    conversationList: 'conversation-list',
    conversationItem: 'conversation-item',
    creditBalance: 'credit-balance',
    purchaseCreditsButton: 'purchase-credits-button',
    insightCard: 'insight-card',
    insightCardCompact: 'insight-card-compact',
    insightCompleteButton: 'insight-complete-button',
    insightDismissButton: 'insight-dismiss-button',
    insightActionCheckbox: 'insight-action-checkbox',
    insightAction: 'insight-action',
    chatInterface: 'chat-interface',
    newConversationButton: 'new-conversation-button',
    newConversationButtonSmall: 'new-conversation-button-small',
    insightsList: 'insights-list',
    insightsStats: 'insights-stats',
    insightsTabAll: 'insights-tab-all',
    insightsTabCritical: 'insights-tab-critical',
    insightsTabHigh: 'insights-tab-high',
    insightsTabPending: 'insights-tab-pending',
    insightsTabCompleted: 'insights-tab-completed',
    messageList: 'message-list',
    quickActions: 'quick-actions',
    quickActionButton: 'quick-action-button',
    archiveButton: 'archive-button',
    exportConversationButton: 'export-conversation-button',
  },
  
  // Reports
  reports: {
    reportTypeSelect: 'report-type-select',
    dateRangePicker: 'date-range-picker',
    generateReportButton: 'generate-report-button',
    exportPdfButton: 'export-pdf-button',
    exportExcelButton: 'export-excel-button',
    exportCsvButton: 'export-csv-button',
    scheduleReportButton: 'schedule-report-button',
    reportHistoryList: 'report-history-list',
    reportHistoryItem: 'report-history-item',
    quickPeriodButton: 'quick-period-button',
    visualizationsTab: 'visualizations-tab',
    customReportsTab: 'custom-reports-tab',
    reportTypeCard: 'report-type-card',
    startDatePicker: 'start-date-picker',
    endDatePicker: 'end-date-picker',
    formatSelect: 'format-select',
    accountSelect: 'account-select',
    categorySelect: 'category-select',
    downloadReportButton: 'download-report-button',
  },
  
  // Company Management
  company: {
    subscriptionCard: 'subscription-card',
    subscriptionPlanCard: 'subscription-plan-card',
    upgradePlanButton: 'upgrade-plan-button',
    downgradePlanButton: 'downgrade-plan-button',
    cancelSubscriptionButton: 'cancel-subscription-button',
    paymentMethodForm: 'payment-method-form',
    billingHistoryTable: 'billing-history-table',
    invoiceDownloadButton: 'invoice-download-button',
    usageMeter: 'usage-meter',
    notificationSettings: 'notification-settings',
    startTrialButton: 'start-trial-button',
    subscriptionStatusBadge: 'subscription-status-badge',
    manageSubscriptionButton: 'manage-subscription-button',
    transactionsUsageMeter: 'transactions-usage-meter',
    bankAccountsUsageMeter: 'bank-accounts-usage-meter',
    aiRequestsUsageMeter: 'ai-requests-usage-meter',
    billingPeriodToggle: 'billing-period-toggle',
    selectPlanButton: 'select-plan-button',
    upgradeFromLimitButton: 'upgrade-from-limit-button',
  },
  
  // Common UI Elements
  common: {
    loadingSpinner: 'loading-spinner',
    toast: 'toast',
    toastClose: 'toast-close',
    modal: 'modal',
    modalClose: 'modal-close',
    confirmButton: 'confirm-button',
    cancelButton: 'cancel-button',
    saveButton: 'save-button',
    searchInput: 'search-input',
    pagination: 'pagination',
    pageButton: 'page-button',
  },
  
  // Navigation
  navigation: {
    dashboardLink: 'dashboard-link',
    bankingLink: 'banking-link',
    reportsLink: 'reports-link',
    aiInsightsLink: 'ai-insights-link',
    settingsLink: 'settings-link',
    helpLink: 'help-link',
  }
};

/**
 * Helper to generate test IDs for form fields with their error messages
 * @param fieldName - The name of the form field
 * @returns Object with input and error test IDs
 * 
 * @example
 * const { input, error } = formFieldTestIds('email');
 * <Input {...testId(input)} />
 * <span {...testId(error)}>{errors.email?.message}</span>
 */
export const formFieldTestIds = (fieldName: string) => ({
  input: `${fieldName}-input`,
  error: `${fieldName}-error`,
  label: `${fieldName}-label`,
});

/**
 * Helper for generating test IDs for lists and their items
 * @param listName - The name of the list
 * @returns Object with list and item test ID generators
 * 
 * @example
 * const transactionTestIds = listTestIds('transaction');
 * <div {...testId(transactionTestIds.list)}>
 *   {items.map((item, index) => (
 *     <div {...testId(transactionTestIds.item(index))}>
 *   ))}
 * </div>
 */
export const listTestIds = (listName: string) => ({
  list: `${listName}-list`,
  item: (index: number) => `${listName}-item-${index}`,
  empty: `${listName}-empty`,
  loading: `${listName}-loading`,
});