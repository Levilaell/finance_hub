'use client';

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { EmptyState } from '@/components/ui/empty-state';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { reportsService } from '@/services/reports.service';
import { aiAnalysisService } from '@/services/ai-analysis.service';
import { Report, ReportParameters, Account, Category, AIInsights, BankAccount } from '@/types';
import { formatCurrency, formatDate, cn } from '@/lib/utils';
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

const QUICK_PERIODS = [
  { id: 'current_month', label: 'Mês Atual', icon: CalendarIcon },
  { id: 'last_month', label: 'Mês Anterior', icon: CalendarIcon },
  { id: 'quarterly', label: 'Trimestre', icon: ChartBarIcon },
  { id: 'year_to_date', label: 'Ano Atual', icon: TrendingUpIcon },
];

const CHART_COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658'];

// AI Analyses Tab Component
function AIAnalysesTab() {
  const [selectedAnalysisType, setSelectedAnalysisType] = useState<string>('all');
  const [showFavorites, setShowFavorites] = useState(false);

  // Query for AI analyses
  const { 
    data: aiAnalyses, 
    isLoading: aiAnalysesLoading, 
    error: aiAnalysesError,
    refetch: refetchAnalyses
  } = useQuery({
    queryKey: ['ai-analyses', selectedAnalysisType, showFavorites],
    queryFn: async () => {
      const params: any = {};
      if (selectedAnalysisType !== 'all') {
        params.analysis_type = selectedAnalysisType;
      }
      if (showFavorites) {
        return await aiAnalysisService.getFavorites();
      }
      const result = await aiAnalysisService.list(params);
      return result.results || result;
    }
  });

  // Toggle favorite mutation
  const toggleFavoriteMutation = useMutation({
    mutationFn: (id: number) => aiAnalysisService.toggleFavorite(id),
    onSuccess: () => {
      refetchAnalyses();
      toast.success('Favorito atualizado!');
    },
    onError: () => {
      toast.error('Erro ao atualizar favorito');
    }
  });

  const analysisTypes = [
    { value: 'all', label: 'Todas as Análises' },
    { value: 'financial_health', label: 'Saúde Financeira' },
    { value: 'cash_flow_prediction', label: 'Previsão de Fluxo de Caixa' },
    { value: 'expense_optimization', label: 'Otimização de Gastos' },
    { value: 'revenue_analysis', label: 'Análise de Receita' },
    { value: 'general_insights', label: 'Insights Gerais' },
  ];

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <SparklesIcon className="h-5 w-5 mr-2" />
            Análises de IA Salvas
          </CardTitle>
          <CardDescription>
            Acesse suas análises de IA geradas anteriormente
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-6">
            <div className="flex-1">
              <Label>Tipo de Análise</Label>
              <Select value={selectedAnalysisType} onValueChange={setSelectedAnalysisType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {analysisTypes.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button
                variant={showFavorites ? "default" : "outline"}
                onClick={() => setShowFavorites(!showFavorites)}
                className="flex items-center"
              >
                <CheckCircleIcon className="h-4 w-4 mr-2" />
                {showFavorites ? 'Todos' : 'Favoritos'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Suas Análises</CardTitle>
        </CardHeader>
        <CardContent>
          {aiAnalysesLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : aiAnalysesError ? (
            <ErrorMessage 
              title="Erro ao carregar análises"
              message="Tente novamente mais tarde"
            />
          ) : aiAnalyses && aiAnalyses.length > 0 ? (
            <div className="space-y-4">
              {aiAnalyses.map((analysis: any) => (
                <div
                  key={analysis.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center space-x-4 flex-1">
                    <div className="p-2 bg-purple-100 rounded-lg">
                      <SparklesIcon className="h-5 w-5 text-purple-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium">{analysis.title}</h3>
                        {analysis.is_favorite && (
                          <CheckCircleIcon className="h-4 w-4 text-yellow-500" />
                        )}
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <span className="flex items-center">
                          <CalendarIcon className="h-4 w-4 mr-1" />
                          {formatDate(analysis.period_start)} - {formatDate(analysis.period_end)}
                        </span>
                        <span className="flex items-center">
                          <ClockIcon className="h-4 w-4 mr-1" />
                          {analysis.days_since_created === 0 ? 'Hoje' : 
                           analysis.days_since_created === 1 ? 'Ontem' :
                           `${analysis.days_since_created} dias atrás`}
                        </span>
                        <span className="px-2 py-1 bg-gray-100 rounded text-xs">
                          {analysis.analysis_type_display}
                        </span>
                        {analysis.confidence_score && (
                          <span className="flex items-center text-green-600">
                            <LightBulbIcon className="h-4 w-4 mr-1" />
                            {analysis.confidence_score}% confiança
                          </span>
                        )}
                      </div>
                      {analysis.summary_text && (
                        <p className="text-sm text-gray-600 mt-1">{analysis.summary_text}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => toggleFavoriteMutation.mutate(analysis.id)}
                      disabled={toggleFavoriteMutation.isPending}
                    >
                      <CheckCircleIcon className={cn(
                        "h-4 w-4 mr-1",
                        analysis.is_favorite ? "text-yellow-500" : "text-gray-400"
                      )} />
                      {analysis.is_favorite ? 'Favoritado' : 'Favoritar'}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => window.open(`/ai-insights?period_start=${analysis.period_start}&period_end=${analysis.period_end}`, '_blank')}
                    >
                      <SparklesIcon className="h-4 w-4 mr-1" />
                      Ver Análise
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={SparklesIcon}
              title="Nenhuma análise salva"
              description={showFavorites ? 
                "Você ainda não tem análises favoritas. Marque suas análises como favoritas para vê-las aqui." :
                "Suas análises de IA aparecerão aqui automaticamente. Gere sua primeira análise na aba 'Insights com IA'."
              }
            />
          )}
        </CardContent>
      </Card>
    </>
  );
}

// Types
interface ReportData {
  id: string;
  title: string;
  report_type: string;
  period_start: string;
  period_end: string;
  file_format: string;
  is_generated: boolean;
  created_at: string;
  created_by_name?: string;
  file?: string;
  file_size?: number;
  generation_time?: number;
  error_message?: string;
}

interface AIInsight {
  type: 'success' | 'warning' | 'info' | 'danger';
  title: string;
  description: string;
  value?: string;
  trend?: 'up' | 'down' | 'stable';
  priority?: 'high' | 'medium' | 'low';
  actionable?: boolean;
  category?: string;
}

// Components - AI components removidos (usar página /ai-insights)






export default function ReportsPage() {
  const queryClient = useQueryClient();
  
  // State
  const [selectedPeriod, setSelectedPeriod] = useState<{
    start_date: Date | null;
    end_date: Date | null;
  }>({
    start_date: null,
    end_date: null,
  });
  
  const [reportType, setReportType] = useState<string>('profit_loss');
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [exportFormat, setExportFormat] = useState<'pdf' | 'xlsx'>('pdf');

  // Set dates on client-side after hydration
  useEffect(() => {
    const now = new Date();
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    setSelectedPeriod({
      start_date: startOfMonth,
      end_date: now,
    });
  }, []);

  // Queries
  const { data: reports, isLoading, error, refetch: refetchReports } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportsService.getReports(),
  });

  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => bankingService.getBankAccounts(),
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

  // AI insights query removida - usar página separada /ai-insights

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
      const report = reports?.results?.find((r: ReportData) => r.id === reportId);
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
  const handleQuickPeriod = useCallback((periodId: string) => {
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
      case 'quarterly':
        const quarter = Math.floor(now.getMonth() / 3);
        start = new Date(now.getFullYear(), quarter * 3, 1);
        break;
      case 'year_to_date':
        start = new Date(now.getFullYear(), 0, 1);
        break;
      default:
        start = new Date(now.getFullYear(), now.getMonth(), 1);
    }
    
    setSelectedPeriod({ start_date: start, end_date: end });
  }, []);

  const handleGenerateReport = useCallback(() => {
    if (!selectedPeriod.start_date || !selectedPeriod.end_date) {
      toast.error('Por favor, selecione um período');
      return;
    }
    
    const parameters: ReportParameters = {
      start_date: selectedPeriod.start_date.toISOString().split('T')[0],
      end_date: selectedPeriod.end_date.toISOString().split('T')[0],
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
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="visualizations">Visualizações</TabsTrigger>
          <TabsTrigger value="custom">Relatórios Personalizados</TabsTrigger>
          <TabsTrigger value="ai-analyses">Análises de IA</TabsTrigger>
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
                          {categorySpending.map((entry: any, index: number) => (
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
                    <Select value={exportFormat} onValueChange={(value: 'pdf' | 'xlsx') => setExportFormat(value)}>
                      <SelectTrigger>
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
                      <SelectTrigger>
                        <SelectValue placeholder="Todas as contas" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todas as contas</SelectItem>
                        {(accounts as any)?.results?.map((account: BankAccount) => (
                          <SelectItem key={account.id} value={account.id}>
                            {account.account_name}
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
                  {reports.results.map((report: ReportData) => (
                    <div
                      key={report.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center space-x-4">
                        <div className="p-2 bg-primary/10 rounded-lg">
                          <DocumentChartBarIcon className="h-5 w-5 text-primary" />
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

        {/* AI Analyses Tab */}
        <TabsContent value="ai-analyses" className="space-y-6">
          <AIAnalysesTab />
        </TabsContent>
        
      </Tabs>
    </div>
  );
}