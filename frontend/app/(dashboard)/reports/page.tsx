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
  ArrowTrendingDownIcon,
  XMarkIcon
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
  { id: 'quarterly', label: 'Trimestre', icon: ChartBarIcon },
  { id: 'year_to_date', label: 'Ano Atual', icon: TrendingUpIcon },
];

const CHART_COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658'];

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

// Components
const AIInsightsErrorBoundary: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    const handleError = () => setHasError(true);
    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);

  if (hasError) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <ExclamationTriangleIcon className="h-12 w-12 mx-auto text-yellow-500 mb-4" />
          <p className="text-gray-600">Erro ao carregar insights. Por favor, tente novamente.</p>
          <Button 
            variant="outline" 
            className="mt-4"
            onClick={() => {
              setHasError(false);
              window.location.reload();
            }}
          >
            Recarregar
          </Button>
        </CardContent>
      </Card>
    );
  }

  return <>{children}</>;
};

const ScoreCard: React.FC<{ 
  title: string; 
  score: number; 
  grade?: string;
  trend?: 'up' | 'down' | 'stable';
}> = ({ title, score, grade, trend }) => {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getGradeColor = (grade: string) => {
    const colors: Record<string, string> = {
      'A': 'bg-green-100 text-green-800',
      'B': 'bg-blue-100 text-blue-800',
      'C': 'bg-yellow-100 text-yellow-800',
      'D': 'bg-orange-100 text-orange-800',
      'F': 'bg-red-100 text-red-800'
    };
    return colors[grade] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="bg-white p-4 rounded-lg border">
      <div className="flex justify-between items-start mb-2">
        <h5 className="text-sm font-medium text-gray-600">{title}</h5>
        {grade && (
          <span className={cn(
            "px-2 py-1 rounded text-xs font-bold",
            getGradeColor(grade)
          )}>
            {grade}
          </span>
        )}
      </div>
      <div className="flex items-baseline space-x-2">
        <span className={cn("text-3xl font-bold", getScoreColor(score))}>
          {score}
        </span>
        <span className="text-sm text-gray-500">/100</span>
        {trend && (
          <div className="ml-auto">
            {trend === 'up' && <ArrowTrendingUpIcon className="h-5 w-5 text-green-500" />}
            {trend === 'down' && <ArrowTrendingDownIcon className="h-5 w-5 text-red-500" />}
            {trend === 'stable' && <span className="text-gray-400">→</span>}
          </div>
        )}
      </div>
      <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div 
          className={cn(
            "h-full transition-all duration-1000 ease-out",
            score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
          )}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
};

const ConfidenceIndicator: React.FC<{ level: 'high' | 'medium' | 'low' }> = ({ level }) => {
  const configs = {
    high: { color: 'text-green-600', bars: 3, label: 'Alta Confiança' },
    medium: { color: 'text-yellow-600', bars: 2, label: 'Confiança Média' },
    low: { color: 'text-red-600', bars: 1, label: 'Baixa Confiança' }
  };

  const config = configs[level];

  return (
    <div className="flex items-center space-x-2 text-sm">
      <div className="flex space-x-1">
        {[1, 2, 3].map((bar) => (
          <div
            key={bar}
            className={cn(
              "w-1 h-3 rounded-full",
              bar <= config.bars ? config.color : 'bg-gray-300'
            )}
          />
        ))}
      </div>
      <span className={cn("text-xs", config.color)}>{config.label}</span>
    </div>
  );
};

const InsightCard: React.FC<{ insight: AIInsight; index: number }> = ({ insight, index }) => {
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

  const Icon = getInsightIcon(insight.type);
  
  return (
    <div
      className={cn(
        "p-4 border rounded-lg transition-all duration-300 animate-in fade-in slide-in-from-bottom-2",
        "hover:shadow-md hover:scale-[1.02]",
        insight.type === 'success' && "border-green-200 bg-green-50",
        insight.type === 'warning' && "border-yellow-200 bg-yellow-50",
        insight.type === 'info' && "border-blue-200 bg-blue-50",
        insight.type === 'danger' && "border-red-200 bg-red-50"
      )}
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <div className="flex items-start space-x-3">
        <div className={cn(
          "p-2 rounded-full",
          insight.type === 'success' && "bg-green-100",
          insight.type === 'warning' && "bg-yellow-100",
          insight.type === 'info' && "bg-blue-100",
          insight.type === 'danger' && "bg-red-100"
        )}>
          <Icon className={cn(
            "h-5 w-5",
            insight.type === 'success' && "text-green-600",
            insight.type === 'warning' && "text-yellow-600",
            insight.type === 'info' && "text-blue-600",
            insight.type === 'danger' && "text-red-600"
          )} />
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <h4 className="font-medium flex items-center">
              {insight.title}
              {insight.trend && (
                <>
                  {insight.trend === 'up' && <ArrowTrendingUpIcon className="h-4 w-4 ml-2 text-green-600" />}
                  {insight.trend === 'down' && <ArrowTrendingDownIcon className="h-4 w-4 ml-2 text-red-600" />}
                </>
              )}
            </h4>
            {insight.priority === 'high' && (
              <span className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded">
                Alta Prioridade
              </span>
            )}
          </div>
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
};

const CategorizedInsights: React.FC<{ insights: AIInsight[] }> = ({ insights }) => {
  const categorized = insights.reduce((acc, insight) => {
    const category = insight.category || 'general';
    if (!acc[category]) acc[category] = [];
    acc[category].push(insight);
    return acc;
  }, {} as Record<string, AIInsight[]>);

  const categoryLabels: Record<string, string> = {
    revenue: 'Receitas',
    expense: 'Despesas',
    cashflow: 'Fluxo de Caixa',
    risk: 'Riscos',
    general: 'Geral'
  };

  return (
    <div className="space-y-6">
      {Object.entries(categorized).map(([category, categoryInsights]) => (
        <div key={category}>
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            {categoryLabels[category] || category}
          </h4>
          <div className="space-y-3">
            {categoryInsights.map((insight, index) => (
              <InsightCard key={index} insight={insight} index={index} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

const ExecutiveSummary: React.FC<{ summary: any }> = ({ summary }) => {
  const statusColors = {
    excellent: 'bg-green-100 text-green-800 border-green-300',
    healthy: 'bg-blue-100 text-blue-800 border-blue-300',
    attention_needed: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    critical: 'bg-red-100 text-red-800 border-red-300'
  };

  return (
    <div className={cn(
      "p-6 rounded-lg border-2 mb-6",
      statusColors[summary.overall_status] || statusColors.healthy
    )}>
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">{summary.status_message}</h3>
          <p className="text-sm opacity-90">{summary.key_message}</p>
        </div>
        <SparklesIcon className="h-6 w-6 opacity-50" />
      </div>
      
      {summary.executive_takeaway && (
        <div className="mt-4 p-3 bg-white/50 rounded text-sm">
          <strong>Resumo Executivo:</strong> {summary.executive_takeaway}
        </div>
      )}
      
      <div className="grid grid-cols-2 gap-4 mt-4">
        {summary.main_opportunity && (
          <div className="text-sm">
            <span className="font-medium">Principal Oportunidade:</span>
            <p className="text-xs mt-1">{summary.main_opportunity}</p>
          </div>
        )}
        {summary.recommended_action && (
          <div className="text-sm">
            <span className="font-medium">Ação Recomendada:</span>
            <p className="text-xs mt-1">{summary.recommended_action}</p>
          </div>
        )}
      </div>
    </div>
  );
};

const ScheduledReportCard = ({ schedule, onToggle, onDelete, onRunNow }: { 
  schedule: any;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
  onRunNow: (id: string) => void;
}) => {
  const getNextRunLabel = (nextRunAt: string) => {
    if (!nextRunAt) return 'Não agendado';
    
    const nextRun = new Date(nextRunAt);
    const now = new Date();
    const diffHours = (nextRun.getTime() - now.getTime()) / (1000 * 60 * 60);
    
    if (diffHours < 0) return 'Atrasado';
    if (diffHours < 24) return `Em ${Math.round(diffHours)} horas`;
    if (diffHours < 168) return `Em ${Math.round(diffHours / 24)} dias`;
    
    return formatDate(nextRunAt);
  };
  
  return (
    <div className="flex items-center justify-between p-4 border rounded-lg hover:shadow-md transition-shadow">
      <div className="flex items-center space-x-4">
        <div className={cn(
          "p-2 rounded-lg",
          schedule.is_active ? "bg-primary/10" : "bg-gray-100"
        )}>
          <ClockIcon className={cn(
            "h-5 w-5",
            schedule.is_active ? "text-primary" : "text-gray-400"
          )} />
        </div>
        <div>
          <h3 className="font-medium flex items-center">
            {schedule.name || `${schedule.report_type} Report`}
            {!schedule.is_active && (
              <span className="ml-2 text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">
                Inativo
              </span>
            )}
          </h3>
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <span>{FREQUENCIES.find(f => f.value === schedule.frequency)?.label}</span>
            <span className="flex items-center">
              <EnvelopeIcon className="h-4 w-4 mr-1" />
              {schedule.email_recipients?.length || 0} destinatário(s)
            </span>
            {schedule.file_format && (
              <span className="uppercase text-xs bg-gray-100 px-2 py-0.5 rounded">
                {schedule.file_format}
              </span>
            )}
          </div>
          <div className="flex items-center space-x-4 text-xs text-gray-500 mt-1">
            <span>Próxima execução: {getNextRunLabel(schedule.next_run_at)}</span>
            {schedule.last_run_at && (
              <span>Última execução: {formatDate(schedule.last_run_at)}</span>
            )}
          </div>
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onRunNow(schedule.id)}
          disabled={!schedule.is_active}
        >
          <PlayIcon className="h-4 w-4" />
        </Button>
        <Switch
          checked={schedule.is_active}
          onCheckedChange={() => onToggle(schedule.id)}
        />
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onDelete(schedule.id)}
        >
          <XMarkIcon className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};

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
  const [isScheduleDialogOpen, setIsScheduleDialogOpen] = useState(false);
  const [scheduleName, setScheduleName] = useState('');
  const [scheduleFrequency, setScheduleFrequency] = useState('monthly');
  const [scheduleRecipients, setScheduleRecipients] = useState('');
  const [exportFormat, setExportFormat] = useState<'pdf' | 'excel'>('pdf');

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

  const { data: scheduledReports, refetch: refetchScheduledReports } = useQuery({
    queryKey: ['scheduledReports'],
    queryFn: () => reportsService.getScheduledReports(),
  });

  const { data: aiInsightsData, isLoading: aiInsightsLoading, error: aiInsightsError } = useQuery({
    queryKey: ['ai-insights', selectedPeriod],
    queryFn: () => {
      if (!selectedPeriod.start_date || !selectedPeriod.end_date) return null;
      return reportsService.getAIInsights({
        start_date: selectedPeriod.start_date,
        end_date: selectedPeriod.end_date
      });
    },
    enabled: !!selectedPeriod.start_date && !!selectedPeriod.end_date,
    retry: 2,
    retryDelay: 1000,
  });

  // Mutations
  const generateReportMutation = useMutation({
    mutationFn: (params: { type: string; parameters: ReportParameters; format: 'pdf' | 'excel' }) =>
      reportsService.generateReport(params.type, params.parameters, params.format),
    onSuccess: (data) => {
      toast.success('Relatório está sendo gerado. Você será notificado quando estiver pronto.');
      refetchReports();
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

  const createScheduledReportMutation = useMutation({
    mutationFn: (data: any) => reportsService.createScheduledReport(data),
    onSuccess: () => {
      refetchScheduledReports();
      toast.success('Agendamento criado com sucesso');
      setIsScheduleDialogOpen(false);
      setScheduleName('');
      setScheduleRecipients('');
    },
    onError: (error: any) => {
      console.error('Erro ao criar agendamento:', error);
      const errorMessage = error.response?.data?.error || 
                          error.response?.data?.detail || 
                          error.response?.data?.message || 
                          'Falha ao criar agendamento';
      toast.error(errorMessage);
    },
  });

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

  const runScheduledReportNowMutation = useMutation({
    mutationFn: (id: string) => reportsService.runScheduledReportNow(id),
    onSuccess: (data) => {
      toast.success(data.message || 'Relatório sendo gerado');
      refetchReports();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Falha ao executar relatório');
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
      account_ids: selectedAccounts,
      category_ids: selectedCategories,
      title: `${REPORT_TYPES.find(t => t.value === reportType)?.label} - ${formatDate(selectedPeriod.start_date)} a ${formatDate(selectedPeriod.end_date)}`,
      file_format: exportFormat,
    };

    generateReportMutation.mutate({ 
      type: reportType, 
      parameters, 
      format: exportFormat 
    });
  }, [selectedPeriod, selectedAccounts, selectedCategories, reportType, exportFormat, generateReportMutation]);

  const handleScheduleReport = useCallback(() => {
    // Validações
    if (!scheduleName.trim()) {
      toast.error('Por favor, insira um nome para o agendamento');
      return;
    }
    
    if (!scheduleRecipients.trim()) {
      toast.error('Por favor, insira pelo menos um email de destinatário');
      return;
    }
    
    // Validar emails
    const emails = scheduleRecipients.split(',').map(email => email.trim());
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const invalidEmails = emails.filter(email => !emailRegex.test(email));
    
    if (invalidEmails.length > 0) {
      toast.error(`Emails inválidos: ${invalidEmails.join(', ')}`);
      return;
    }

    const scheduleData = {
      name: scheduleName.trim(),
      report_type: reportType,
      frequency: scheduleFrequency,
      email_recipients: emails,
      file_format: exportFormat,
      send_email: true,
      parameters: {
        account_ids: selectedAccounts,
        category_ids: selectedCategories,
      },
      filters: {}
    };

    createScheduledReportMutation.mutate(scheduleData);
  }, [scheduleName, scheduleRecipients, reportType, scheduleFrequency, exportFormat, selectedAccounts, selectedCategories, createScheduledReportMutation]);

  const handleRunScheduledReport = useCallback((scheduleId: string) => {
    if (confirm('Deseja executar este relatório agora?')) {
      runScheduledReportNowMutation.mutate(scheduleId);
    }
  }, [runScheduledReportNowMutation]);

  const handleDeleteScheduledReport = useCallback((scheduleId: string) => {
    if (confirm('Tem certeza que deseja remover este agendamento?')) {
      deleteScheduledReportMutation.mutate(scheduleId);
    }
  }, [deleteScheduledReportMutation]);

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
                  <ScheduledReportCard
                    key={schedule.id}
                    schedule={schedule}
                    onToggle={toggleScheduledReportMutation.mutate}
                    onDelete={handleDeleteScheduledReport}
                    onRunNow={handleRunScheduledReport}
                  />
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
          <AIInsightsErrorBoundary>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center">
                    <SparklesIcon className="h-5 w-5 mr-2" />
                    Análise com Inteligência Artificial
                  </div>
                  {aiInsightsData?.predictions?.confidence && (
                    <ConfidenceIndicator level={aiInsightsData.predictions.confidence} />
                  )}
                </CardTitle>
                <CardDescription>
                  Insights automáticos e previsões baseadas em seus dados financeiros
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Executive Summary */}
                  {aiInsightsData?.summary && (
                    <ExecutiveSummary summary={aiInsightsData.summary} />
                  )}

                  {/* Key Metrics */}
                  {aiInsightsData?.key_metrics && (
                    <div className="grid gap-4 md:grid-cols-3 mb-6">
                      <ScoreCard 
                        title="Saúde Financeira" 
                        score={aiInsightsData.key_metrics.health_score}
                        grade={aiInsightsData.key_metrics.overall_grade}
                      />
                      <ScoreCard 
                        title="Eficiência Operacional" 
                        score={aiInsightsData.key_metrics.efficiency_score}
                      />
                      <ScoreCard 
                        title="Potencial de Crescimento" 
                        score={aiInsightsData.key_metrics.growth_potential}
                      />
                    </div>
                  )}

                  {/* Loading State */}
                  {aiInsightsLoading && (
                    <div className="flex flex-col items-center justify-center py-12 space-y-4">
                      <div className="relative">
                        <SparklesIcon className="h-16 w-16 text-purple-600 animate-pulse" />
                        <div className="absolute inset-0 flex items-center justify-center">
                          <LoadingSpinner className="h-8 w-8" />
                        </div>
                      </div>
                      <div className="text-center space-y-2">
                        <p className="text-lg font-medium text-gray-900">Analisando seus dados com IA...</p>
                        <p className="text-sm text-gray-600">Isso pode levar alguns segundos</p>
                        <div className="flex items-center justify-center space-x-2 text-xs text-gray-500">
                          <div className="flex space-x-1">
                            <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                            <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                            <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                          </div>
                          <span>Processando com OpenAI GPT</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Error State */}
                  {aiInsightsError && (
                    <div className="text-center py-8">
                      <ExclamationTriangleIcon className="h-12 w-12 mx-auto text-yellow-500 mb-4" />
                      <p className="text-gray-600">Erro ao carregar insights. Usando análise offline.</p>
                    </div>
                  )}

                  {/* Categorized Insights */}
                  {aiInsightsData?.insights && aiInsightsData.insights.length > 0 && (
                    <CategorizedInsights insights={aiInsightsData.insights} />
                  )}
                  
                  {/* Predictions Section */}
                  {aiInsightsData?.predictions && (
                    <div className="mt-6 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200 animate-in fade-in slide-in-from-bottom-3">
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
                      
                      {/* Opportunities & Threats */}
                      <div className="grid gap-4 md:grid-cols-2 mt-4">
                        {aiInsightsData.predictions.opportunities && aiInsightsData.predictions.opportunities.length > 0 && (
                          <div>
                            <h5 className="text-sm font-medium mb-2">Oportunidades</h5>
                            <ul className="space-y-1">
                              {aiInsightsData.predictions.opportunities.map((opp: string, idx: number) => (
                                <li key={idx} className="text-sm flex items-start">
                                  <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1 flex-shrink-0 mt-0.5" />
                                  {opp}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {aiInsightsData.predictions.threats && aiInsightsData.predictions.threats.length > 0 && (
                          <div>
                            <h5 className="text-sm font-medium mb-2">Ameaças</h5>
                            <ul className="space-y-1">
                              {aiInsightsData.predictions.threats.map((threat: string, idx: number) => (
                                <li key={idx} className="text-sm flex items-start">
                                  <ExclamationTriangleIcon className="h-4 w-4 text-red-500 mr-1 flex-shrink-0 mt-0.5" />
                                  {threat}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Recommendations */}
                  {aiInsightsData?.recommendations && aiInsightsData.recommendations.length > 0 && (
                    <div className="mt-6 animate-in fade-in slide-in-from-bottom-4">
                      <h4 className="font-medium mb-3">Recomendações Personalizadas</h4>
                      <div className="space-y-3">
                        {aiInsightsData.recommendations.map((rec: any, index: number) => (
                          <div 
                            key={index} 
                            className="p-4 border rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                            style={{ animationDelay: `${index * 100 + 400}ms` }}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center">
                                  <CheckCircleIcon className="h-5 w-5 text-green-600 mr-2 flex-shrink-0" />
                                  <h5 className="font-medium">{rec.title}</h5>
                                  {rec.priority === 'high' && (
                                    <span className="ml-2 text-xs px-2 py-1 bg-red-100 text-red-700 rounded">
                                      Prioridade Alta
                                    </span>
                                  )}
                                </div>
                                <p className="text-sm text-gray-600 mt-1 ml-7">{rec.description}</p>
                                <div className="flex items-center gap-4 mt-2 ml-7 text-xs text-gray-500">
                                  <span>Impacto: {rec.potential_impact}</span>
                                  <span>Implementação: {rec.time_to_implement === 'imediato' ? 'Imediata' : rec.time_to_implement === 'curto_prazo' ? 'Curto prazo' : 'Médio prazo'}</span>
                                  {rec.difficulty && <span>Dificuldade: {rec.difficulty === 'easy' ? 'Fácil' : rec.difficulty === 'medium' ? 'Média' : 'Difícil'}</span>}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Alerts */}
                  {aiInsightsData?.alerts && aiInsightsData.alerts.length > 0 && (
                    <div className="mt-6">
                      <h4 className="font-medium mb-3 flex items-center">
                        <ExclamationTriangleIcon className="h-5 w-5 mr-2 text-yellow-600" />
                        Alertas Importantes
                      </h4>
                      <div className="space-y-2">
                        {aiInsightsData.alerts.map((alert: any, index: number) => (
                          <div 
                            key={index}
                            className={cn(
                              "p-3 rounded-lg border",
                              alert.severity === 'high' && "bg-red-50 border-red-200",
                              alert.severity === 'medium' && "bg-yellow-50 border-yellow-200",
                              alert.severity === 'low' && "bg-blue-50 border-blue-200"
                            )}
                          >
                            <div className="flex items-start">
                              <ExclamationTriangleIcon className={cn(
                                "h-5 w-5 mr-2 flex-shrink-0",
                                alert.severity === 'high' && "text-red-600",
                                alert.severity === 'medium' && "text-yellow-600",
                                alert.severity === 'low' && "text-blue-600"
                              )} />
                              <div className="flex-1">
                                <h5 className="font-medium">{alert.title}</h5>
                                <p className="text-sm mt-1">{alert.description}</p>
                                {alert.action_required && (
                                  <p className="text-sm font-medium mt-2">
                                    Ação necessária: {alert.action_required}
                                  </p>
                                )}
                                {alert.urgency && (
                                  <span className={cn(
                                    "text-xs mt-2 inline-block px-2 py-1 rounded",
                                    alert.urgency === 'immediate' && "bg-red-100 text-red-700",
                                    alert.urgency === 'urgent' && "bg-orange-100 text-orange-700",
                                    alert.urgency === 'soon' && "bg-yellow-100 text-yellow-700",
                                    alert.urgency === 'monitor' && "bg-blue-100 text-blue-700"
                                  )}>
                                    {alert.urgency === 'immediate' ? 'Imediato' : 
                                     alert.urgency === 'urgent' ? 'Urgente' :
                                     alert.urgency === 'soon' ? 'Em breve' : 'Monitorar'}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Empty State - No Period Selected */}
                  {!aiInsightsData && !aiInsightsLoading && (!selectedPeriod.start_date || !selectedPeriod.end_date) && (
                    <div className="text-center py-8">
                      <SparklesIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                      <p className="text-gray-500">Selecione um período para ver insights com IA</p>
                    </div>
                  )}

                  {/* AI Badge */}
                  {aiInsightsData && (
                    <div className="mt-8 flex items-center justify-center">
                      <div className="inline-flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-purple-100 to-pink-100 rounded-full text-sm">
                        <SparklesIcon className="h-4 w-4 text-purple-600" />
                        <span className="text-purple-700 font-medium">
                          {aiInsightsData.ai_generated ? 'Powered by OpenAI GPT' : 'Análise Avançada (Modo Offline)'}
                        </span>
                        {aiInsightsData.from_cache && (
                          <span className="text-xs text-purple-600">(Cache)</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </AIInsightsErrorBoundary>
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
              <Label>Tipo de Relatório</Label>
              <Select value={reportType} onValueChange={setReportType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {REPORT_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
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
              <Label>Formato do Arquivo</Label>
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
            <div>
              <Label>Destinatários (emails separados por vírgula)</Label>
              <Input
                value={scheduleRecipients}
                onChange={(e) => setScheduleRecipients(e.target.value)}
                placeholder="email1@example.com, email2@example.com"
              />
            </div>
            <div className="flex justify-end space-x-2 pt-4">
              <Button variant="outline" onClick={() => {
                setIsScheduleDialogOpen(false);
                setScheduleName('');
                setScheduleRecipients('');
              }}>
                Cancelar
              </Button>
              <Button onClick={handleScheduleReport} disabled={createScheduledReportMutation.isPending}>
                {createScheduledReportMutation.isPending ? (
                  <LoadingSpinner />
                ) : (
                  'Criar Agendamento'
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}