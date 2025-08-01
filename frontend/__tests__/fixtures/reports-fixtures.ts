/**
 * Test fixtures and mock data generators for reports frontend tests
 */
import { faker } from '@faker-js/faker';
import type { 
  Report, 
  ReportSummary,
  AnalyticsData,
  CashFlowData,
  CategorySpending,
  AIInsights,
  ScheduledReport,
  Account,
  Category,
  Transaction
} from '@/types';

// Configure faker for consistent test data
faker.seed(12345);

/**
 * Generate a mock report
 */
export const createMockReport = (overrides: Partial<Report> = {}): Report => ({
  id: faker.string.uuid(),
  title: faker.lorem.words(3),
  report_type: faker.helpers.arrayElement([
    'monthly_summary',
    'cash_flow', 
    'profit_loss',
    'category_analysis',
    'quarterly_report'
  ]),
  description: faker.lorem.sentence(),
  period_start: faker.date.past().toISOString().split('T')[0],
  period_end: faker.date.recent().toISOString().split('T')[0],
  file_format: faker.helpers.arrayElement(['pdf', 'xlsx', 'csv']),
  is_generated: faker.datatype.boolean(),
  created_at: faker.date.recent().toISOString(),
  updated_at: faker.date.recent().toISOString(),
  created_by_name: faker.person.fullName(),
  file_size: faker.datatype.boolean() ? faker.number.int({ min: 1024, max: 10485760 }) : null,
  download_url: faker.datatype.boolean() ? faker.internet.url() : null,
  error_message: faker.datatype.boolean({ probability: 0.1 }) ? faker.lorem.sentence() : null,
  parameters: {
    include_charts: faker.datatype.boolean(),
    detailed_breakdown: faker.datatype.boolean(),
    include_comparisons: faker.datatype.boolean(),
    account_ids: faker.helpers.arrayElements(
      Array.from({ length: 5 }, () => faker.string.uuid()),
      { min: 0, max: 3 }
    ),
    category_ids: faker.helpers.arrayElements(
      Array.from({ length: 10 }, () => faker.string.uuid()),
      { min: 0, max: 5 }
    )
  },
  metadata: {
    generation_time_seconds: faker.number.float({ min: 5, max: 120, precision: 0.1 }),
    total_transactions: faker.number.int({ min: 10, max: 1000 }),
    date_range_days: faker.number.int({ min: 1, max: 365 }),
    accounts_included: faker.number.int({ min: 1, max: 5 }),
    categories_included: faker.number.int({ min: 3, max: 15 })
  },
  ...overrides
});

/**
 * Generate multiple mock reports
 */
export const createMockReports = (count: number = 5): Report[] => {
  return Array.from({ length: count }, () => createMockReport());
};

/**
 * Generate mock reports with specific statuses
 */
export const createMockReportsWithStatuses = () => {
  return [
    createMockReport({
      id: 'generated-report',
      title: 'Monthly Summary - January 2024',
      is_generated: true,
      file_size: 2048000,
      download_url: '/download/generated-report',
      error_message: null
    }),
    createMockReport({
      id: 'processing-report',
      title: 'Cash Flow Report - January 2024', 
      is_generated: false,
      file_size: null,
      download_url: null,
      error_message: null
    }),
    createMockReport({
      id: 'failed-report',
      title: 'Failed Report',
      is_generated: false,
      file_size: null,
      download_url: null,
      error_message: 'Insufficient data for report generation'
    })
  ];
};

/**
 * Generate mock analytics data
 */
export const createMockAnalytics = (overrides: Partial<AnalyticsData> = {}): AnalyticsData => ({
  total_income: faker.number.float({ min: 5000, max: 20000, precision: 0.01 }),
  total_expenses: faker.number.float({ min: 2000, max: 15000, precision: 0.01 }),
  net_result: faker.number.float({ min: -5000, max: 10000, precision: 0.01 }),
  transaction_count: faker.number.int({ min: 10, max: 500 }),
  period_days: faker.number.int({ min: 1, max: 365 }),
  average_daily_expense: faker.number.float({ min: 50, max: 500, precision: 0.01 }),
  average_daily_income: faker.number.float({ min: 100, max: 1000, precision: 0.01 }),
  top_expense_category: faker.helpers.arrayElement([
    'Food & Dining',
    'Transportation', 
    'Shopping',
    'Bills & Utilities'
  ]),
  expense_growth_rate: faker.number.float({ min: -50, max: 50, precision: 0.1 }),
  income_growth_rate: faker.number.float({ min: -30, max: 30, precision: 0.1 }),
  ...overrides
});

/**
 * Generate mock cash flow data
 */
export const createMockCashFlowData = (days: number = 30): CashFlowData => {
  const data = Array.from({ length: days }, (_, index) => {
    const date = new Date();
    date.setDate(date.getDate() - (days - 1 - index));
    
    return {
      date: date.toISOString().split('T')[0],
      income: faker.number.float({ min: 0, max: 2000, precision: 0.01 }),
      expenses: faker.number.float({ min: 0, max: 1500, precision: 0.01 }),
      net: faker.number.float({ min: -1000, max: 1500, precision: 0.01 }),
      balance: faker.number.float({ min: 1000, max: 50000, precision: 0.01 })
    };
  });
  
  return { data };
};

/**
 * Generate mock category spending data
 */
export const createMockCategorySpending = (categories: number = 8): CategorySpending => {
  const categoryNames = [
    'Food & Dining',
    'Transportation',
    'Shopping', 
    'Entertainment',
    'Bills & Utilities',
    'Healthcare',
    'Education',
    'Travel',
    'Investments',
    'Other'
  ];
  
  const data = Array.from({ length: categories }, (_, index) => ({
    category: categoryNames[index] || faker.commerce.department(),
    amount: faker.number.float({ min: 100, max: 2000, precision: 0.01 }),
    count: faker.number.int({ min: 1, max: 50 }),
    percentage: faker.number.float({ min: 1, max: 30, precision: 0.1 }),
    average_per_transaction: faker.number.float({ min: 20, max: 200, precision: 0.01 }),
    trend: faker.helpers.arrayElement(['up', 'down', 'stable']),
    trend_percentage: faker.number.float({ min: -50, max: 50, precision: 0.1 })
  }));
  
  return { data };
};

/**
 * Generate mock AI insights
 */
export const createMockAIInsights = (overrides: Partial<AIInsights> = {}): AIInsights => ({
  insights: [
    {
      type: faker.helpers.arrayElement(['success', 'warning', 'info', 'error']),
      title: faker.helpers.arrayElement([
        'Strong Financial Health',
        'High Food Spending', 
        'Irregular Income Pattern',
        'Budget Goal Achievement',
        'Unusual Transaction Activity'
      ]),
      description: faker.lorem.sentences(2),
      confidence: faker.number.float({ min: 0.6, max: 1.0, precision: 0.01 }),
      importance: faker.helpers.arrayElement(['high', 'medium', 'low'])
    },
    {
      type: faker.helpers.arrayElement(['success', 'warning', 'info']),
      title: faker.helpers.arrayElement([
        'Expense Optimization Opportunity',
        'Saving Goal Progress',
        'Category Spending Alert'
      ]),
      description: faker.lorem.sentences(2),
      confidence: faker.number.float({ min: 0.7, max: 0.95, precision: 0.01 }),
      importance: faker.helpers.arrayElement(['high', 'medium'])
    }
  ],
  predictions: {
    next_month_income: faker.number.float({ min: 3000, max: 15000, precision: 0.01 }),
    next_month_expenses: faker.number.float({ min: 2000, max: 12000, precision: 0.01 }),
    projected_savings: faker.number.float({ min: -2000, max: 5000, precision: 0.01 }),
    confidence_score: faker.number.float({ min: 0.6, max: 0.9, precision: 0.01 }),
    factors: [
      faker.helpers.arrayElement([
        'Historical spending patterns',
        'Seasonal trends',
        'Income stability',
        'Recurring expenses'
      ])
    ]
  },
  recommendations: [
    {
      title: faker.helpers.arrayElement([
        'Optimize Food Spending',
        'Reduce Transportation Costs',
        'Build Emergency Fund',
        'Automate Savings'
      ]),
      description: faker.lorem.sentence(),
      impact: faker.helpers.arrayElement(['high', 'medium', 'low']),
      effort: faker.helpers.arrayElement(['low', 'medium', 'high']),
      category: faker.helpers.arrayElement(['savings', 'optimization', 'planning']),
      estimated_savings: faker.number.float({ min: 50, max: 500, precision: 0.01 })
    },
    {
      title: faker.helpers.arrayElement([
        'Set Monthly Budget Limits',
        'Track Investment Performance',
        'Review Subscription Services'
      ]),
      description: faker.lorem.sentence(),
      impact: faker.helpers.arrayElement(['medium', 'high']),
      effort: faker.helpers.arrayElement(['low', 'medium']),
      category: faker.helpers.arrayElement(['budgeting', 'investment', 'optimization']),
      estimated_savings: faker.number.float({ min: 100, max: 800, precision: 0.01 })
    }
  ],
  key_metrics: {
    health_score: faker.number.int({ min: 60, max: 95 }),
    efficiency_score: faker.number.int({ min: 50, max: 90 }),
    growth_potential: faker.number.int({ min: 40, max: 95 }),
    risk_level: faker.helpers.arrayElement(['low', 'medium', 'high']),
    savings_rate: faker.number.float({ min: 5, max: 30, precision: 0.1 })
  },
  ai_generated: true,
  generated_at: new Date().toISOString(),
  model_version: 'gpt-4-turbo',
  ...overrides
});

/**
 * Generate mock AI insights with fallback mode
 */
export const createMockAIInsightsFallback = (): AIInsights => ({
  insights: [],
  predictions: {
    next_month_income: 0,
    next_month_expenses: 0,
    projected_savings: 0,
    confidence_score: 0,
    factors: []
  },
  recommendations: [],
  key_metrics: {
    health_score: 0,
    efficiency_score: 0,
    growth_potential: 0,
    risk_level: 'medium',
    savings_rate: 0
  },
  ai_generated: false,
  fallback_mode: true,
  error: 'AI service unavailable',
  generated_at: new Date().toISOString(),
  model_version: null
});

/**
 * Generate mock scheduled report
 */
export const createMockScheduledReport = (overrides: Partial<ScheduledReport> = {}): ScheduledReport => ({
  id: faker.string.uuid(),
  name: faker.lorem.words(3),
  description: faker.lorem.sentence(),
  report_type: faker.helpers.arrayElement([
    'daily_summary',
    'weekly_summary',
    'monthly_summary',
    'quarterly_report'
  ]),
  frequency: faker.helpers.arrayElement(['daily', 'weekly', 'monthly', 'quarterly']),
  email_recipients: Array.from({ length: faker.number.int({ min: 1, max: 4 }) }, () => faker.internet.email()),
  file_format: faker.helpers.arrayElement(['pdf', 'xlsx']),
  send_email: faker.datatype.boolean({ probability: 0.8 }),
  is_active: faker.datatype.boolean({ probability: 0.7 }),
  parameters: {
    include_charts: faker.datatype.boolean(),
    detailed_breakdown: faker.datatype.boolean(),
    include_comparisons: faker.datatype.boolean()
  },
  next_run_at: faker.date.future().toISOString(),
  last_run_at: faker.datatype.boolean({ probability: 0.6 }) ? faker.date.past().toISOString() : null,
  created_at: faker.date.past().toISOString(),
  updated_at: faker.date.recent().toISOString(),
  created_by_name: faker.person.fullName(),
  ...overrides
});

/**
 * Generate multiple scheduled reports
 */
export const createMockScheduledReports = (count: number = 3): ScheduledReport[] => {
  return Array.from({ length: count }, () => createMockScheduledReport());
};

/**
 * Generate mock account
 */
export const createMockAccount = (overrides: Partial<Account> = {}): Account => ({
  id: faker.string.uuid(),
  name: faker.helpers.arrayElement([
    'Checking Account',
    'Savings Account',
    'Credit Card',
    'Business Account'
  ]),
  display_name: faker.helpers.arrayElement([
    'Main Checking',
    'Emergency Fund', 
    'Rewards Card',
    'Company Account'
  ]),
  masked_number: `****${faker.string.numeric(4)}`,
  balance: faker.number.float({ min: -5000, max: 50000, precision: 0.01 }),
  type: faker.helpers.arrayElement(['BANK', 'CREDIT']),
  subtype: faker.helpers.arrayElement(['CHECKING', 'SAVINGS', 'CREDIT_CARD']),
  currency: 'BRL',
  institution: {
    name: faker.helpers.arrayElement([
      'Banco do Brasil',
      'Itaú',
      'Bradesco', 
      'Santander',
      'Caixa'
    ]),
    code: faker.string.numeric(3)
  },
  is_active: faker.datatype.boolean({ probability: 0.9 }),
  last_sync_at: faker.date.recent().toISOString(),
  ...overrides
});

/**
 * Generate multiple accounts
 */
export const createMockAccounts = (count: number = 3): Account[] => {
  return Array.from({ length: count }, () => createMockAccount());
};

/**
 * Generate mock category
 */
export const createMockCategory = (overrides: Partial<Category> = {}): Category => ({
  id: faker.string.uuid(),
  name: faker.helpers.arrayElement([
    'Food & Dining',
    'Transportation',
    'Shopping',
    'Entertainment', 
    'Bills & Utilities',
    'Healthcare',
    'Education',
    'Travel',
    'Salary',
    'Investments'
  ]),
  icon: faker.helpers.arrayElement([
    'utensils',
    'car',
    'shopping-cart',
    'film',
    'zap',
    'heart',
    'book',
    'plane',
    'briefcase',
    'trending-up'
  ]),
  type: faker.helpers.arrayElement(['expense', 'income', 'transfer']),
  color: faker.helpers.arrayElement([
    '#ef4444',
    '#f97316', 
    '#eab308',
    '#22c55e',
    '#06b6d4',
    '#3b82f6',
    '#8b5cf6',
    '#ec4899'
  ]),
  parent_id: faker.datatype.boolean({ probability: 0.2 }) ? faker.string.uuid() : null,
  is_active: faker.datatype.boolean({ probability: 0.95 }),
  ...overrides
});

/**
 * Generate multiple categories
 */
export const createMockCategories = (count: number = 10): Category[] => {
  return Array.from({ length: count }, () => createMockCategory());
};

/**
 * Generate mock transaction
 */
export const createMockTransaction = (overrides: Partial<Transaction> = {}): Transaction => ({
  id: faker.string.uuid(),
  account_id: faker.string.uuid(),
  category_id: faker.datatype.boolean({ probability: 0.8 }) ? faker.string.uuid() : null,
  type: faker.helpers.arrayElement(['DEBIT', 'CREDIT']),
  amount: faker.number.float({ min: 1, max: 2000, precision: 0.01 }),
  description: faker.lorem.words({ min: 2, max: 6 }),
  date: faker.date.past().toISOString().split('T')[0],
  currency: 'BRL',
  merchant: faker.datatype.boolean({ probability: 0.6 }) ? {
    name: faker.company.name(),
    category: faker.helpers.arrayElement(['grocery', 'restaurant', 'gas_station', 'retail'])
  } : null,
  location: faker.datatype.boolean({ probability: 0.4 }) ? {
    city: faker.location.city(),
    state: faker.location.state({ abbreviated: true }),
    country: 'BR'
  } : null,
  is_pending: faker.datatype.boolean({ probability: 0.1 }),
  created_at: faker.date.recent().toISOString(),
  ...overrides
});

/**
 * Generate multiple transactions
 */
export const createMockTransactions = (count: number = 50): Transaction[] => {
  return Array.from({ length: count }, () => createMockTransaction());
};

/**
 * Generate realistic transaction data for a specific period
 */
export const createRealisticTransactionData = (
  startDate: Date,
  endDate: Date,
  accountIds: string[],
  categoryIds: string[]
): Transaction[] => {
  const transactions: Transaction[] = [];
  const currentDate = new Date(startDate);
  
  while (currentDate <= endDate) {
    // Generate 0-5 transactions per day
    const dailyTransactionCount = faker.number.int({ min: 0, max: 5 });
    
    for (let i = 0; i < dailyTransactionCount; i++) {
      const isExpense = faker.datatype.boolean({ probability: 0.7 });
      
      transactions.push(createMockTransaction({
        account_id: faker.helpers.arrayElement(accountIds),
        category_id: faker.helpers.arrayElement(categoryIds),
        type: isExpense ? 'DEBIT' : 'CREDIT',
        amount: isExpense 
          ? faker.number.float({ min: 5, max: 500, precision: 0.01 })
          : faker.number.float({ min: 100, max: 5000, precision: 0.01 }),
        date: currentDate.toISOString().split('T')[0]
      }));
    }
    
    currentDate.setDate(currentDate.getDate() + 1);
  }
  
  return transactions;
};

/**
 * Mock API response structure
 */
export const createMockApiResponse = <T>(data: T, overrides: any = {}) => ({
  data,
  status: 200,
  statusText: 'OK',
  headers: {},
  config: {},
  ...overrides
});

/**
 * Mock paginated API response
 */
export const createMockPaginatedResponse = <T>(
  results: T[],
  page: number = 1,
  pageSize: number = 20
) => {
  const totalCount = results.length;
  const totalPages = Math.ceil(totalCount / pageSize);
  const startIndex = (page - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedResults = results.slice(startIndex, endIndex);
  
  return {
    count: totalCount,
    next: page < totalPages ? `?page=${page + 1}` : null,
    previous: page > 1 ? `?page=${page - 1}` : null,
    results: paginatedResults,
    page_size: pageSize,
    total_pages: totalPages
  };
};

/**
 * Mock error response
 */
export const createMockErrorResponse = (
  status: number = 400,
  message: string = 'Bad Request',
  details?: any
) => ({
  response: {
    status,
    data: {
      detail: message,
      errors: details || {},
      timestamp: new Date().toISOString()
    }
  }
});

/**
 * Mock WebSocket message
 */
export const createMockWebSocketMessage = (type: string, data: any) => ({
  type,
  data,
  timestamp: new Date().toISOString()
});

/**
 * Create complete test scenario data
 */
export const createTestScenario = (scenarioName: 'basic' | 'premium' | 'enterprise' = 'basic') => {
  const baseData = {
    accounts: createMockAccounts(2),
    categories: createMockCategories(8),
    reports: createMockReportsWithStatuses(),
    analytics: createMockAnalytics(),
    cashFlow: createMockCashFlowData(30),
    categorySpending: createMockCategorySpending(6)
  };
  
  switch (scenarioName) {
    case 'premium':
      return {
        ...baseData,
        accounts: createMockAccounts(5),
        categories: createMockCategories(15),
        reports: createMockReports(10),
        aiInsights: createMockAIInsights(),
        scheduledReports: createMockScheduledReports(3)
      };
      
    case 'enterprise':
      return {
        ...baseData,
        accounts: createMockAccounts(10),
        categories: createMockCategories(25),
        reports: createMockReports(20),
        aiInsights: createMockAIInsights(),
        scheduledReports: createMockScheduledReports(8)
      };
      
    default:
      return baseData;
  }
};

/**
 * Test data presets for common scenarios
 */
export const TestDataPresets = {
  emptyState: {
    reports: { count: 0, results: [] },
    accounts: { results: [] },
    categories: { results: [] },
    analytics: createMockAnalytics({
      total_income: 0,
      total_expenses: 0,
      net_result: 0,
      transaction_count: 0
    })
  },
  
  loadingState: null, // Used to simulate loading states
  
  errorState: createMockErrorResponse(500, 'Internal Server Error'),
  
  basicUser: createTestScenario('basic'),
  
  premiumUser: createTestScenario('premium'),
  
  enterpriseUser: createTestScenario('enterprise')
};

/**
 * Helper to create mock fetch responses
 */
export const mockFetchResponses = (responses: Array<{ url: string; response: any }>) => {
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
  
  responses.forEach(({ url, response }) => {
    mockFetch.mockImplementationOnce((input) => {
      if (typeof input === 'string' && input.includes(url)) {
        return Promise.resolve(new Response(JSON.stringify(response)));
      }
      return Promise.reject(new Error('Unexpected fetch call'));
    });
  });
};

/**
 * Helper to setup common mock responses for reports page
 */
export const setupReportsPageMocks = (scenario: 'basic' | 'premium' | 'enterprise' = 'basic') => {
  const testData = createTestScenario(scenario);
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
  
  mockFetch
    .mockResolvedValueOnce(new Response(JSON.stringify(createMockPaginatedResponse(testData.reports))))
    .mockResolvedValueOnce(new Response(JSON.stringify({ results: testData.accounts })))
    .mockResolvedValueOnce(new Response(JSON.stringify({ results: testData.categories })))
    .mockResolvedValueOnce(new Response(JSON.stringify(testData.analytics)))
    .mockResolvedValueOnce(new Response(JSON.stringify(testData.cashFlow)))
    .mockResolvedValueOnce(new Response(JSON.stringify(testData.categorySpending)));
  
  if (scenario !== 'basic' && 'aiInsights' in testData) {
    mockFetch.mockResolvedValueOnce(new Response(JSON.stringify(testData.aiInsights)));
  }
  
  return testData;
};