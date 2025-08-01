/**
 * @jest-environment jsdom
 * Frontend integration tests for reports system
 */
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { jest } from '@jest/globals';
import userEvent from '@testing-library/user-event';
import fetch from 'jest-fetch-mock';

// Mock Next.js router
const mockPush = jest.fn();
const mockReplace = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    pathname: '/reports',
    query: {},
  }),
  usePathname: () => '/reports',
  useSearchParams: () => new URLSearchParams(),
}));

// Mock toast notifications
const mockToast = {
  success: jest.fn(),
  error: jest.fn(),
  info: jest.fn(),
  loading: jest.fn(),
  dismiss: jest.fn(),
};

jest.mock('sonner', () => ({
  toast: mockToast,
}));

// Import components after mocks
import ReportsPage from '@/app/(dashboard)/reports/page';
import { api } from '@/lib/api-client';

// Enable fetch mocking
beforeEach(() => {
  fetch.resetMocks();
  jest.clearAllMocks();
});

// Test data
const mockReports = {
  count: 3,
  next: null,
  previous: null,
  results: [
    {
      id: '1',
      title: 'Monthly Summary - January 2024',
      report_type: 'monthly_summary',
      period_start: '2024-01-01',
      period_end: '2024-01-31',
      file_format: 'pdf',
      is_generated: true,
      created_at: '2024-01-15T10:30:00Z',
      created_by_name: 'Test User',
      file_size: 2048000,
      error_message: null,
    },
    {
      id: '2',
      title: 'Cash Flow Report - January 2024',
      report_type: 'cash_flow',
      period_start: '2024-01-01',
      period_end: '2024-01-31',
      file_format: 'xlsx',
      is_generated: false,
      created_at: '2024-01-16T14:20:00Z',
      created_by_name: 'Test User',
      file_size: null,
      error_message: null,
    },
    {
      id: '3',
      title: 'Failed Report',
      report_type: 'profit_loss',
      period_start: '2024-01-01',
      period_end: '2024-01-31',
      file_format: 'pdf',
      is_generated: false,
      created_at: '2024-01-17T09:45:00Z',
      created_by_name: 'Test User',
      file_size: null,
      error_message: 'Insufficient data for report generation',
    },
  ],
};

const mockAccounts = {
  results: [
    {
      id: '1',
      name: 'Checking Account',
      display_name: 'Main Checking',
      masked_number: '****1234',
      balance: 5000.0,
    },
    {
      id: '2',
      name: 'Savings Account',
      display_name: 'Emergency Fund',
      masked_number: '****5678',
      balance: 15000.0,
    },
  ],
};

const mockCategories = {
  results: [
    {
      id: '1',
      name: 'Food & Dining',
      icon: 'utensils',
      type: 'expense',
    },
    {
      id: '2',
      name: 'Transportation',
      icon: 'car',
      type: 'expense',
    },
    {
      id: '3',
      name: 'Salary',
      icon: 'briefcase',
      type: 'income',
    },
  ],
};

const mockAnalytics = {
  total_income: 8000.0,
  total_expenses: 3000.0,
  net_result: 5000.0,
  transaction_count: 45,
};

const mockCashFlowData = {
  data: [
    { date: '2024-01-01', income: 1000, expenses: 500 },
    { date: '2024-01-02', income: 1200, expenses: 600 },
    { date: '2024-01-03', income: 800, expenses: 400 },
  ],
};

const mockCategorySpending = {
  data: [
    { category: 'Food & Dining', amount: 800, count: 15 },
    { category: 'Transportation', amount: 400, count: 8 },
    { category: 'Entertainment', amount: 200, count: 5 },
  ],
};

const mockAIInsights = {
  insights: [
    {
      type: 'success',
      title: 'Strong Financial Health',
      description: 'Your expenses are well controlled this month.',
    },
    {
      type: 'warning',
      title: 'High Food Spending',
      description: 'Food expenses increased by 20% compared to last month.',
    },
  ],
  predictions: {
    next_month_income: 5000,
    next_month_expenses: 2800,
    projected_savings: 2200,
  },
  recommendations: [
    {
      title: 'Optimize Food Spending',
      description: 'Consider meal planning to reduce food costs.',
      impact: 'medium',
    },
  ],
  key_metrics: {
    health_score: 85,
    efficiency_score: 78,
    growth_potential: 90,
  },
  ai_generated: true,
};

// Test wrapper with QueryClient
const createTestWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

// Setup fetch mocks for common endpoints
const setupFetchMocks = () => {
  fetch
    .mockResponseOnce(JSON.stringify(mockReports)) // Reports list
    .mockResponseOnce(JSON.stringify(mockAccounts)) // Accounts
    .mockResponseOnce(JSON.stringify(mockCategories)) // Categories
    .mockResponseOnce(JSON.stringify(mockAnalytics)) // Analytics
    .mockResponseOnce(JSON.stringify(mockCashFlowData)) // Cash flow
    .mockResponseOnce(JSON.stringify(mockCategorySpending)) // Category spending
    .mockResponseOnce(JSON.stringify([])); // Report templates
};

describe('Reports Integration Tests', () => {
  beforeEach(() => {
    setupFetchMocks();
  });

  describe('Complete Report Generation Workflow', () => {
    it('completes full report generation workflow from UI to API', async () => {
      const user = userEvent.setup();

      render(<ReportsPage />, { wrapper: createTestWrapper() });

      // Wait for initial data to load
      await waitFor(() => {
        expect(screen.getByText('Relatórios')).toBeInTheDocument();
      });

      // Switch to custom reports tab
      const customReportsTab = screen.getByText('Relatórios Personalizados');
      await user.click(customReportsTab);

      await waitFor(() => {
        expect(screen.getByText('Gerador de Relatórios Personalizados')).toBeInTheDocument();
      });

      // Mock successful report creation
      fetch.mockResponseOnce(
        JSON.stringify({
          id: 'new-report-123',
          title: 'Generated Report',
          report_type: 'monthly_summary',
          is_generated: false,
          status: 'processing',
        })
      );

      // Fill out report generation form
      const titleInput = screen.getByLabelText(/título/i);
      await user.type(titleInput, 'Integration Test Report');

      // Select report type
      const monthlyReportButton = screen.getByText('Resumo Mensal');
      await user.click(monthlyReportButton);

      // Set date range
      const startDateInput = screen.getByLabelText(/período inicial/i);
      const endDateInput = screen.getByLabelText(/período final/i);
      
      await user.clear(startDateInput);
      await user.type(startDateInput, '2024-01-01');
      
      await user.clear(endDateInput);
      await user.type(endDateInput, '2024-01-31');

      // Generate report
      const generateButton = screen.getByText('Gerar Relatório');
      await user.click(generateButton);

      // Verify API was called
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/reports/reports/'),
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Content-Type': 'application/json',
            }),
            body: expect.stringContaining('Integration Test Report'),
          })
        );
      });

      // Verify success toast
      expect(mockToast.success).toHaveBeenCalledWith(
        expect.stringContaining('gerado com sucesso')
      );
    });

    it('handles report generation errors gracefully', async () => {
      const user = userEvent.setup();

      render(<ReportsPage />, { wrapper: createTestWrapper() });

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Relatórios')).toBeInTheDocument();
      });

      // Switch to custom reports tab
      const customReportsTab = screen.getByText('Relatórios Personalizados');
      await user.click(customReportsTab);

      await waitFor(() => {
        expect(screen.getByText('Gerador de Relatórios Personalizados')).toBeInTheDocument();
      });

      // Mock API error
      fetch.mockRejectOnce(new Error('Insufficient data for report generation'));

      // Try to generate report
      const generateButton = screen.getByText('Gerar Relatório');
      await user.click(generateButton);

      // Verify error handling
      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith(
          expect.stringContaining('Erro ao gerar relatório')
        );
      });
    });

    it('polls for report completion status', async () => {
      const user = userEvent.setup();

      render(<ReportsPage />, { wrapper: createTestWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Relatórios')).toBeInTheDocument();
      });

      // Mock report creation and status polling
      fetch
        .mockResponseOnce(
          JSON.stringify({
            id: 'polling-test-123',
            is_generated: false,
            status: 'processing',
          })
        ) // Initial creation
        .mockResponseOnce(
          JSON.stringify({
            id: 'polling-test-123',
            is_generated: false,
            status: 'generating',
          })
        ) // First poll
        .mockResponseOnce(
          JSON.stringify({
            id: 'polling-test-123',
            is_generated: true,
            status: 'completed',
          })
        ); // Second poll - completed

      // Switch to custom reports and generate
      const customReportsTab = screen.getByText('Relatórios Personalizados');
      await user.click(customReportsTab);

      await waitFor(() => {
        const generateButton = screen.getByText('Gerar Relatório');
        user.click(generateButton);
      });

      // Should eventually show completion
      await waitFor(
        () => {
          expect(mockToast.success).toHaveBeenCalledWith(
            expect.stringContaining('concluído')
          );
        },
        { timeout: 5000 }
      );
    });
  });

  describe('Report List and Management', () => {
    it('loads and displays reports list', async () => {
      render(<ReportsPage />, { wrapper: createTestWrapper() });

      // Wait for reports to load
      await waitFor(() => {
        expect(screen.getByText('Monthly Summary - January 2024')).toBeInTheDocument();
        expect(screen.getByText('Cash Flow Report - January 2024')).toBeInTheDocument();
        expect(screen.getByText('Failed Report')).toBeInTheDocument();
      });

      // Switch to custom reports tab to see detailed list
      const customReportsTab = screen.getByText('Relatórios Personalizados');
      fireEvent.click(customReportsTab);

      await waitFor(() => {
        expect(screen.getByText('Relatórios Recentes')).toBeInTheDocument();
      });

      // Verify report statuses
      expect(screen.getByText('Pronto')).toBeInTheDocument(); // Generated report
      expect(screen.getByText('Processando')).toBeInTheDocument(); // Processing report
      expect(screen.getByText('Erro')).toBeInTheDocument(); // Failed report
    });

    it('handles report download', async () => {
      const user = userEvent.setup();

      render(<ReportsPage />, { wrapper: createTestWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Relatórios')).toBeInTheDocument();
      });

      // Switch to custom reports tab
      const customReportsTab = screen.getByText('Relatórios Personalizados');
      await user.click(customReportsTab);

      await waitFor(() => {
        expect(screen.getByText('Relatórios Recentes')).toBeInTheDocument();
      });

      // Mock download URL response
      fetch.mockResponseOnce(
        JSON.stringify({
          download_url: '/api/reports/secure-download/signed-url-123/',
        })
      );

      // Click download button
      const downloadButton = screen.getAllByText('Baixar')[0];
      await user.click(downloadButton);

      // Verify download API was called
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/download/'),
          expect.objectContaining({
            method: 'GET',
          })
        );
      });
    });

    it('handles report regeneration', async () => {
      const user = userEvent.setup();

      render(<ReportsPage />, { wrapper: createTestWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Relatórios')).toBeInTheDocument();
      });

      // Switch to custom reports tab
      const customReportsTab = screen.getByText('Relatórios Personalizados');
      await user.click(customReportsTab);

      // Mock regeneration response
      fetch.mockResponseOnce(
        JSON.stringify({
          message: 'Report regeneration started',
          report_id: '1',
        })
      );

      // Find and click regenerate button (assuming it exists for generated reports)
      const regenerateButton = screen.getByText('Regerar'); // Assuming this button exists
      await user.click(regenerateButton);

      // Verify regeneration API was called
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/regenerate/'),
          expect.objectContaining({
            method: 'POST',
          })
        );
      });

      expect(mockToast.info).toHaveBeenCalledWith(
        expect.stringContaining('regeneração iniciada')
      );
    });
  });

  describe('Data Visualization Integration', () => {
    it('loads and displays analytics data', async () => {
      render(<ReportsPage />, { wrapper: createTestWrapper() });

      // Should display visualization tab by default
      await waitFor(() => {
        expect(screen.getByText('Visualizações')).toBeInTheDocument();
      });

      // Wait for charts to load
      await waitFor(() => {
        // These would be actual chart elements in a real implementation
        expect(screen.getByText('Cash Flow Chart')).toBeInTheDocument();
        expect(screen.getByText('Category Pie Chart')).toBeInTheDocument();
        expect(screen.getByText('Income vs Expense Chart')).toBeInTheDocument();
      });

      // Verify analytics API was called
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/analytics/'),
        expect.objectContaining({
          method: 'GET',
        })
      );
    });

    it('handles period selection for analytics', async () => {
      const user = userEvent.setup();

      render(<ReportsPage />, { wrapper: createTestWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Visualizações')).toBeInTheDocument();
      });

      // Mock fresh analytics data for new period
      fetch.mockResponseOnce(
        JSON.stringify({
          ...mockAnalytics,
          total_income: 9000.0,
          period_changed: true,
        })
      );

      // Select a different period
      const currentMonthButton = screen.getByText('Mês Atual');
      await user.click(currentMonthButton);

      // Should trigger new analytics request
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/analytics/'),
          expect.objectContaining({
            method: 'GET',
          })
        );
      });

      expect(mockToast.success).toHaveBeenCalledWith(
        expect.stringContaining('Período selecionado')
      );
    });

    it('handles real-time data updates', async () => {
      render(<ReportsPage />, { wrapper: createTestWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Visualizações')).toBeInTheDocument();
      });

      // Mock WebSocket or real-time update mechanism
      // In a real implementation, this might involve WebSocket mocking
      
      // Simulate data refresh
      const refreshButton = screen.getByText('Atualizar Dados'); // Assuming this exists
      
      // Mock fresh data response
      fetch.mockResponseOnce(
        JSON.stringify({
          ...mockAnalytics,
          total_income: 8500.0,
          last_updated: new Date().toISOString(),
        })
      );

      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(mockToast.success).toHaveBeenCalledWith('Dados atualizados com sucesso!');
      });
    });
  });

  describe('AI Insights Integration', () => {
    it('loads and displays AI insights', async () => {
      render(<ReportsPage />, { wrapper: createTestWrapper() });

      // Mock AI insights response
      fetch.mockResponseOnce(JSON.stringify(mockAIInsights));

      await waitFor(() => {
        expect(screen.getByText('Visualizações')).toBeInTheDocument();
      });

      // Navigate to AI insights section (assuming it exists)
      const aiInsightsButton = screen.getByText('Insights IA'); // Assuming this exists
      fireEvent.click(aiInsightsButton);

      // Wait for AI insights to load
      await waitFor(() => {
        expect(screen.getByText('Strong Financial Health')).toBeInTheDocument();
        expect(screen.getByText('High Food Spending')).toBeInTheDocument();
        expect(screen.getByText('Optimize Food Spending')).toBeInTheDocument();
      });

      // Verify AI insights API was called
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/ai-insights/'),
        expect.objectContaining({
          method: 'GET',
        })
      );
    });

    it('handles AI insights error gracefully', async () => {
      render(<ReportsPage />, { wrapper: createTestWrapper() });

      // Mock AI insights error (403 - subscription issue)
      fetch.mockRejectOnce(
        Object.assign(new Error('Forbidden'), {
          response: { status: 403 },
        })
      );

      await waitFor(() => {
        expect(screen.getByText('Visualizações')).toBeInTheDocument();
      });

      // Try to load AI insights
      const aiInsightsButton = screen.getByText('Insights IA'); // Assuming this exists
      fireEvent.click(aiInsightsButton);

      // Should show fallback message
      await waitFor(() => {
        expect(screen.getByText(/recurso não disponível/i)).toBeInTheDocument();
      });
    });

    it('allows asking AI questions', async () => {
      const user = userEvent.setup();

      render(<ReportsPage />, { wrapper: createTestWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Visualizações')).toBeInTheDocument();
      });

      // Navigate to AI chat/question section
      const aiChatButton = screen.getByText('Perguntar à IA'); // Assuming this exists
      await user.click(aiChatButton);

      // Mock AI response
      fetch.mockResponseOnce(
        JSON.stringify({
          answer: 'Based on your spending patterns, I recommend creating a monthly budget for food expenses.',
          confidence: 0.85,
          sources: ['transaction_data', 'category_analysis'],
        })
      );

      // Type question
      const questionInput = screen.getByPlaceholderText(/faça uma pergunta/i);
      await user.type(questionInput, 'Como posso reduzir meus gastos com alimentação?');

      // Submit question
      const askButton = screen.getByText('Perguntar');
      await user.click(askButton);

      // Wait for response
      await waitFor(() => {
        expect(screen.getByText(/monthly budget for food expenses/)).toBeInTheDocument();
      });

      // Verify API was called
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/ask_ai/'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('alimentação'),
        })
      );
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('handles network errors gracefully', async () => {
      // Mock network error
      fetch.mockRejectOnce(new Error('Network error'));

      render(<ReportsPage />, { wrapper: createTestWrapper() });

      // Should show error state
      await waitFor(() => {
        expect(screen.getByText(/erro ao carregar/i)).toBeInTheDocument();
      });

      expect(mockToast.error).toHaveBeenCalledWith(
        expect.stringContaining('erro ao carregar dados')
      );
    });

    it('shows loading states appropriately', async () => {
      // Mock delayed response
      fetch.mockImplementationOnce(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(new Response(JSON.stringify(mockReports))), 1000)
          )
      );

      render(<ReportsPage />, { wrapper: createTestWrapper() });

      // Should show loading spinner initially
      expect(screen.getByText('Loading...')).toBeInTheDocument();

      // Wait for data to load
      await waitFor(
        () => {
          expect(screen.getByText('Monthly Summary - January 2024')).toBeInTheDocument();
        },
        { timeout: 2000 }
      );
    });

    it('handles empty data states', async () => {
      // Mock empty responses
      fetch
        .mockResponseOnce(JSON.stringify({ count: 0, results: [] })) // Empty reports
        .mockResponseOnce(JSON.stringify({ results: [] })) // Empty accounts
        .mockResponseOnce(JSON.stringify({ results: [] })) // Empty categories
        .mockResponseOnce(JSON.stringify(mockAnalytics)) // Keep analytics
        .mockResponseOnce(JSON.stringify({ data: [] })) // Empty cash flow
        .mockResponseOnce(JSON.stringify({ data: [] })); // Empty category spending

      render(<ReportsPage />, { wrapper: createTestWrapper() });

      // Switch to custom reports tab
      const customReportsTab = screen.getByText('Relatórios Personalizados');
      fireEvent.click(customReportsTab);

      // Should show empty state
      await waitFor(() => {
        expect(screen.getByText('Nenhum relatório gerado')).toBeInTheDocument();
        expect(
          screen.getByText('Gere seu primeiro relatório para obter insights sobre suas finanças')
        ).toBeInTheDocument();
      });
    });

    it('validates form inputs before submission', async () => {
      const user = userEvent.setup();

      render(<ReportsPage />, { wrapper: createTestWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Relatórios')).toBeInTheDocument();
      });

      // Switch to custom reports tab
      const customReportsTab = screen.getByText('Relatórios Personalizados');
      await user.click(customReportsTab);

      await waitFor(() => {
        expect(screen.getByText('Gerador de Relatórios Personalizados')).toBeInTheDocument();
      });

      // Try to generate report without filling required fields
      const generateButton = screen.getByText('Gerar Relatório');
      await user.click(generateButton);

      // Should show validation errors
      await waitFor(() => {
        expect(screen.getByText(/campo obrigatório/i)).toBeInTheDocument();
      });

      // Should not make API call
      expect(fetch).not.toHaveBeenCalledWith(
        expect.stringContaining('/api/reports/reports/'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  describe('Accessibility and User Experience', () => {
    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();

      render(<ReportsPage />, { wrapper: createTestWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Relatórios')).toBeInTheDocument();
      });

      // Test tab navigation
      await user.tab();
      expect(document.activeElement).toHaveAttribute('role', 'tab');

      // Test enter key activation
      await user.keyboard('{Enter}');

      // Should navigate to the tab
      await waitFor(() => {
        expect(document.activeElement).toHaveTextContent('Visualizações');
      });
    });

    it('provides proper ARIA labels and roles', async () => {
      render(<ReportsPage />, { wrapper: createTestWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Relatórios')).toBeInTheDocument();
      });

      // Check main heading
      const mainHeading = screen.getByRole('heading', { level: 1 });
      expect(mainHeading).toHaveTextContent('Relatórios');

      // Check tab navigation
      const tabs = screen.getAllByRole('tab');
      expect(tabs.length).toBeGreaterThan(0);

      // Check button accessibility
      const buttons = screen.getAllByRole('button');
      buttons.forEach((button) => {
        expect(button).toBeEnabled();
      });
    });

    it('shows appropriate loading and progress indicators', async () => {
      // Mock slow API response
      fetch.mockImplementationOnce(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(new Response(JSON.stringify(mockReports))), 500)
          )
      );

      render(<ReportsPage />, { wrapper: createTestWrapper() });

      // Should show loading state
      expect(screen.getByText('Loading...')).toBeInTheDocument();

      // Wait for completion
      await waitFor(
        () => {
          expect(screen.getByText('Monthly Summary - January 2024')).toBeInTheDocument();
        },
        { timeout: 1000 }
      );

      // Loading should be gone
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });
  });
});

describe('WebSocket Integration Tests', () => {
  let mockWebSocket: jest.Mocked<WebSocket>;

  beforeEach(() => {
    // Mock WebSocket
    mockWebSocket = {
      send: jest.fn(),
      close: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      readyState: WebSocket.OPEN,
      url: 'ws://localhost/ws/reports/',
      protocol: '',
      extensions: '',
      bufferedAmount: 0,
      binaryType: 'blob' as BinaryType,
      onopen: null,
      onclose: null,
      onmessage: null,
      onerror: null,
      dispatchEvent: jest.fn(),
      CONNECTING: WebSocket.CONNECTING,
      OPEN: WebSocket.OPEN,
      CLOSING: WebSocket.CLOSING,
      CLOSED: WebSocket.CLOSED,
    };

    global.WebSocket = jest.fn(() => mockWebSocket) as any;
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('connects to WebSocket for real-time updates', async () => {
    setupFetchMocks();

    render(<ReportsPage />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Relatórios')).toBeInTheDocument();
    });

    // Should establish WebSocket connection
    expect(global.WebSocket).toHaveBeenCalledWith(
      expect.stringContaining('ws://localhost/ws/reports/')
    );
  });

  it('handles report progress updates via WebSocket', async () => {
    setupFetchMocks();

    render(<ReportsPage />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Relatórios')).toBeInTheDocument();
    });

    // Simulate WebSocket message for report progress
    const progressMessage = {
      type: 'report_progress',
      data: {
        report_id: 'test-123',
        status: 'generating_charts',
        progress: 50,
      },
    };

    // Trigger WebSocket message handler
    act(() => {
      const messageHandler = mockWebSocket.addEventListener.mock.calls.find(
        (call) => call[0] === 'message'
      )?.[1];
      
      if (messageHandler) {
        messageHandler({
          data: JSON.stringify(progressMessage),
        } as MessageEvent);
      }
    });

    // Should show progress indicator
    await waitFor(() => {
      // In a real implementation, this would show progress
      expect(screen.getByText(/50%/)).toBeInTheDocument();
    });
  });

  it('handles report completion notifications', async () => {
    setupFetchMocks();

    render(<ReportsPage />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Relatórios')).toBeInTheDocument();
    });

    // Simulate completion message
    const completionMessage = {
      type: 'report_completed',
      data: {
        report_id: 'test-123',
        title: 'Completed Report',
        download_url: '/download/test-123',
      },
    };

    // Trigger message
    act(() => {
      const messageHandler = mockWebSocket.addEventListener.mock.calls.find(
        (call) => call[0] === 'message'
      )?.[1];
      
      if (messageHandler) {
        messageHandler({
          data: JSON.stringify(completionMessage),
        } as MessageEvent);
      }
    });

    // Should show completion notification
    await waitFor(() => {
      expect(mockToast.success).toHaveBeenCalledWith(
        expect.stringContaining('Relatório concluído')
      );
    });
  });
});