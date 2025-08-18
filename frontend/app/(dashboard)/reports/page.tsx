'use client';

import { useState, useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { useReportData } from '@/hooks/useReportData';
import { apiClient } from '@/lib/api-client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { EmptyState } from '@/components/ui/empty-state';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { reportsService } from '@/services/reports.service';
import { Report, ReportParameters, Category, BankAccount } from '@/types';
import { DateRange } from '@/types/reports';
import { formatCurrency, formatDate, cn } from '@/lib/utils';
import { testId, TEST_IDS, testIdWithIndex } from '@/utils/test-helpers';
import { 
  DocumentChartBarIcon,
  ArrowDownTrayIcon,
  PlayIcon,
  ClockIcon,
  CalendarIcon,
  ChartBarIcon,
  ChartPieIcon,
  BanknotesIcon,
  ArrowTrendingUpIcon as TrendingUpIcon,
  LightBulbIcon,
  SparklesIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DatePicker } from '@/components/ui/date-picker';
import { Label } from '@/components/ui/label';
import { CashFlowChart, CategoryPieChart, IncomeExpenseChart } from '@/components/charts';
import { bankingService } from '@/services/banking.service';
import { categoriesService } from '@/services/categories.service';

const REPORT_TYPES = [
  { value: 'profit_loss', label: 'DRE - Demonstração de Resultados', icon: DocumentChartBarIcon },
  { value: 'cash_flow', label: 'Fluxo de Caixa', icon: BanknotesIcon },
  { value: 'monthly_summary', label: 'Resumo Mensal', icon: ChartBarIcon },
  { value: 'category_analysis', label: 'Análise por Categoria', icon: ChartPieIcon },
];

const QUICK_PERIODS = [
  { id: 'current_month', label: 'Mês Atual', icon: CalendarIcon },
  { id: 'last_month', label: 'Mês Anterior', icon: CalendarIcon },
  { id: 'quarterly', label: 'Trimestre', icon: ChartBarIcon },
  { id: 'year_to_date', label: 'Ano Atual', icon: TrendingUpIcon },
];


// Components






function ReportsPageContent() {
  const queryClient = useQueryClient();
  
  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        await apiClient.get('/api/auth/profile/');
      } catch (error: any) {
        if (error.response?.status === 401) {
          toast.error('Sessão expirada. Por favor, faça login novamente.');
          window.location.href = '/login';
        }
      }
    };
    
    checkAuth();
  }, []);
  
  // Use custom hook for report data
  const {
    selectedPeriod,
    setSelectedPeriod,
    refetch: refreshData,
    reports: reportDataReports,
    accounts: reportDataAccounts,
    categories: reportDataCategories,
    isLoading: reportDataLoading,
    isError: reportDataError,
    error: reportDataErrorMessage,
  } = useReportData();
  
  // Fetch dashboard data using React Query
  const [dateRange, setDateRange] = useState(() => {
    const end = new Date();
    const start = new Date();
    start.setMonth(start.getMonth() - 3); // Default to last 3 months
    return { start, end };
  });

  const { data: cashFlowData = [], isLoading: cashFlowLoading } = useQuery({
    queryKey: ['cashFlow', dateRange.start.toISOString(), dateRange.end.toISOString()],
    queryFn: () => reportsService.getCashFlowData({
      start_date: dateRange.start,
      end_date: dateRange.end
    }),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // First try to get expense data, fallback to income if no expenses exist
  const { data: categorySpendingData = [], isLoading: categorySpendingLoading } = useQuery({
    queryKey: ['categorySpending', dateRange.start.toISOString(), dateRange.end.toISOString()],
    queryFn: async () => {
      // Try expense data first
      const expenseData = await reportsService.getCategorySpending({
        start_date: dateRange.start,
        end_date: dateRange.end,
        type: 'expense'
      });
      
      // If no expense data, try income data
      if (!expenseData || expenseData.length === 0) {
        const incomeData = await reportsService.getCategorySpending({
          start_date: dateRange.start,
          end_date: dateRange.end,
          type: 'income'
        });
        return incomeData;
      }
      
      return expenseData;
    },
    staleTime: 5 * 60 * 1000,
  });

  const { data: incomeVsExpensesData = [], isLoading: incomeVsExpensesLoading } = useQuery({
    queryKey: ['incomeVsExpenses', dateRange.start.toISOString(), dateRange.end.toISOString()],
    queryFn: () => reportsService.getIncomeVsExpenses({
      start_date: dateRange.start,
      end_date: dateRange.end
    }),
    staleTime: 5 * 60 * 1000,
  });

  const cashFlow = { data: cashFlowData, isLoading: cashFlowLoading };
  const categorySpending = { data: categorySpendingData, isLoading: categorySpendingLoading };
  const incomeVsExpenses = { data: incomeVsExpensesData, isLoading: incomeVsExpensesLoading };
  const analytics = { data: null, isLoading: false };
  
  const handleQuickPeriod = (periodId: string) => {
    // Implementation for quick period selection
    const today = new Date();
    let startDate = new Date();
    let endDate = new Date();
    
    switch (periodId) {
      case 'current_month':
        startDate = new Date(today.getFullYear(), today.getMonth(), 1);
        endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        break;
      case 'last_month':
        startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        endDate = new Date(today.getFullYear(), today.getMonth(), 0);
        break;
      case 'quarterly':
        // Last 3 months
        startDate = new Date(today.getFullYear(), today.getMonth() - 2, 1);
        endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        break;
      case 'year_to_date':
        startDate = new Date(today.getFullYear(), 0, 1);
        endDate = today; // Today for year-to-date
        break;
      default:
        // Default to last 3 months if no match
        startDate = new Date(today.getFullYear(), today.getMonth() - 2, 1);
        endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        break;
    }
    
    // Update both date range and selected period
    setDateRange({ start: startDate, end: endDate });
    setSelectedPeriod({
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0]
    });
  };
  
  // State
  const [reportType, setReportType] = useState<string>('profit_loss');
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [exportFormat, setExportFormat] = useState<'pdf' | 'xlsx'>('pdf');

  // Queries
  const { data: reports, isLoading, error, refetch: refetchReports } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportsService.getReports(),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  });

  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => bankingService.getAccounts(),
    staleTime: 10 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  });

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesService.getCategories(),
    staleTime: 10 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  });

  // Mutations
  const generateReportMutation = useMutation({
    mutationFn: (params: { type: string; parameters: ReportParameters; format: 'pdf' | 'xlsx' | 'csv' | 'json' }) =>
      reportsService.generateReport(params.type, params.parameters, params.format),
    onSuccess: (data: Report) => {
      toast.success('Relatório gerado com sucesso! Fazendo download...');
      refetchReports();
      
      // Fazer download automaticamente após gerar
      if (data.id && data.is_generated) {
        downloadReportMutation.mutate(data.id);
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Falha ao gerar relatório');
    },
  });

  const downloadReportMutation = useMutation({
    mutationFn: (reportId: string) => reportsService.downloadReport(reportId),
    onSuccess: (data, reportId) => {
      const report = reports?.results?.find((r: Report) => r.id === reportId);
      if (typeof window !== 'undefined') {
        const url = window.URL.createObjectURL(new Blob([data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `${report?.title || 'report'}_${new Date().toISOString().split('T')[0]}.${report?.file_format || 'pdf'}`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        toast.success('Download iniciado');
      }
    },
    onError: (error: any) => {
      toast.error('Falha ao baixar relatório');
    },
  });

  // Handlers

  const handleGenerateReport = useCallback(() => {
    if (!selectedPeriod || !selectedPeriod.start_date || !selectedPeriod.end_date) {
      toast.error('Por favor, selecione um período');
      return;
    }
    
    const parameters: ReportParameters = {
      start_date: selectedPeriod.start_date,
      end_date: selectedPeriod.end_date,
      account_ids: selectedAccounts.length > 0 ? selectedAccounts : undefined,
      category_ids: selectedCategories.length > 0 ? selectedCategories : undefined,
      title: `${REPORT_TYPES.find(t => t.value === reportType)?.label} - ${formatDate(selectedPeriod.start_date)} a ${formatDate(selectedPeriod.end_date)}`,
      description: `Relatório gerado via interface web`,
      filters: {},
    };

    generateReportMutation.mutate({ 
      type: reportType, 
      parameters, 
      format: exportFormat 
    });
  }, [selectedPeriod, selectedAccounts, selectedCategories, reportType, exportFormat, generateReportMutation]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage message="Falha ao carregar relatórios" />;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-foreground">
            Relatórios
          </h1>
          <p className="text-muted-foreground">Análises completas e insights sobre suas finanças</p>
        </div>
      </div>

      {/* Quick Reports */}
      <Card className="shadow-md">
        <CardHeader>
          <CardTitle className="text-foreground">
            Relatórios Rápidos
          </CardTitle>
          <CardDescription>Gere relatórios instantâneos para períodos comuns</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            {QUICK_PERIODS.map((period, index) => {
              const Icon = period.icon;
              return (
                <Button
                  key={period.id}
                  variant="outline"
                  className="justify-start h-auto p-4 hover:bg-muted hover:border-border transition-all duration-300 hover:shadow-md hover:scale-105"
                  onClick={() => {
                    handleQuickPeriod(period.id);
                    toast.success(`Período selecionado: ${period.label}`);
                  }}
                  {...testIdWithIndex(TEST_IDS.reports.quickPeriodButton, index)}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  <div className="text-left">
                    <div className="font-medium">{period.label}</div>
                    <div className="text-xs text-muted-foreground">Clique para visualizar</div>
                  </div>
                </Button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs defaultValue="visualizations" className="space-y-4">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="visualizations" {...testId(TEST_IDS.reports.visualizationsTab)}>Visualizações</TabsTrigger>
          <TabsTrigger value="custom" {...testId(TEST_IDS.reports.customReportsTab)}>Relatórios Personalizados</TabsTrigger>
        </TabsList>

        {/* Visualizations Tab */}
        <TabsContent value="visualizations" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Cash Flow Chart */}
            <Card className="hover:shadow-lg transition-all duration-300">
              <CardHeader>
                <CardTitle className="flex items-center text-foreground">
                  <BanknotesIcon className="h-5 w-5 mr-2 text-blue-600" />
                  Fluxo de Caixa
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CashFlowChart 
                  data={cashFlow.data} 
                  isLoading={cashFlow.isLoading}
                  height={320} 
                />
              </CardContent>
            </Card>

            {/* Category Distribution */}
            <Card className="hover:shadow-lg transition-all duration-300">
              <CardHeader>
                <CardTitle className="flex items-center text-foreground">
                  <ChartPieIcon className="h-5 w-5 mr-2 text-purple-600" />
                  Distribuição por Categoria
                  {categorySpending.data && categorySpending.data.length > 0 && (
                    <span className="ml-2 text-sm font-normal text-muted-foreground">
                      ({categorySpending.data[0]?.amount > 0 ? 'Receitas' : 'Despesas'})
                    </span>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CategoryPieChart 
                  data={categorySpending.data} 
                  isLoading={categorySpending.isLoading}
                  height={320}
                  showLegend={true}
                />
              </CardContent>
            </Card>

            {/* Income vs Expenses Comparison */}
            <Card className="lg:col-span-2 hover:shadow-lg transition-all duration-300">
              <CardHeader>
                <CardTitle className="flex items-center text-foreground">
                  <ChartBarIcon className="h-5 w-5 mr-2 text-blue-600" />
                  Comparativo: Receitas vs Despesas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <IncomeExpenseChart 
                  data={incomeVsExpenses.data} 
                  isLoading={incomeVsExpenses.isLoading}
                  height={320}
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Custom Reports Tab */}
        <TabsContent value="custom" className="space-y-6">
          <Card className="shadow-md">
            <CardHeader>
              <CardTitle className="text-foreground">
                Gerador de Relatórios Personalizados
              </CardTitle>
              <CardDescription>Configure e gere relatórios detalhados com filtros avançados</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Report Type Selection */}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                  {REPORT_TYPES.map((type, index) => {
                    const Icon = type.icon;
                    return (
                      <div
                        key={type.value}
                        className={cn(
                          "border rounded-lg p-4 cursor-pointer transition-colors",
                          reportType === type.value
                            ? "border-primary bg-primary/5"
                            : "border-gray-200 hover:border-gray-300"
                        )}
                        onClick={() => setReportType(type.value)}
                        {...testIdWithIndex(TEST_IDS.reports.reportTypeCard, index)}
                      >
                        <Icon className="h-8 w-8 mb-2 text-blue-600" />
                        <h4 className="font-medium">{type.label}</h4>
                      </div>
                    );
                  })}
                </div>

                {/* Filters */}
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <Label>Período Inicial</Label>
                    <DatePicker
                      date={selectedPeriod?.start_date ? new Date(selectedPeriod.start_date) : undefined}
                      onDateChange={(date) =>
                        setSelectedPeriod({ 
                          start_date: date?.toISOString().split('T')[0] || new Date().toISOString().split('T')[0],
                          end_date: selectedPeriod?.end_date || new Date().toISOString().split('T')[0]
                        })
                      }
                      {...testId(TEST_IDS.reports.startDatePicker)}
                    />
                  </div>
                  <div>
                    <Label>Período Final</Label>
                    <DatePicker
                      date={selectedPeriod?.end_date ? new Date(selectedPeriod.end_date) : undefined}
                      onDateChange={(date) =>
                        setSelectedPeriod({ 
                          start_date: selectedPeriod?.start_date || new Date().toISOString().split('T')[0],
                          end_date: date?.toISOString().split('T')[0] || new Date().toISOString().split('T')[0]
                        })
                      }
                      {...testId(TEST_IDS.reports.endDatePicker)}
                    />
                  </div>
                  <div>
                    <Label>Formato de Exportação</Label>
                    <Select value={exportFormat} onValueChange={(value: 'pdf' | 'xlsx') => setExportFormat(value)}>
                      <SelectTrigger {...testId(TEST_IDS.reports.formatSelect)}>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pdf">PDF</SelectItem>
                        <SelectItem value="xlsx">Excel</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Account and Category Filters */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <Label>Contas (opcional)</Label>
                    <Select 
                      value={selectedAccounts[0] || "all"}
                      onValueChange={(value) => setSelectedAccounts(value === "all" ? [] : [value])}
                    >
                      <SelectTrigger {...testId(TEST_IDS.reports.accountSelect)}>
                        <SelectValue placeholder="Todas as contas" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todas as contas</SelectItem>
                        {(accounts as any)?.results?.map((account: BankAccount) => (
                          <SelectItem key={account.id} value={account.id}>
                            {account.name || account.display_name || `Conta ${account.masked_number}`}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Categorias (opcional)</Label>
                    <Select
                      value={selectedCategories[0] || "all"}
                      onValueChange={(value) => setSelectedCategories(value === "all" ? [] : [value])}
                    >
                      <SelectTrigger {...testId(TEST_IDS.reports.categorySelect)}>
                        <SelectValue placeholder="Todas as categorias" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todas as categorias</SelectItem>
                        {(categories as any)?.results?.map((category: Category) => (
                          <SelectItem key={category.id} value={category.id}>
                            {category.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-4">
                  <Button
                    onClick={handleGenerateReport}
                    disabled={generateReportMutation.isPending}
                    className="flex-1 bg-primary hover:bg-primary/90 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
                    {...testId(TEST_IDS.reports.generateReportButton)}
                  >
                    {generateReportMutation.isPending ? (
                      <LoadingSpinner />
                    ) : (
                      <>
                        <PlayIcon className="h-4 w-4 mr-2" />
                        Gerar Relatório
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recent Reports */}
          <Card className="shadow-md">
            <CardHeader>
              <CardTitle className="text-foreground">
                Relatórios Recentes
              </CardTitle>
            </CardHeader>
            <CardContent>
              {reports?.results && reports.results.length > 0 ? (
                <div className="space-y-4" {...testId(TEST_IDS.reports.reportHistoryList)}>
                  {reports.results.map((report: Report, index: number) => (
                    <div
                      key={report.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-gradient-to-r hover:from-blue-50/30 hover:to-purple-50/30 hover:border-blue-200 transition-all duration-200 hover:shadow-md"
                      {...testIdWithIndex(TEST_IDS.reports.reportHistoryItem, index)}
                    >
                      <div className="flex items-center space-x-4">
                        <div className="p-2 bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg">
                          <DocumentChartBarIcon className="h-5 w-5 text-blue-600" />
                        </div>
                        <div>
                          <h3 className="font-medium">{report.title}</h3>
                          <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <span className="flex items-center">
                              <CalendarIcon className="h-4 w-4 mr-1" />
                              {formatDate(report.period_start)} - {formatDate(report.period_end)}
                            </span>
                            <span className="flex items-center">
                              <ClockIcon className="h-4 w-4 mr-1" />
                              Criado {formatDate(report.created_at)}
                            </span>
                            {report.is_generated ? (
                              <span className="flex items-center text-green-600">
                                <CheckCircleIcon className="h-4 w-4 mr-1" />
                                Pronto
                              </span>
                            ) : report.error_message ? (
                              <span className="flex items-center text-red-600">
                                <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                                Erro
                              </span>
                            ) : (
                              <span className="flex items-center text-yellow-600">
                                <ClockIcon className="h-4 w-4 mr-1" />
                                Processando
                              </span>
                            )}
                          </div>
                          {report.error_message && (
                            <p className="text-sm text-red-600 mt-1">{report.error_message}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        {report.is_generated && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => downloadReportMutation.mutate(report.id)}
                            disabled={downloadReportMutation.isPending}
                            {...testIdWithIndex(TEST_IDS.reports.downloadReportButton, index)}
                          >
                            <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                            Baixar
                          </Button>
                        )}
                        {!report.is_generated && !report.error_message && (
                          <Button variant="outline" size="sm" disabled>
                            <LoadingSpinner className="h-4 w-4 mr-1" />
                            Gerando...
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon={DocumentChartBarIcon}
                  title="Nenhum relatório gerado"
                  description="Gere seu primeiro relatório para obter insights sobre suas finanças"
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
      </Tabs>
    </div>
  );
}

export default function ReportsPage() {
  return (
    <ErrorBoundary>
      <ReportsPageContent />
    </ErrorBoundary>
  );
}