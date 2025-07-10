'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { EmptyState } from '@/components/ui/empty-state';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { reportsService } from '@/services/reports.service';
import { Report, ReportParameters, Account, Category } from '@/types';
import { formatCurrency, formatDate, cn } from '@/lib/utils';
import { 
  DocumentChartBarIcon,
  ArrowDownTrayIcon,
  PlayIcon,
  PlusIcon,
  ClockIcon,
  CalendarIcon,
  ChartBarIcon,
  ChartPieIcon,
  BanknotesIcon,
  ArrowTrendingUpIcon as TrendingUpIcon,
  LightBulbIcon,
  EnvelopeIcon,
  SparklesIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon
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
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Legend,
  AreaChart,
  Area,
  ComposedChart
} from 'recharts';
import { bankingService } from '@/services/banking.service';
import { categoriesService } from '@/services/categories.service';

const REPORT_TYPES = [
  { value: 'profit_loss', label: 'DRE - Demonstração de Resultados', icon: DocumentChartBarIcon },
  { value: 'cash_flow', label: 'Fluxo de Caixa', icon: BanknotesIcon },
  { value: 'monthly_summary', label: 'Resumo Mensal', icon: ChartBarIcon },
  { value: 'category_analysis', label: 'Análise por Categoria', icon: ChartPieIcon },
];

const FREQUENCIES = [
  { value: 'daily', label: 'Diário' },
  { value: 'weekly', label: 'Semanal' },
  { value: 'monthly', label: 'Mensal' },
  { value: 'quarterly', label: 'Trimestral' },
  { value: 'yearly', label: 'Anual' },
];

const QUICK_PERIODS = [
  { id: 'current_month', label: 'Mês Atual', icon: CalendarIcon },
  { id: 'last_month', label: 'Mês Anterior', icon: CalendarIcon },
  { id: 'quarter', label: 'Trimestre', icon: ChartBarIcon },
  { id: 'year', label: 'Ano Atual', icon: TrendingUpIcon },
];

const CHART_COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658'];

interface AIInsight {
  type: 'success' | 'warning' | 'info' | 'danger';
  title: string;
  description: string;
  value?: string;
  trend?: 'up' | 'down' | 'stable';
}

interface ScheduledReport {
  id: string;
  name: string;
  type: string;
  frequency: string;
  recipients: string[];
  nextRun: Date;
  lastRun?: Date;
  active: boolean;
}

export default function ReportsPage() {
  // Initialize with null to avoid hydration issues
  const [selectedPeriod, setSelectedPeriod] = useState<{
    start_date: Date | null;
    end_date: Date | null;
  }>({
    start_date: null,
    end_date: null,
  });

  // Set dates on client-side after hydration
  useEffect(() => {
    const now = new Date();
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    setSelectedPeriod({
      start_date: startOfMonth,
      end_date: now,
    });
  }, []);
  
  const [reportType, setReportType] = useState<string>('profit_loss');
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [isScheduleDialogOpen, setIsScheduleDialogOpen] = useState(false);
  const [scheduleName, setScheduleName] = useState('');
  const [scheduleFrequency, setScheduleFrequency] = useState('monthly');
  const [scheduleRecipients, setScheduleRecipients] = useState('');
  const [exportFormat, setExportFormat] = useState<'pdf' | 'excel'>('pdf');
  // AI Insights query
  const { data: aiInsightsData } = useQuery({
    queryKey: ['ai-insights', selectedPeriod],
    queryFn: () => {
      if (!selectedPeriod.start_date || !selectedPeriod.end_date) return null;
      return reportsService.getAIInsights({
        start_date: selectedPeriod.start_date,
        end_date: selectedPeriod.end_date
      });
    },
    enabled: !!selectedPeriod.start_date && !!selectedPeriod.end_date,
  });

  // Queries
  const { data: reports, isLoading, error } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportsService.getReports(),
  });

  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => bankingService.getAccounts(),
  });

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesService.getCategories(),
  });

  const { data: cashFlowData } = useQuery({
    queryKey: ['cash-flow', selectedPeriod],
    queryFn: () => {
      if (!selectedPeriod.start_date || !selectedPeriod.end_date) return null;
      return reportsService.getCashFlowData({
        start_date: selectedPeriod.start_date,
        end_date: selectedPeriod.end_date
      });
    },
    enabled: !!selectedPeriod.start_date && !!selectedPeriod.end_date,
  });

  const { data: categorySpending } = useQuery({
    queryKey: ['category-spending', selectedPeriod],
    queryFn: () => {
      if (!selectedPeriod.start_date || !selectedPeriod.end_date) return null;
      return reportsService.getCategorySpending({
        start_date: selectedPeriod.start_date,
        end_date: selectedPeriod.end_date
      });
    },
    enabled: !!selectedPeriod.start_date && !!selectedPeriod.end_date,
  });

  const { data: incomeVsExpenses } = useQuery({
    queryKey: ['income-vs-expenses', selectedPeriod],
    queryFn: () => {
      if (!selectedPeriod.start_date || !selectedPeriod.end_date) return null;
      return reportsService.getIncomeVsExpenses({
        start_date: selectedPeriod.start_date,
        end_date: selectedPeriod.end_date
      });
    },
    enabled: !!selectedPeriod.start_date && !!selectedPeriod.end_date,
  });

  // Scheduled reports query
  const { data: scheduledReports, refetch: refetchScheduledReports } = useQuery({
    queryKey: ['scheduledReports'],
    queryFn: () => reportsService.getScheduledReports(),
  });

  // Create scheduled report mutation
  const createScheduledReportMutation = useMutation({
    mutationFn: (data: any) => reportsService.createScheduledReport(data),
    onSuccess: () => {
      refetchScheduledReports();
      toast.success('Agendamento criado com sucesso');
    },
    onError: (error: any) => {
      console.error('Erro ao criar agendamento:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          JSON.stringify(error.response?.data) || 
                          'Falha ao criar agendamento';
      toast.error(errorMessage);
    },
  });

  // Toggle scheduled report mutation
  const toggleScheduledReportMutation = useMutation({
    mutationFn: (id: string) => reportsService.toggleScheduledReport(id),
    onSuccess: () => {
      refetchScheduledReports();
      toast.success('Status do agendamento alterado');
    },
    onError: (error: any) => {
      toast.error('Falha ao alterar status');
    },
  });

  // Delete scheduled report mutation
  const deleteScheduledReportMutation = useMutation({
    mutationFn: (id: string) => reportsService.deleteScheduledReport(id),
    onSuccess: () => {
      refetchScheduledReports();
      toast.success('Agendamento removido');
    },
    onError: (error: any) => {
      toast.error('Falha ao remover agendamento');
    },
  });


  // Mutations
  const generateReportMutation = useMutation({
    mutationFn: (params: { type: string; parameters: ReportParameters; format: 'pdf' | 'excel' }) =>
      reportsService.generateReport(params.type, params.parameters),
    onSuccess: (data) => {
      toast.success('Relatório gerado com sucesso');
      if (data.file_url && typeof window !== 'undefined') {
        window.open(data.file_url, '_blank');
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Falha ao gerar relatório');
    },
  });

  const downloadReportMutation = useMutation({
    mutationFn: (reportId: string) => reportsService.downloadReport(reportId),
    onSuccess: (data, reportId) => {
      if (typeof window !== 'undefined') {
        const url = window.URL.createObjectURL(new Blob([data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `report_${reportId}_${new Date().toISOString()}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      }
    },
    onError: (error: any) => {
      toast.error('Falha ao baixar relatório');
    },
  });

  // Handlers
  const handleQuickPeriod = (periodId: string) => {
    const now = new Date();
    let start: Date;
    let end: Date = now;
    
    switch (periodId) {
      case 'current_month':
        start = new Date(now.getFullYear(), now.getMonth(), 1);
        break;
      case 'last_month':
        start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        end = new Date(now.getFullYear(), now.getMonth(), 0);
        break;
      case 'quarter':
        const quarter = Math.floor(now.getMonth() / 3);
        start = new Date(now.getFullYear(), quarter * 3, 1);
        break;
      case 'year':
        start = new Date(now.getFullYear(), 0, 1);
        break;
      default:
        start = new Date(now.getFullYear(), now.getMonth(), 1);
    }
    
    setSelectedPeriod({ start_date: start, end_date: end });
  };

  const handleGenerateReport = () => {
    if (!selectedPeriod.start_date || !selectedPeriod.end_date) return;
    
    const parameters: ReportParameters = {
      start_date: selectedPeriod.start_date.toISOString().split('T')[0],
      end_date: selectedPeriod.end_date.toISOString().split('T')[0],
      account_ids: selectedAccounts,
      category_ids: selectedCategories,
    };

    generateReportMutation.mutate({ type: reportType, parameters, format: exportFormat });
  };

  const handleScheduleReport = () => {
    if (!scheduleName || !scheduleRecipients) {
      toast.error('Nome e destinatários são obrigatórios');
      return;
    }

    const scheduleData = {
      name: scheduleName,
      report_type: reportType,
      frequency: scheduleFrequency,
      email_recipients: scheduleRecipients.split(',').map(email => email.trim()),
      file_format: exportFormat,
      parameters: {
        start_date: selectedPeriod.start_date?.toISOString().split('T')[0],
        end_date: selectedPeriod.end_date?.toISOString().split('T')[0],
        account_ids: selectedAccounts,
        category_ids: selectedCategories,
      }
    };

    console.log('Sending schedule data:', scheduleData);
    createScheduledReportMutation.mutate(scheduleData);
    setIsScheduleDialogOpen(false);
    setScheduleName('');
    setScheduleRecipients('');
  };

  const getInsightIcon = (type: AIInsight['type']) => {
    switch (type) {
      case 'success':
        return CheckCircleIcon;
      case 'warning':
        return ExclamationTriangleIcon;
      case 'info':
        return LightBulbIcon;
      case 'danger':
        return ExclamationTriangleIcon;
    }
  };

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
          <h1 className="text-3xl font-bold">Relatórios</h1>
          <p className="text-gray-600">Análises completas e insights sobre suas finanças</p>
        </div>
      </div>

      {/* Quick Reports */}
      <Card>
        <CardHeader>
          <CardTitle>Relatórios Rápidos</CardTitle>
          <CardDescription>Gere relatórios instantâneos para períodos comuns</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            {QUICK_PERIODS.map((period) => {
              const Icon = period.icon;
              return (
                <Button
                  key={period.id}
                  variant="outline"
                  className="justify-start h-auto p-4"
                  onClick={() => {
                    handleQuickPeriod(period.id);
                    toast.success(`Período selecionado: ${period.label}`);
                  }}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  <div className="text-left">
                    <div className="font-medium">{period.label}</div>
                    <div className="text-xs text-gray-500">Clique para visualizar</div>
                  </div>
                </Button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs defaultValue="visualizations" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="visualizations">Visualizações</TabsTrigger>
          <TabsTrigger value="custom">Relatórios Personalizados</TabsTrigger>
          <TabsTrigger value="scheduled">Agendados</TabsTrigger>
          <TabsTrigger value="insights">Insights com IA</TabsTrigger>
        </TabsList>

        {/* Visualizations Tab */}
        <TabsContent value="visualizations" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Cash Flow Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BanknotesIcon className="h-5 w-5 mr-2" />
                  Fluxo de Caixa
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  {cashFlowData && (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={cashFlowData}>
                        <defs>
                          <linearGradient id="colorIncome" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#22c55e" stopOpacity={0.8}/>
                            <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
                          </linearGradient>
                          <linearGradient id="colorExpenses" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                            <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip formatter={(value) => formatCurrency(value as number)} />
                        <Legend />
                        <Area
                          type="monotone"
                          dataKey="income"
                          stroke="#22c55e"
                          fillOpacity={1}
                          fill="url(#colorIncome)"
                          name="Receitas"
                        />
                        <Area
                          type="monotone"
                          dataKey="expenses"
                          stroke="#ef4444"
                          fillOpacity={1}
                          fill="url(#colorExpenses)"
                          name="Despesas"
                        />
                        <Line
                          type="monotone"
                          dataKey="balance"
                          stroke="#3b82f6"
                          strokeWidth={3}
                          name="Saldo"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Category Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <ChartPieIcon className="h-5 w-5 mr-2" />
                  Distribuição por Categoria
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  {categorySpending && (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={categorySpending}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ category, percentage }) => `${category.name} (${percentage}%)`}
                          outerRadius={100}
                          fill="#8884d8"
                          dataKey="amount"
                        >
                          {categorySpending.map((entry, index) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={CHART_COLORS[index % CHART_COLORS.length]}
                            />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => formatCurrency(value as number)} />
                      </PieChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Income vs Expenses Comparison */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <ChartBarIcon className="h-5 w-5 mr-2" />
                  Comparativo: Receitas vs Despesas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  {incomeVsExpenses && (
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={incomeVsExpenses}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip formatter={(value) => formatCurrency(value as number)} />
                        <Legend />
                        <Bar dataKey="income" fill="#22c55e" name="Receitas" />
                        <Bar dataKey="expenses" fill="#ef4444" name="Despesas" />
                        <Line 
                          type="monotone" 
                          dataKey="profit" 
                          stroke="#3b82f6" 
                          strokeWidth={3}
                          name="Lucro/Prejuízo"
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Custom Reports Tab */}
        <TabsContent value="custom" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Gerador de Relatórios Personalizados</CardTitle>
              <CardDescription>Configure e gere relatórios detalhados com filtros avançados</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Report Type Selection */}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                  {REPORT_TYPES.map((type) => {
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
                      >
                        <Icon className="h-8 w-8 mb-2 text-primary" />
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
                      date={selectedPeriod.start_date || undefined}
                      onDateChange={(date) =>
                        setSelectedPeriod({ ...selectedPeriod, start_date: date || new Date() })
                      }
                    />
                  </div>
                  <div>
                    <Label>Período Final</Label>
                    <DatePicker
                      date={selectedPeriod.end_date || undefined}
                      onDateChange={(date) =>
                        setSelectedPeriod({ ...selectedPeriod, end_date: date || new Date() })
                      }
                    />
                  </div>
                  <div>
                    <Label>Formato de Exportação</Label>
                    <Select value={exportFormat} onValueChange={(value: 'pdf' | 'excel') => setExportFormat(value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pdf">PDF</SelectItem>
                        <SelectItem value="excel">Excel</SelectItem>
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
                      <SelectTrigger>
                        <SelectValue placeholder="Todas as contas" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todas as contas</SelectItem>
                        {(accounts as any)?.results?.map((account: Account) => (
                          <SelectItem key={account.id} value={account.id}>
                            {account.name}
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
                      <SelectTrigger>
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
                    className="flex-1"
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
                  <Button
                    variant="outline"
                    onClick={() => setIsScheduleDialogOpen(true)}
                  >
                    <ClockIcon className="h-4 w-4 mr-2" />
                    Agendar
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recent Reports */}
          <Card>
            <CardHeader>
              <CardTitle>Relatórios Recentes</CardTitle>
            </CardHeader>
            <CardContent>
              {reports?.results && reports.results.length > 0 ? (
                <div className="space-y-4">
                  {reports.results.map((report) => (
                    <div
                      key={report.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center space-x-4">
                        <div className="p-2 bg-primary/10 rounded-lg">
                          <DocumentChartBarIcon className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <h3 className="font-medium">{report.name}</h3>
                          <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <span className="flex items-center">
                              <CalendarIcon className="h-4 w-4 mr-1" />
                              {report.frequency}
                            </span>
                            {report.last_generated && (
                              <span className="flex items-center">
                                <ClockIcon className="h-4 w-4 mr-1" />
                                Gerado {formatDate(report.last_generated)}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => downloadReportMutation.mutate(report.id)}
                          disabled={downloadReportMutation.isPending}
                        >
                          <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                          Baixar
                        </Button>
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

        {/* Scheduled Reports Tab */}
        <TabsContent value="scheduled" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Relatórios Agendados</CardTitle>
              <CardDescription>Gerencie relatórios automáticos recorrentes</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {scheduledReports?.results?.map((schedule: any) => (
                  <div
                    key={schedule.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex items-center space-x-4">
                      <div className="p-2 bg-primary/10 rounded-lg">
                        <ClockIcon className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-medium">{schedule.name || `${schedule.report_type} Report`}</h3>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <span>{FREQUENCIES.find(f => f.value === schedule.frequency)?.label}</span>
                          <span className="flex items-center">
                            <EnvelopeIcon className="h-4 w-4 mr-1" />
                            {schedule.email_recipients?.join(', ')}
                          </span>
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          Próxima execução: {schedule.next_run_at ? formatDate(schedule.next_run_at) : 'Não definido'}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <Switch
                        checked={schedule.is_active}
                        onCheckedChange={() => {
                          toggleScheduledReportMutation.mutate(schedule.id);
                        }}
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          deleteScheduledReportMutation.mutate(schedule.id);
                        }}
                      >
                        Remover
                      </Button>
                    </div>
                  </div>
                ))}
                
                {(!scheduledReports?.results || scheduledReports.results.length === 0) && (
                  <EmptyState
                    icon={ClockIcon}
                    title="Nenhum relatório agendado"
                    description="Agende relatórios para receber análises automáticas"
                    action={{
                      label: 'Criar Agendamento',
                      onClick: () => setIsScheduleDialogOpen(true)
                    }}
                  />
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI Insights Tab */}
        <TabsContent value="insights" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <SparklesIcon className="h-5 w-5 mr-2" />
                Análise com Inteligência Artificial
              </CardTitle>
              <CardDescription>
                Insights automáticos e previsões baseadas em seus dados financeiros
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {aiInsightsData?.insights?.map((insight: any, index: number) => {
                  const Icon = getInsightIcon(insight.type);
                  return (
                    <div
                      key={index}
                      className={cn(
                        "p-4 border rounded-lg",
                        insight.type === 'success' && "border-green-200 bg-green-50",
                        insight.type === 'warning' && "border-yellow-200 bg-yellow-50",
                        insight.type === 'info' && "border-blue-200 bg-blue-50",
                        insight.type === 'danger' && "border-red-200 bg-red-50"
                      )}
                    >
                      <div className="flex items-start space-x-3">
                        <Icon className={cn(
                          "h-5 w-5 mt-0.5",
                          insight.type === 'success' && "text-green-600",
                          insight.type === 'warning' && "text-yellow-600",
                          insight.type === 'info' && "text-blue-600",
                          insight.type === 'danger' && "text-red-600"
                        )} />
                        <div className="flex-1">
                          <h4 className="font-medium flex items-center">
                            {insight.title}
                            {insight.trend && (
                              <>
                                {insight.trend === 'up' && <ArrowTrendingUpIcon className="h-4 w-4 ml-2 text-green-600" />}
                                {insight.trend === 'down' && <ArrowTrendingDownIcon className="h-4 w-4 ml-2 text-red-600" />}
                              </>
                            )}
                          </h4>
                          <p className="text-sm text-gray-600 mt-1">{insight.description}</p>
                          {insight.value && (
                            <div className="mt-2 text-2xl font-bold">
                              {insight.value}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
                
                {/* Predictions Section */}
                {aiInsightsData?.predictions && (
                  <div className="mt-6 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
                    <h4 className="font-medium flex items-center mb-3">
                      <TrendingUpIcon className="h-5 w-5 mr-2 text-purple-600" />
                      Previsões para o Próximo Mês
                    </h4>
                    <div className="grid gap-3 md:grid-cols-3">
                      <div className="bg-white p-3 rounded-lg">
                        <div className="text-sm text-gray-600">Receita Prevista</div>
                        <div className="text-xl font-bold text-green-600">
                          {formatCurrency(aiInsightsData.predictions.next_month_income)}
                        </div>
                      </div>
                      <div className="bg-white p-3 rounded-lg">
                        <div className="text-sm text-gray-600">Despesas Previstas</div>
                        <div className="text-xl font-bold text-red-600">
                          {formatCurrency(aiInsightsData.predictions.next_month_expenses)}
                        </div>
                      </div>
                      <div className="bg-white p-3 rounded-lg">
                        <div className="text-sm text-gray-600">Economia Estimada</div>
                        <div className="text-xl font-bold text-blue-600">
                          {formatCurrency(aiInsightsData.predictions.projected_savings)}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {aiInsightsData?.recommendations && aiInsightsData.recommendations.length > 0 && (
                  <div className="mt-6">
                    <h4 className="font-medium mb-3">Recomendações Personalizadas</h4>
                    <div className="space-y-2">
                      {aiInsightsData.recommendations.map((rec: any, index: number) => (
                        <div key={index} className="flex items-start space-x-2">
                          <CheckCircleIcon className="h-5 w-5 text-green-600 mt-0.5" />
                          <div>
                            <p className="text-sm font-medium">{rec.title}</p>
                            <p className="text-sm text-gray-600">{rec.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Loading/Empty State */}
                {!aiInsightsData?.insights && (
                  <div className="text-center py-8">
                    <SparklesIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                    <p className="text-gray-500">Selecione um período para ver insights com IA</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Schedule Dialog */}
      <Dialog open={isScheduleDialogOpen} onOpenChange={setIsScheduleDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Agendar Relatório</DialogTitle>
            <DialogDescription>
              Configure um relatório para ser gerado e enviado automaticamente
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Nome do Agendamento</Label>
              <Input
                value={scheduleName}
                onChange={(e) => setScheduleName(e.target.value)}
                placeholder="Ex: Relatório Mensal de Despesas"
              />
            </div>
            <div>
              <Label>Frequência</Label>
              <Select value={scheduleFrequency} onValueChange={setScheduleFrequency}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {FREQUENCIES.map((freq) => (
                    <SelectItem key={freq.value} value={freq.value}>
                      {freq.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Destinatários (emails separados por vírgula)</Label>
              <Input
                value={scheduleRecipients}
                onChange={(e) => setScheduleRecipients(e.target.value)}
                placeholder="email1@example.com, email2@example.com"
              />
            </div>
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setIsScheduleDialogOpen(false)}>
                Cancelar
              </Button>
              <Button onClick={handleScheduleReport}>
                Criar Agendamento
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}