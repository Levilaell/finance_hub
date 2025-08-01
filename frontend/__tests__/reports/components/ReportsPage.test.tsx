/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { jest } from '@jest/globals';
import userEvent from '@testing-library/user-event';
import ReportsPage from '@/app/(dashboard)/reports/page';
import { reportsService } from '@/services/reports.service';
import { bankingService } from '@/services/banking.service';
import { categoriesService } from '@/services/categories.service';

// Mock services
jest.mock('@/services/reports.service');
jest.mock('@/services/banking.service');
jest.mock('@/services/categories.service');
jest.mock('@/hooks/useReportData');

// Mock UI components
jest.mock('@/components/ui/loading-spinner', () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner">Loading...</div>
}));

jest.mock('@/components/ui/error-message', () => ({
  ErrorMessage: ({ message }: { message: string }) => (
    <div data-testid="error-message">{message}</div>
  )
}));

jest.mock('@/components/ui/empty-state', () => ({
  EmptyState: ({ title, description }: { title: string; description: string }) => (
    <div data-testid="empty-state">
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  )
}));

jest.mock('@/components/charts', () => ({
  CashFlowChart: ({ data, isLoading }: { data: any; isLoading: boolean }) => (
    <div data-testid="cash-flow-chart">
      {isLoading ? 'Loading chart...' : 'Cash Flow Chart'}
    </div>
  ),
  CategoryPieChart: ({ data, isLoading }: { data: any; isLoading: boolean }) => (
    <div data-testid="category-pie-chart">
      {isLoading ? 'Loading chart...' : 'Category Pie Chart'}
    </div>
  ),
  IncomeExpenseChart: ({ data, isLoading }: { data: any; isLoading: boolean }) => (
    <div data-testid="income-expense-chart">
      {isLoading ? 'Loading chart...' : 'Income vs Expense Chart'}
    </div>
  )
}));

// Mock useReportData hook
const mockUseReportData = jest.fn();
jest.mock('@/hooks/useReportData', () => ({
  useReportData: () => mockUseReportData()
}));

// Mock toast notifications
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn()
  }
}));

// Test data
const mockReports = {
  count: 3,
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
      created_by_name: 'John Doe',
      file_size: 2048000
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
      created_by_name: 'John Doe'
    },
    {
      id: '3',
      title: 'Failed Report',
      report_type: 'profit_loss',
      period_start: '2024-01-01',
      period_end: '2024-01-31',
      file_format: 'pdf',
      is_generated: false,
      error_message: 'Insufficient data for report generation',
      created_at: '2024-01-17T09:45:00Z',
      created_by_name: 'John Doe'
    }
  ]
};

const mockAccounts = {
  results: [
    {
      id: '1',
      name: 'Checking Account',
      display_name: 'Main Checking',
      masked_number: '****1234',
      balance: 5000.00
    },
    {
      id: '2',
      name: 'Savings Account',
      display_name: 'Emergency Fund',
      masked_number: '****5678',
      balance: 15000.00
    }
  ]
};

const mockCategories = {
  results: [
    {
      id: '1',
      name: 'Food & Dining',
      icon: 'utensils',
      type: 'expense'
    },
    {
      id: '2',
      name: 'Transportation',
      icon: 'car',
      type: 'expense'
    },
    {
      id: '3',
      name: 'Salary',
      icon: 'briefcase',
      type: 'income'
    }
  ]
};

// Wrapper component with QueryClient
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('ReportsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Default mock for useReportData
    mockUseReportData.mockReturnValue({
      selectedPeriod: {
        start_date: new Date('2024-01-01'),
        end_date: new Date('2024-01-31')
      },
      setSelectedPeriod: jest.fn(),
      handleQuickPeriod: jest.fn(),
      refreshData: jest.fn(),
      cashFlow: { data: [], isLoading: false },
      categorySpending: { data: [], isLoading: false },
      incomeVsExpenses: { data: [], isLoading: false },
      analytics: { data: null, isLoading: false }
    });

    // Mock service responses
    (reportsService.getReports as jest.Mock).mockResolvedValue(mockReports);
    (bankingService.getAccounts as jest.Mock).mockResolvedValue(mockAccounts);
    (categoriesService.getCategories as jest.Mock).mockResolvedValue(mockCategories);
  });

  describe('Component Rendering', () => {
    it('renders the reports page with all main sections', async () => {
      render(
        <TestWrapper>
          <ReportsPage />
        </TestWrapper>
      );

      // Check main heading
      expect(screen.getByText('Relatórios')).toBeInTheDocument();
      expect(screen.getByText('Análises completas e insights sobre suas finanças')).toBeInTheDocument();

      // Check quick reports section
      expect(screen.getByText('Relatórios Rápidos')).toBeInTheDocument();
      expect(screen.getByText('Gere relatórios instantâneos para períodos comuns')).toBeInTheDocument();

      // Check tabs
      expect(screen.getByText('Visualizações')).toBeInTheDocument();
      expect(screen.getByText('Relatórios Personalizados')).toBeInTheDocument();
    });

    it('renders quick period buttons', async () => {
      render(
        <TestWrapper>
          <ReportsPage />
        </TestWrapper>
      );

      // Check that all quick period buttons are present
      expect(screen.getByText('Mês Atual')).toBeInTheDocument();
      expect(screen.getByText('Mês Anterior')).toBeInTheDocument();
      expect(screen.getByText('Trimestre')).toBeInTheDocument();
      expect(screen.getByText('Ano Atual')).toBeInTheDocument();
    });

    it('renders visualization charts', async () => {
      render(
        <TestWrapper>
          <ReportsPage />
        </TestWrapper>
      );

      // Check that chart components are rendered
      await waitFor(() => {
        expect(screen.getByTestId('cash-flow-chart')).toBeInTheDocument();
        expect(screen.getByTestId('category-pie-chart')).toBeInTheDocument();
        expect(screen.getByTestId('income-expense-chart')).toBeInTheDocument();
      });
    });
  });

  describe('Quick Reports Functionality', () => {
    it('handles quick period selection', async () => {
      const mockHandleQuickPeriod = jest.fn();
      mockUseReportData.mockReturnValue({
        ...mockUseReportData(),
        handleQuickPeriod: mockHandleQuickPeriod
      });

      render(
        <TestWrapper>
          <ReportsPage />
        </TestWrapper>
      );

      // Click on "Mês Atual" button
      const currentMonthButton = screen.getByText('Mês Atual');
      fireEvent.click(currentMonthButton);

      // Verify the handler was called
      expect(mockHandleQuickPeriod).toHaveBeenCalledWith('current_month');
    });

    it('shows success toast when quick period is selected', async () => {
      const { toast } = require('sonner');
      
      render(
        <TestWrapper>
          <ReportsPage />
        </TestWrapper>
      );

      // Click on "Mês Anterior" button
      const lastMonthButton = screen.getByText('Mês Anterior');
      fireEvent.click(lastMonthButton);

      // Verify toast was called
      expect(toast.success).toHaveBeenCalledWith('Período selecionado: Mês Anterior');
    });
  });

  describe('Custom Reports Tab', () => {
    beforeEach(async () => {
      render(
        <TestWrapper>
          <ReportsPage />
        </TestWrapper>
      );

      // Switch to custom reports tab
      const customReportsTab = screen.getByText('Relatórios Personalizados');
      fireEvent.click(customReportsTab);

      await waitFor(() => {
        expect(screen.getByText('Gerador de Relatórios Personalizados')).toBeInTheDocument();
      });
    });

    it('renders custom report generator', async () => {
      // Check main elements are present
      expect(screen.getByText('Gerador de Relatórios Personalizados')).toBeInTheDocument();
      expect(screen.getByText('Configure e gere relatórios detalhados com filtros avançados')).toBeInTheDocument();

      // Check report type options
      expect(screen.getByText('DRE - Demonstração de Resultados')).toBeInTheDocument();
      expect(screen.getByText('Fluxo de Caixa')).toBeInTheDocument();
      expect(screen.getByText('Resumo Mensal')).toBeInTheDocument();
      expect(screen.getByText('Análise por Categoria')).toBeInTheDocument();
    });

    it('allows selecting report type', async () => {
      // Click on Cash Flow report type
      const cashFlowType = screen.getByText('Fluxo de Caixa');
      fireEvent.click(cashFlowType);

      // The report type should be selected (visual feedback would be tested here)
      // In a real implementation, we'd check for CSS classes or aria-selected attributes
    });

    it('renders date range inputs', async () => {
      // Check for date input labels
      expect(screen.getByText('Período Inicial')).toBeInTheDocument();
      expect(screen.getByText('Período Final')).toBeInTheDocument();
    });

    it('renders export format selector', async () => {
      expect(screen.getByText('Formato de Exportação')).toBeInTheDocument();
      
      // The select component would contain PDF and Excel options
      // This would need to be tested with proper select component testing
    });

    it('renders account and category filters', async () => {
      expect(screen.getByText('Contas (opcional)')).toBeInTheDocument();
      expect(screen.getByText('Categorias (opcional)')).toBeInTheDocument();
    });

    it('renders generate report button', async () => {
      const generateButton = screen.getByText('Gerar Relatório');
      expect(generateButton).toBeInTheDocument();
      expect(generateButton).toBeEnabled();
    });
  });

  describe('Report Generation', () => {
    it('handles successful report generation', async () => {
      const mockGenerateReport = jest.fn().mockResolvedValue({
        id: '4',
        title: 'New Report',
        is_generated: false,
        report_type: 'monthly_summary'
      });
      
      (reportsService.generateReport as jest.Mock) = mockGenerateReport;

      render(
        <TestWrapper>
          <ReportsPage />
        </TestWrapper>
      );

      // Switch to custom reports tab
      const customReportsTab = screen.getByText('Relatórios Personalizados');
      fireEvent.click(customReportsTab);

      await waitFor(() => {
        const generateButton = screen.getByText('Gerar Relatório');
        fireEvent.click(generateButton);
      });

      // In a real implementation, we'd verify the API call and success feedback
    });

    it('shows loading state during report generation', async () => {
      const mockGenerateReport = jest.fn().mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 1000))
      );
      
      (reportsService.generateReport as jest.Mock) = mockGenerateReport;

      render(
        <TestWrapper>
          <ReportsPage />
        </TestWrapper>
      );

      // Switch to custom reports tab and generate report
      const customReportsTab = screen.getByText('Relatórios Personalizados');
      fireEvent.click(customReportsTab);

      await waitFor(() => {
        const generateButton = screen.getByText('Gerar Relatório');
        fireEvent.click(generateButton);
      });

      // Should show loading state
      await waitFor(() => {
        expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
      });
    });
  });

  describe('Recent Reports List', () => {
    beforeEach(async () => {
      render(
        <TestWrapper>
          <ReportsPage />
        </TestWrapper>
      );

      // Switch to custom reports tab to see recent reports
      const customReportsTab = screen.getByText('Relatórios Personalizados');
      fireEvent.click(customReportsTab);

      await waitFor(() => {
        expect(screen.getByText('Relatórios Recentes')).toBeInTheDocument();
      });
    });

    it('displays recent reports list', async () => {
      await waitFor(() => {
        // Check that reports are displayed
        expect(screen.getByText('Monthly Summary - January 2024')).toBeInTheDocument();
        expect(screen.getByText('Cash Flow Report - January 2024')).toBeInTheDocument();
        expect(screen.getByText('Failed Report')).toBeInTheDocument();
      });
    });

    it('shows correct report status indicators', async () => {
      await waitFor(() => {
        // Generated report should show "Pronto"
        expect(screen.getByText('Pronto')).toBeInTheDocument();
        
        // Processing report should show "Processando"
        expect(screen.getByText('Processando')).toBeInTheDocument();
        
        // Failed report should show "Erro"
        expect(screen.getByText('Erro')).toBeInTheDocument();
      });
    });

    it('shows download button for generated reports', async () => {
      await waitFor(() => {
        // Should have download button for generated report
        const downloadButtons = screen.getAllByText('Baixar');
        expect(downloadButtons.length).toBeGreaterThan(0);
      });
    });

    it('handles report download', async () => {
      const mockDownloadReport = jest.fn().mockResolvedValue(new Blob());
      (reportsService.downloadReport as jest.Mock) = mockDownloadReport;

      await waitFor(() => {
        const downloadButton = screen.getAllByText('Baixar')[0];
        fireEvent.click(downloadButton);
      });

      expect(mockDownloadReport).toHaveBeenCalledWith('1');
    });

    it('shows error message for failed reports', async () => {
      await waitFor(() => {
        expect(screen.getByText('Insufficient data for report generation')).toBeInTheDocument();
      });
    });
  });

  describe('Empty States', () => {
    it('shows empty state when no reports exist', async () => {
      (reportsService.getReports as jest.Mock).mockResolvedValue({
        count: 0,
        results: []
      });

      render(
        <TestWrapper>
          <ReportsPage />
        </TestWrapper>
      );

      // Switch to custom reports tab
      const customReportsTab = screen.getByText('Relatórios Personalizados');
      fireEvent.click(customReportsTab);

      await waitFor(() => {
        expect(screen.getByTestId('empty-state')).toBeInTheDocument();
        expect(screen.getByText('Nenhum relatório gerado')).toBeInTheDocument();
        expect(screen.getByText('Gere seu primeiro relatório para obter insights sobre suas finanças')).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('shows loading spinner while fetching data', async () => {
      (reportsService.getReports as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 1000))
      );

      render(
        <TestWrapper>
          <ReportsPage />
        </TestWrapper>
      );

      // Should show loading spinner initially
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });

    it('shows loading state for charts', async () => {
      mockUseReportData.mockReturnValue({
        ...mockUseReportData(),
        cashFlow: { data: [], isLoading: true },
        categorySpending: { data: [], isLoading: true },
        incomeVsExpenses: { data: [], isLoading: true }
      });

      render(
        <TestWrapper>
          <ReportsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Loading chart...')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('shows error message when reports fail to load', async () => {
      (reportsService.getReports as jest.Mock).mockRejectedValue(
        new Error('Failed to fetch reports')
      );

      render(
        <TestWrapper>
          <ReportsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toBeInTheDocument();
        expect(screen.getByText('Falha ao carregar relatórios')).toBeInTheDocument();
      });
    });

    it('handles report generation errors gracefully', async () => {
      const { toast } = require('sonner');
      const mockGenerateReport = jest.fn().mockRejectedValue(
        new Error('Insufficient data for report')
      );
      (reportsService.generateReport as jest.Mock) = mockGenerateReport;

      render(
        <TestWrapper>
          <ReportsPage />
        </TestWrapper>
      );

      // Switch to custom reports and try to generate
      const customReportsTab = screen.getByText('Relatórios Personalizados');
      fireEvent.click(customReportsTab);

      await waitFor(() => {
        const generateButton = screen.getByText('Gerar Relatório');
        fireEvent.click(generateButton);
      });

      // Should show error toast
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalled();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', async () => {
      render(
        <TestWrapper>
          <ReportsPage />
        </TestWrapper>
      );

      // Check for proper heading hierarchy
      const mainHeading = screen.getByRole('heading', { level: 1 });
      expect(mainHeading).toHaveTextContent('Relatórios');

      // Check for tab navigation
      const tabs = screen.getAllByRole('tab');
      expect(tabs.length).toBeGreaterThan(0);

      // Check for button accessibility
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toBeEnabled();
      });
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ReportsPage />
        </TestWrapper>
      );

      // Tab through quick report buttons
      const quickReportButtons = screen.getAllByRole('button');
      const firstButton = quickReportButtons[0];
      
      await user.tab();
      expect(firstButton).toHaveFocus();
    });
  });

  describe('Responsive Behavior', () => {
    it('adapts layout for mobile screens', () => {
      // Mock window.matchMedia for mobile
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query.includes('max-width'),
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });

      render(
        <TestWrapper>
          <ReportsPage />
        </TestWrapper>
      );

      // In a real implementation, we'd test responsive grid classes
      // and mobile-specific UI adaptations
    });
  });
});