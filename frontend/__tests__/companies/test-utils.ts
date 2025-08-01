/**
 * Test utilities for companies module tests
 */
import { QueryClient } from '@tanstack/react-query';
import { render as rtlRender, RenderOptions } from '@testing-library/react';
import { ReactElement, ReactNode } from 'react';
import { SubscriptionPlan, Company, UsageLimits, SubscriptionStatus } from '@/services/unified-subscription.service';

// Mock data factories
export const mockSubscriptionPlan = (overrides: Partial<SubscriptionPlan> = {}): SubscriptionPlan => ({
  id: 1,
  name: 'Basic',
  slug: 'basic',
  price_monthly: 9.99,
  price_yearly: 99.99,
  yearly_discount: 17,
  max_transactions: 500,
  max_bank_accounts: 2,
  max_ai_requests: 50,
  has_ai_insights: false,
  has_advanced_reports: false,
  stripe_price_id_monthly: 'price_test_monthly',
  stripe_price_id_yearly: 'price_test_yearly',
  is_active: true,
  display_order: 1,
  ...overrides,
});

export const mockPremiumPlan = (): SubscriptionPlan => mockSubscriptionPlan({
  id: 2,
  name: 'Premium',
  slug: 'premium',
  price_monthly: 19.99,
  price_yearly: 199.99,
  max_transactions: 2000,
  max_bank_accounts: 5,
  max_ai_requests: 200,
  has_ai_insights: true,
  has_advanced_reports: true,
});

export const mockEnterprisePlan = (): SubscriptionPlan => mockSubscriptionPlan({
  id: 3,
  name: 'Enterprise',
  slug: 'enterprise',
  price_monthly: 49.99,
  price_yearly: 499.99,
  max_transactions: 10000,
  max_bank_accounts: 20,
  max_ai_requests: 1000,
  has_ai_insights: true,
  has_advanced_reports: true,
});

export const mockCompany = (overrides: Partial<Company> = {}): Company => ({
  id: 'company-1',
  name: 'Test Company',
  owner_email: 'owner@test.com',
  subscription_plan: mockSubscriptionPlan(),
  subscription_status: 'trial',
  billing_cycle: 'monthly',
  trial_ends_at: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(), // 14 days from now
  is_trial_active: true,
  days_until_trial_ends: 14,
  current_month_transactions: 100,
  current_month_ai_requests: 25,
  created_at: new Date().toISOString(),
  ...overrides,
});

export const mockActiveCompany = (): Company => mockCompany({
  subscription_status: 'active',
  trial_ends_at: null,
  is_trial_active: false,
  days_until_trial_ends: 0,
});

export const mockExpiredTrialCompany = (): Company => mockCompany({
  subscription_status: 'trial',
  trial_ends_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
  is_trial_active: false,
  days_until_trial_ends: 0,
});

export const mockUsageLimits = (overrides: Partial<UsageLimits> = {}): UsageLimits => ({
  transactions: {
    used: 150,
    limit: 500,
    percentage: 30,
  },
  bank_accounts: {
    used: 1,
    limit: 2,
    percentage: 50,
  },
  ai_requests: {
    used: 25,
    limit: 50,
    percentage: 50,
  },
  ...overrides,
});

export const mockSubscriptionStatus = (overrides: Partial<SubscriptionStatus> = {}): SubscriptionStatus => ({
  subscription_status: 'trial',
  plan: mockSubscriptionPlan(),
  trial_days_left: 14,
  trial_ends_at: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
  requires_payment_setup: true,
  has_payment_method: false,
  ...overrides,
});

export const mockActiveSubscriptionStatus = (): SubscriptionStatus => mockSubscriptionStatus({
  subscription_status: 'active',
  trial_days_left: 0,
  trial_ends_at: null,
  requires_payment_setup: false,
  has_payment_method: true,
});

// Mock API responses
export const mockApiResponses = {
  subscriptionPlans: [
    mockSubscriptionPlan(),
    mockPremiumPlan(),
    mockEnterprisePlan(),
  ],
  company: mockCompany(),
  usageLimits: mockUsageLimits(),
  subscriptionStatus: mockSubscriptionStatus(),
};

// Mock fetch functions
export const mockFetch = (data: any, status = 200) => {
  return jest.fn().mockResolvedValue({
    ok: status < 400,
    status,
    json: jest.fn().mockResolvedValue(data),
  });
};

export const mockApiError = (status = 400, message = 'Bad Request') => {
  return jest.fn().mockRejectedValue({
    response: {
      status,
      data: { error: message },
    },
  });
};

// Test wrapper with providers
interface TestWrapperProps {
  children: ReactNode;
  queryClient?: QueryClient;
}

const TestWrapper = ({ children, queryClient }: TestWrapperProps) => {
  const client = queryClient || new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return (
    <div data-testid="test-wrapper">
      {children}
    </div>
  );
};

// Custom render function
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient;
}

export const render = (ui: ReactElement, options: CustomRenderOptions = {}) => {
  const { queryClient, ...renderOptions } = options;
  
  const Wrapper = ({ children }: { children: ReactNode }) => (
    <TestWrapper queryClient={queryClient}>
      {children}
    </TestWrapper>
  );

  return rtlRender(ui, { wrapper: Wrapper, ...renderOptions });
};

// Mock auth store
export const mockAuthStore = {
  user: {
    id: 'user-1',
    email: 'test@example.com',
    name: 'Test User',
  },
  isAuthenticated: true,
  login: jest.fn(),
  logout: jest.fn(),
  updateUser: jest.fn(),
};

// Mock router
export const mockRouter = {
  push: jest.fn(),
  replace: jest.fn(),
  back: jest.fn(),
  forward: jest.fn(),
  refresh: jest.fn(),
  prefetch: jest.fn(),
};

// Usage scenarios for testing
export const usageScenarios = {
  underLimit: mockUsageLimits({
    transactions: { used: 100, limit: 500, percentage: 20 },
    bank_accounts: { used: 1, limit: 2, percentage: 50 },
    ai_requests: { used: 10, limit: 50, percentage: 20 },
  }),
  
  nearLimit: mockUsageLimits({
    transactions: { used: 450, limit: 500, percentage: 90 },
    bank_accounts: { used: 2, limit: 2, percentage: 100 },
    ai_requests: { used: 45, limit: 50, percentage: 90 },
  }),
  
  overLimit: mockUsageLimits({
    transactions: { used: 600, limit: 500, percentage: 120 },
    bank_accounts: { used: 3, limit: 2, percentage: 150 },
    ai_requests: { used: 60, limit: 50, percentage: 120 },
  }),
};

// Subscription status scenarios
export const subscriptionScenarios = {
  activeTrial: mockSubscriptionStatus({
    subscription_status: 'trial',
    trial_days_left: 10,
    requires_payment_setup: true,
  }),
  
  expiringSoon: mockSubscriptionStatus({
    subscription_status: 'trial',
    trial_days_left: 2,
    requires_payment_setup: true,
  }),
  
  expired: mockSubscriptionStatus({
    subscription_status: 'expired',
    trial_days_left: 0,
    trial_ends_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    requires_payment_setup: true,
  }),
  
  active: mockActiveSubscriptionStatus(),
  
  cancelled: mockSubscriptionStatus({
    subscription_status: 'cancelled',
    trial_days_left: 0,
    requires_payment_setup: false,
    has_payment_method: true,
  }),
};

// Helper functions for testing
export const waitForApiCall = (mockFn: jest.Mock, timeout = 1000) => {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const checkCall = () => {
      if (mockFn.mock.calls.length > 0) {
        resolve(mockFn);
      } else if (Date.now() - startTime > timeout) {
        reject(new Error('API call timeout'));
      } else {
        setTimeout(checkCall, 10);
      }
    };
    
    checkCall();
  });
};

export const createQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      gcTime: 0,
    },
    mutations: {
      retry: false,
    },
  },
});

// Mock console methods to avoid test noise
export const mockConsole = () => {
  const originalConsole = { ...console };
  
  beforeEach(() => {
    console.warn = jest.fn();
    console.error = jest.fn();
    console.log = jest.fn();
  });
  
  afterEach(() => {
    Object.assign(console, originalConsole);
  });
};

// Assertion helpers
export const expectUsageLimitsStructure = (usageLimits: any) => {
  expect(usageLimits).toHaveProperty('transactions');
  expect(usageLimits).toHaveProperty('bank_accounts');
  expect(usageLimits).toHaveProperty('ai_requests');
  
  ['transactions', 'bank_accounts', 'ai_requests'].forEach(key => {
    expect(usageLimits[key]).toHaveProperty('used');
    expect(usageLimits[key]).toHaveProperty('limit');
    expect(usageLimits[key]).toHaveProperty('percentage');
  });
};

export const expectSubscriptionPlanStructure = (plan: any) => {
  const requiredFields = [
    'id', 'name', 'slug', 'price_monthly', 'price_yearly',
    'max_transactions', 'max_bank_accounts', 'max_ai_requests',
    'has_ai_insights', 'has_advanced_reports',
  ];
  
  requiredFields.forEach(field => {
    expect(plan).toHaveProperty(field);
  });
};

export const expectCompanyStructure = (company: any) => {
  const requiredFields = [
    'id', 'name', 'owner_email', 'subscription_status',
    'billing_cycle', 'is_trial_active', 'days_until_trial_ends',
    'current_month_transactions', 'current_month_ai_requests',
  ];
  
  requiredFields.forEach(field => {
    expect(company).toHaveProperty(field);
  });
};

// Performance testing helpers
export const measureRenderTime = (renderFn: () => void) => {
  const start = performance.now();
  renderFn();
  const end = performance.now();
  return end - start;
};

export const expectFastRender = (renderFn: () => void, maxTime = 100) => {
  const renderTime = measureRenderTime(renderFn);
  expect(renderTime).toBeLessThan(maxTime);
};

// Mock service responses
export const mockUnifiedSubscriptionService = {
  getSubscriptionPlans: jest.fn().mockResolvedValue(mockApiResponses.subscriptionPlans),
  getCompanyDetails: jest.fn().mockResolvedValue(mockApiResponses.company),
  getUsageLimits: jest.fn().mockResolvedValue(mockApiResponses.usageLimits),
  getSubscriptionStatus: jest.fn().mockResolvedValue(mockApiResponses.subscriptionStatus),
  canUseFeature: jest.fn().mockReturnValue(false),
  isUsageLimitReached: jest.fn().mockReturnValue(false),
  getUsageWarningLevel: jest.fn().mockReturnValue('none'),
};

export default {
  mockSubscriptionPlan,
  mockCompany,
  mockUsageLimits,
  mockSubscriptionStatus,
  mockApiResponses,
  render,
  mockAuthStore,
  usageScenarios,
  subscriptionScenarios,
  expectUsageLimitsStructure,
  expectSubscriptionPlanStructure,
  expectCompanyStructure,
};