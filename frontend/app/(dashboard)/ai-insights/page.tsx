'use client';

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { DatePicker } from '@/components/ui/date-picker';
import { Label } from '@/components/ui/label';
import { reportsService } from '@/services/reports.service';
import { aiAnalysisService } from '@/services/ai-analysis.service';
import { formatCurrency, formatDate, cn } from '@/lib/utils';
import { useAuthStore } from '@/store/auth-store';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorMessage } from '@/components/ui/error-message';
import { 
  SparklesIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  LightBulbIcon,
  CalendarIcon,
  ChartBarIcon,
  BanknotesIcon,
  ArrowPathIcon,
  LockClosedIcon,
  ClockIcon,
  TrashIcon,
  CogIcon,
  BeakerIcon,
  GlobeAltIcon,
} from '@heroicons/react/24/outline';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { EnhancedScenarioSimulator } from '@/components/ai-insights/enhanced-scenario-simulator';
import { MarketBenchmarking } from '@/components/ai-insights/market-benchmarking';
import { ContextInput, BusinessContext } from '@/components/ai-insights/context-input';
import { FeatureShowcase } from '@/components/ai-insights/feature-showcase';
import { ProactiveInsightsSystem } from '@/components/ai-insights/proactive-insights-system';
import { InsightsSharing } from '@/components/ai-insights/insights-sharing';

// Types
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
  const statusColors: Record<string, string> = {
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

const QUICK_PERIODS = [
  { id: 'current_month', label: 'Mês Atual', icon: CalendarIcon },
  { id: 'last_month', label: 'Mês Anterior', icon: CalendarIcon },
  { id: 'quarterly', label: 'Trimestre', icon: ChartBarIcon },
  { id: 'year_to_date', label: 'Ano Atual', icon: ArrowTrendingUpIcon },
  { id: 'last_12_months', label: 'Últimos 12 Meses', icon: ArrowTrendingUpIcon },
  { id: 'all_time', label: 'Todo Período', icon: BanknotesIcon },
];

// Saved AI Analyses Component
function AIAnalysesSection() {
  const [selectedAnalysisType, setSelectedAnalysisType] = useState<string>('all');
  const [showFavorites, setShowFavorites] = useState(false);
  const router = useRouter();

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

  // Delete analysis mutation
  const deleteAnalysisMutation = useMutation({
    mutationFn: (id: number) => aiAnalysisService.delete(id),
    onSuccess: () => {
      refetchAnalyses();
      toast.success('Análise excluída com sucesso!');
    },
    onError: () => {
      toast.error('Erro ao excluir análise');
    }
  });

  // Listen for refetch event
  useEffect(() => {
    const handleRefetch = () => {
      if (refetchAnalyses) {
        refetchAnalyses();
      }
    };
    
    window.addEventListener('refetch-ai-analyses', handleRefetch);
    return () => {
      window.removeEventListener('refetch-ai-analyses', handleRefetch);
    };
  }, [refetchAnalyses]);

  const analysisTypes = [
    { value: 'all', label: 'Todas as Análises' },
    { value: 'financial_health', label: 'Saúde Financeira' },
    { value: 'cash_flow_prediction', label: 'Previsão de Fluxo de Caixa' },
    { value: 'expense_optimization', label: 'Otimização de Gastos' },
    { value: 'revenue_analysis', label: 'Análise de Receita' },
    { value: 'general_insights', label: 'Insights Gerais' },
  ];

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center">
            <SparklesIcon className="h-5 w-5 mr-2" />
            Análises Salvas
          </div>
          <div className="flex gap-2">
            <Select value={selectedAnalysisType} onValueChange={setSelectedAnalysisType}>
              <SelectTrigger className="w-[200px]">
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
            <Button
              variant={showFavorites ? "default" : "outline"}
              onClick={() => setShowFavorites(!showFavorites)}
              size="sm"
            >
              <CheckCircleIcon className="h-4 w-4 mr-1" />
              {showFavorites ? 'Todos' : 'Favoritos'}
            </Button>
          </div>
        </CardTitle>
        <CardDescription>
          Todas as análises de IA são salvas automaticamente e podem ser acessadas aqui
        </CardDescription>
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
          <div className="space-y-3">
            {aiAnalyses.map((analysis: any) => (
              <div
                key={analysis.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
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
                      <p className="text-sm text-gray-600 mt-1 line-clamp-1">{analysis.summary_text}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => toggleFavoriteMutation.mutate(analysis.id)}
                    disabled={toggleFavoriteMutation.isPending}
                    title={analysis.is_favorite ? "Remover dos favoritos" : "Adicionar aos favoritos"}
                  >
                    <CheckCircleIcon className={cn(
                      "h-4 w-4",
                      analysis.is_favorite ? "text-yellow-500" : "text-gray-400"
                    )} />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      // Navegar para a análise específica sem recarregar a página
                      router.push(`/ai-insights/${analysis.id}`);
                    }}
                  >
                    <SparklesIcon className="h-4 w-4 mr-1" />
                    Ver Detalhes
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      if (confirm(`Tem certeza que deseja excluir a análise "${analysis.title}"?`)) {
                        deleteAnalysisMutation.mutate(analysis.id);
                      }
                    }}
                    disabled={deleteAnalysisMutation.isPending}
                    title="Excluir análise"
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={SparklesIcon}
            title="Nenhuma análise encontrada"
            description={showFavorites ? 
              "Você ainda não tem análises favoritas. Marque suas análises como favoritas para vê-las aqui." :
              "Suas análises de IA aparecerão aqui automaticamente após serem geradas."
            }
          />
        )}
      </CardContent>
    </Card>
  );
}

export default function AIInsightsPage() {
  // Hooks
  const { user } = useAuthStore();
  const router = useRouter();
  
  // State
  const [selectedPeriod, setSelectedPeriod] = useState<{
    start_date: Date | null;
    end_date: Date | null;
  }>({
    start_date: null,
    end_date: null,
  });
  const [forceRefresh, setForceRefresh] = useState(false);
  const [isUpgradeRequired, setIsUpgradeRequired] = useState(false);
  const [cachedAIData, setCachedAIData] = useState<any>(null);
  const [shouldFetchAnalysis, setShouldFetchAnalysis] = useState(false);
  const [businessContext, setBusinessContext] = useState<BusinessContext | null>(null);
  const [activeTab, setActiveTab] = useState('insights');
  const [currentStep, setCurrentStep] = useState(1); // Novo estado para steps

  // Set dates on client-side after hydration
  useEffect(() => {
    const now = new Date();
    // Usar últimos 12 meses como padrão para incluir as transações existentes
    const start = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
    setSelectedPeriod({
      start_date: start,
      end_date: now,
    });
  }, []);


  // Query
  const { 
    data: aiInsightsData, 
    isLoading: aiInsightsLoading, 
    error: aiInsightsError,
    refetch: refetchAIInsights,
    dataUpdatedAt
  } = useQuery({
    queryKey: ['ai-insights', selectedPeriod, forceRefresh, businessContext],
    queryFn: async () => {
      if (!selectedPeriod.start_date || !selectedPeriod.end_date) return null;
      const result = await reportsService.getAIInsights({
        start_date: selectedPeriod.start_date,
        end_date: selectedPeriod.end_date,
        force_refresh: forceRefresh,
        context: businessContext
      });
      
      // Reset force refresh after use
      if (forceRefresh) {
        setForceRefresh(false);
      }
      
      // Reset shouldFetchAnalysis after use
      setShouldFetchAnalysis(false);
      
      // Check if result is null (403 error from service)
      if (result === null) {
        setIsUpgradeRequired(true);
        // Retorna os dados em cache se existirem
        return cachedAIData;
      }
      
      setIsUpgradeRequired(false);
      // Salva os dados no cache para uso futuro
      setCachedAIData(result);
      
      // Salva automaticamente a análise se há dados válidos
      if (result && result.insights && !isUpgradeRequired) {
        try {
          await aiAnalysisService.saveFromInsights({
            insights_data: result,
            period_start: selectedPeriod.start_date.toISOString().split('T')[0],
            period_end: selectedPeriod.end_date.toISOString().split('T')[0],
            title: `Análise de IA - ${formatDate(selectedPeriod.start_date)} a ${formatDate(selectedPeriod.end_date)}`
          });
          
          // Dispara evento para atualizar lista de análises salvas
          window.dispatchEvent(new Event('refetch-ai-analyses'));
          
          // Feedback visual opcional
          toast.success('Análise salva automaticamente!');
        } catch (error) {
          // Falha silenciosa - não queremos interromper o fluxo
          console.warn('Falha ao salvar análise automaticamente:', error);
        }
      }
      
      return result;
    },
    enabled: !!selectedPeriod.start_date && !!selectedPeriod.end_date && shouldFetchAnalysis,
    retry: (failureCount, error: any) => {
      // Don't retry on 403 errors
      if (error?.response?.status === 403) return false;
      return failureCount < 2;
    },
    throwOnError: (error: any) => {
      // Don't treat 403 as error for React Query
      if (error?.response?.status === 403) return false;
      return true;
    },
    retryDelay: 1000,
    staleTime: forceRefresh ? 0 : 7 * 24 * 60 * 60 * 1000, // No cache if force refresh
    gcTime: forceRefresh ? 0 : 7 * 24 * 60 * 60 * 1000, // No cache if force refresh
    refetchOnWindowFocus: false, // Não refetch automaticamente
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
      case 'last_12_months':
        start = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
        break;
      case 'all_time':
        start = new Date(2020, 0, 1); // Data muito antiga para pegar tudo
        break;
      default:
        start = new Date(now.getFullYear(), now.getMonth(), 1);
    }
    
    setSelectedPeriod({ start_date: start, end_date: end });
  }, []);

  // Step progression logic
  const canProceedToStep2 = selectedPeriod.start_date && selectedPeriod.end_date;
  const canProceedToStep3 = canProceedToStep2 && aiInsightsData;
  const canProceedToStep4 = canProceedToStep3;

  return (
    <div className="space-y-6">
      {/* Header simplificado */}
      <div className="text-center">
        <h1 className="text-3xl font-bold flex items-center justify-center gap-2 mb-2">
          <SparklesIcon className="h-8 w-8 text-purple-600" />
          Análise Inteligente de Finanças
        </h1>
        <p className="text-lg text-gray-600">
          Transforme seus dados em decisões inteligentes em 3 passos simples
        </p>
      </div>

      {/* Progress Steps */}
      <Card className="bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200">
        <CardContent className="py-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              {/* Step 1 */}
              <div className="flex items-center">
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold",
                  currentStep >= 1 ? "bg-purple-600 text-white" : "bg-gray-200 text-gray-600"
                )}>
                  1
                </div>
                <span className={cn(
                  "ml-2 font-medium",
                  currentStep >= 1 ? "text-purple-600" : "text-gray-500"
                )}>
                  Escolher Período
                </span>
              </div>
              
              <div className="w-12 h-0.5 bg-gray-300"></div>
              
              {/* Step 2 */}
              <div className="flex items-center">
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold",
                  currentStep >= 2 ? "bg-purple-600 text-white" : "bg-gray-200 text-gray-600"
                )}>
                  2
                </div>
                <span className={cn(
                  "ml-2 font-medium",
                  currentStep >= 2 ? "text-purple-600" : "text-gray-500"
                )}>
                  Gerar Análise
                </span>
              </div>
              
              <div className="w-12 h-0.5 bg-gray-300"></div>
              
              {/* Step 3 */}
              <div className="flex items-center">
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold",
                  currentStep >= 3 ? "bg-purple-600 text-white" : "bg-gray-200 text-gray-600"
                )}>
                  3
                </div>
                <span className={cn(
                  "ml-2 font-medium",
                  currentStep >= 3 ? "text-purple-600" : "text-gray-500"
                )}>
                  Explorar Ferramentas
                </span>
              </div>
            </div>
          </div>
          
          <div className="text-center">
            <p className="text-sm text-gray-600">
              {currentStep === 1 && "📅 Primeiro, escolha o período que deseja analisar"}
              {currentStep === 2 && "🚀 Agora vamos gerar sua análise personalizada com IA"}
              {currentStep === 3 && "🎯 Explore as ferramentas avançadas com seus dados"}
            </p>
          </div>
        </CardContent>
      </Card>


      {/* STEP 1: Period Selection */}
      {currentStep === 1 && (
        <Card className="border-2 border-purple-200">
          <CardHeader className="text-center">
            <CardTitle className="text-xl flex items-center justify-center gap-2">
              <CalendarIcon className="h-6 w-6 text-purple-600" />
              Passo 1: Escolha o Período para Análise
            </CardTitle>
            <CardDescription className="text-base">
              Selecione o período que você quer analisar. Recomendamos começar com &quot;Últimos 3 meses&quot;
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Quick period buttons - simplified */}
            <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-6 mb-6">
              {QUICK_PERIODS.slice(0, 6).map((period) => {
                const Icon = period.icon;
                return (
                  <Button
                    key={period.id}
                    variant="outline"
                    className="h-auto p-3 text-center hover:border-purple-400 hover:bg-purple-50"
                    onClick={() => {
                      handleQuickPeriod(period.id);
                      setCurrentStep(2);
                    }}
                  >
                    <div>
                      <Icon className="h-5 w-5 mx-auto mb-1" />
                      <div className="text-xs font-medium">{period.label}</div>
                    </div>
                  </Button>
                );
              })}
            </div>
            
            <div className="text-center text-sm text-gray-500 mb-4">ou escolha datas específicas:</div>
            
            <div className="grid gap-4 md:grid-cols-2 max-w-md mx-auto">
              <div>
                <Label>Data Inicial</Label>
                <DatePicker
                  date={selectedPeriod.start_date || undefined}
                  onDateChange={(date) => {
                    setSelectedPeriod({ ...selectedPeriod, start_date: date || new Date() });
                    if (date && selectedPeriod.end_date) {
                      setCurrentStep(2);
                    }
                  }}
                />
              </div>
              <div>
                <Label>Data Final</Label>
                <DatePicker
                  date={selectedPeriod.end_date || undefined}
                  onDateChange={(date) => {
                    setSelectedPeriod({ ...selectedPeriod, end_date: date || new Date() });
                    if (date && selectedPeriod.start_date) {
                      setCurrentStep(2);
                    }
                  }}
                />
              </div>
            </div>
            
            {canProceedToStep2 && (
              <div className="mt-6 text-center">
                <Button
                  onClick={() => setCurrentStep(2)}
                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold px-8"
                  size="lg"
                >
                  Continuar para Análise <ArrowTrendingUpIcon className="h-5 w-5 ml-2" />
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* STEP 2: Generate Analysis */}
      {currentStep === 2 && (
        <Card className="border-2 border-purple-200">
          <CardHeader className="text-center">
            <CardTitle className="text-xl flex items-center justify-center gap-2">
              <SparklesIcon className="h-6 w-6 text-purple-600" />
              Passo 2: Gerar Análise Inteligente
            </CardTitle>
            <CardDescription className="text-base">
              Período selecionado: {selectedPeriod.start_date && formatDate(selectedPeriod.start_date)} até {selectedPeriod.end_date && formatDate(selectedPeriod.end_date)}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center space-y-4">
              {!aiInsightsData && !aiInsightsLoading && (
                <>
                  <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-6 rounded-lg border border-purple-200">
                    <SparklesIcon className="h-12 w-12 mx-auto text-purple-600 mb-3" />
                    <h3 className="text-lg font-semibold mb-2">Pronto para Análise Inteligente!</h3>
                    <p className="text-gray-600 mb-4">
                      Nossa IA irá analisar suas transações e gerar insights personalizados, 
                      previsões e recomendações específicas para o seu negócio.
                    </p>
                    <div className="flex items-center justify-center space-x-6 text-sm text-gray-600 mb-4">
                      <div className="flex items-center">
                        <CheckCircleIcon className="h-5 w-5 text-green-600 mr-2" />
                        <span>Análise Automática</span>
                      </div>
                      <div className="flex items-center">
                        <CheckCircleIcon className="h-5 w-5 text-green-600 mr-2" />
                        <span>Previsões Futuras</span>
                      </div>
                      <div className="flex items-center">
                        <CheckCircleIcon className="h-5 w-5 text-green-600 mr-2" />
                        <span>Recomendações</span>
                      </div>
                    </div>
                  </div>
                  
                  <Button
                    onClick={() => {
                      setShouldFetchAnalysis(true);
                      setTimeout(() => refetchAIInsights(), 100);
                    }}
                    className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold px-12 py-4 text-lg"
                    size="lg"
                  >
                    <SparklesIcon className="h-6 w-6 mr-3" />
                    Gerar Análise com IA
                  </Button>
                  
                  <div className="flex justify-center">
                    <Button variant="ghost" onClick={() => setCurrentStep(1)} className="text-gray-500">
                      ← Voltar e alterar período
                    </Button>
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* STEP 2 & 3: AI Insights Content */}
      {(currentStep === 2 || currentStep === 3) && (
        <AIInsightsErrorBoundary>
          <Card className={cn(
            "border-2",
            currentStep === 3 ? "border-green-200 bg-green-50/30" : "border-purple-200"
          )}>            
            <CardContent className="py-6">
            <div className="space-y-6">
              {/* Success message when analysis is ready */}
              {aiInsightsData && currentStep === 2 && (
                <>
                  <div className="text-center py-6">
                    <div className="bg-green-100 w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center">
                      <CheckCircleIcon className="h-8 w-8 text-green-600" />
                    </div>
                    <h3 className="text-xl font-bold text-green-800 mb-2">✨ Análise Concluída!</h3>
                    <p className="text-gray-600 mb-4">
                      Sua análise inteligente está pronta. Vamos ver os resultados?
                    </p>
                    <Button
                      onClick={() => setCurrentStep(3)}
                      className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-bold px-8"
                      size="lg"
                    >
                      Ver Resultados <ChartBarIcon className="h-5 w-5 ml-2" />
                    </Button>
                  </div>
                </>
              )}
              
              {/* Show results in step 3 */}
              {aiInsightsData && currentStep === 3 && (
                <>
                  <div className="text-center mb-6">
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">
                      📊 Seus Resultados
                    </h3>
                    <p className="text-gray-600">
                      Período: {selectedPeriod.start_date && formatDate(selectedPeriod.start_date)} até {selectedPeriod.end_date && formatDate(selectedPeriod.end_date)}
                    </p>
                    <div className="flex justify-center gap-4 mt-4">
                      {aiInsightsData && (
                        <InsightsSharing
                          insights={aiInsightsData}
                          onShare={(shareData) => {
                            console.log('Insights shared:', shareData);
                            toast.success('Insights compartilhados com sucesso!');
                          }}
                        />
                      )}
                      <Button
                        variant="outline"
                        onClick={() => {
                          setForceRefresh(true);
                          setShouldFetchAnalysis(true);
                          setCurrentStep(2);
                          setTimeout(() => refetchAIInsights(), 100);
                        }}
                        disabled={aiInsightsLoading}
                      >
                        <ArrowPathIcon className={cn("h-4 w-4 mr-2", aiInsightsLoading && "animate-spin")} />
                        Atualizar Análise
                      </Button>
                    </div>
                  </div>

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
                  
                  {/* Sistema de Insights Proativos */}
                  <ProactiveInsightsSystem
                    financialData={aiInsightsData}
                    businessContext={businessContext}
                    onActionTaken={(insight) => {
                      console.log('Action taken on insight:', insight);
                    }}
                  />
                </>
              )}

              {/* Loading State - only in step 2 */}
              {aiInsightsLoading && currentStep === 2 && (
                <div className="text-center py-12">
                  <div className="relative mb-6">
                    <SparklesIcon className="h-20 w-20 mx-auto text-purple-600 animate-pulse" />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <LoadingSpinner className="h-10 w-10" />
                    </div>
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">🤖 Analisando com IA...</h3>
                  <p className="text-gray-600 mb-4">Nossa inteligência artificial está processando seus dados</p>
                  
                  <div className="max-w-md mx-auto">
                    <div className="flex items-center justify-center space-x-2 text-sm text-gray-500 mb-4">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                      <span>Powered by OpenAI GPT</span>
                    </div>
                    
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
                      <p><strong>Aguarde...</strong> Estamos analisando padrões, gerando previsões e criando recomendações personalizadas para você.</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Upgrade Required Banner - Mostra apenas quando não há dados em cache */}
              {isUpgradeRequired && !aiInsightsLoading && !aiInsightsData && (
                <div className="text-center py-12">
                  <div className="max-w-md mx-auto">
                    <div className="mb-6">
                      <div className="relative">
                        <LockClosedIcon className="h-16 w-16 mx-auto text-gray-400" />
                        <SparklesIcon className="h-8 w-8 absolute bottom-0 right-1/3 text-purple-600" />
                      </div>
                    </div>
                    <h3 className="text-2xl font-bold mb-2 bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                      🚀 Desbloqueie o Poder da IA para Suas Finanças
                    </h3>
                    <p className="text-gray-600 mb-6 text-lg">
                      {user?.company?.subscription_plan?.plan_type === 'starter' 
                        ? 'Transforme sua gestão financeira com insights inteligentes! Upgrade agora para Professional ou Enterprise e tome decisões baseadas em dados com nossa IA avançada.'
                        : 'Ative seu plano premium e descubra oportunidades ocultas nos seus dados financeiros com análises automáticas de IA.'}
                    </p>
                    
                    {/* Plan Comparison */}
                    <div className="bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-200 rounded-xl p-6 mb-6 text-left">
                      <h4 className="font-bold text-lg mb-4 flex items-center">
                        <SparklesIcon className="h-6 w-6 mr-2 text-purple-600" />
                        Recursos Exclusivos de IA que Você Terá:
                      </h4>
                      <ul className="space-y-3 text-sm">
                        <li className="flex items-start">
                          <CheckCircleIcon className="h-5 w-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
                          <div>
                            <span className="font-medium">Análise Automática de Padrões</span>
                            <p className="text-gray-600 text-xs mt-1">Descubra tendências ocultas nos seus gastos</p>
                          </div>
                        </li>
                        <li className="flex items-start">
                          <CheckCircleIcon className="h-5 w-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
                          <div>
                            <span className="font-medium">Previsões Inteligentes de Fluxo de Caixa</span>
                            <p className="text-gray-600 text-xs mt-1">Antecipe problemas e oportunidades financeiras</p>
                          </div>
                        </li>
                        <li className="flex items-start">
                          <CheckCircleIcon className="h-5 w-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
                          <div>
                            <span className="font-medium">Recomendações de Economia Personalizadas</span>
                            <p className="text-gray-600 text-xs mt-1">Economize mais com sugestões baseadas no seu perfil</p>
                          </div>
                        </li>
                        <li className="flex items-start">
                          <CheckCircleIcon className="h-5 w-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
                          <div>
                            <span className="font-medium">Alertas Proativos de Oportunidades</span>
                            <p className="text-gray-600 text-xs mt-1">Seja notificado antes que problemas aconteçam</p>
                          </div>
                        </li>
                      </ul>
                      
                      <div className="mt-4 p-3 bg-white/70 rounded-lg">
                        <p className="text-xs text-center text-purple-700 font-medium">
                          💡 Empresas que usam nossos insights de IA economizam em média 23% nos custos mensais
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                      <Button 
                        onClick={() => router.push('/pricing')}
                        className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold px-8 py-3 text-lg"
                        size="lg"
                      >
                        🚀 Fazer Upgrade Agora
                      </Button>
                      <Button 
                        variant="outline"
                        onClick={() => router.push('/settings?tab=billing')}
                        className="border-purple-300 text-purple-700 hover:bg-purple-50 font-medium px-6 py-3"
                        size="lg"
                      >
                        💳 Configurar Pagamento
                      </Button>
                    </div>
                    
                    <div className="mt-4 text-center">
                      <p className="text-xs text-gray-500">
                        ⚡ Ativação instantânea • 💰 Primeiro mês com desconto • 🔒 Cancele quando quiser
                      </p>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Generic Error State */}
              {aiInsightsError && !isUpgradeRequired && (
                <div className="text-center py-8">
                  <ExclamationTriangleIcon className="h-12 w-12 mx-auto text-yellow-500 mb-4" />
                  <p className="text-gray-600">Erro ao carregar insights. Tente novamente mais tarde.</p>
                  <Button 
                    variant="outline" 
                    className="mt-4"
                    onClick={() => refetchAIInsights()}
                  >
                    <ArrowPathIcon className="h-4 w-4 mr-2" />
                    Tentar Novamente
                  </Button>
                </div>
              )}

              {/* Banner de limite atingido quando há dados em cache */}
              {isUpgradeRequired && aiInsightsData && (
                <div className="mb-6 p-4 bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <LockClosedIcon className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <h4 className="font-medium text-yellow-900">Limite de requisições atingido</h4>
                      <p className="text-sm text-yellow-800 mt-1">
                        Você atingiu o limite mensal de análises com IA. Faça upgrade para continuar atualizando seus insights.
                      </p>
                      <div className="flex gap-3 mt-3">
                        <Button 
                          size="sm"
                          onClick={() => router.push('/pricing')}
                          className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
                        >
                          🚀 Fazer Upgrade
                        </Button>
                        <Button 
                          size="sm"
                          variant="outline"
                          onClick={() => router.push('/settings?tab=billing')}
                          className="border-yellow-300 text-yellow-800 hover:bg-yellow-50"
                        >
                          Ver Planos
                        </Button>
                      </div>
                    </div>
                  </div>
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
                    <ArrowTrendingUpIcon className="h-5 w-5 mr-2 text-purple-600" />
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

              {/* Empty State - No Analysis Generated */}
              {!aiInsightsData && !aiInsightsLoading && selectedPeriod.start_date && selectedPeriod.end_date && (
                <div className="text-center py-12">
                  <SparklesIcon className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Gere Sua Primeira Análise com IA
                  </h3>
                  <p className="text-gray-500 mb-6">
                    Clique no botão &quot;Gerar Análise com IA&quot; acima para obter insights inteligentes sobre o período selecionado.
                  </p>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
                    <strong>Dica:</strong> Nossa IA analisará suas transações e fornecerá insights valiosos sobre padrões de gastos, oportunidades de economia e previsões financeiras. As análises são salvas automaticamente após serem geradas.
                  </div>
                </div>
              )}

              {/* Empty State - No Period Selected */}
              {!selectedPeriod.start_date || !selectedPeriod.end_date ? (
                <div className="text-center py-8">
                  <CalendarIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                  <p className="text-gray-500">Selecione um período para começar</p>
                </div>
              ) : null}

              {/* AI Badge */}
              {aiInsightsData && (
                <div className="mt-8 flex items-center justify-center">
                  <div className="inline-flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-purple-100 to-pink-100 rounded-full text-sm">
                    <SparklesIcon className="h-4 w-4 text-purple-600" />
                    <span className="text-purple-700 font-medium">
                      {aiInsightsData.ai_generated ? 'Powered by OpenAI GPT' : 'Análise Avançada (Modo Offline)'}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </AIInsightsErrorBoundary>
      )}

      {/* STEP 3: Advanced Tools - Only show when analysis is ready */}
      {currentStep === 3 && aiInsightsData && (
        <Card className="border-2 border-blue-200 bg-gradient-to-br from-blue-50/50 to-indigo-50/50">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl flex items-center justify-center gap-2">
              <SparklesIcon className="h-7 w-7 text-blue-600" />
              Ferramentas Avançadas
              <Badge className="bg-gradient-to-r from-blue-600 to-indigo-600">PREMIUM</Badge>
            </CardTitle>
            <CardDescription className="text-base">
              Explore ferramentas exclusivas para maximizar seus resultados
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-3 mb-8 h-auto p-1">
                <TabsTrigger 
                  value="context" 
                  className="flex flex-col items-center gap-2 py-4 data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-indigo-600 data-[state=active]:text-white"
                >
                  <CogIcon className="h-6 w-6" />
                  <div className="text-center">
                    <div className="text-sm font-semibold">Contexto</div>
                    <div className="text-xs opacity-80">Personalizar IA</div>
                  </div>
                </TabsTrigger>
                <TabsTrigger 
                  value="simulator" 
                  className="flex flex-col items-center gap-2 py-4 data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-indigo-600 data-[state=active]:text-white"
                >
                  <BeakerIcon className="h-6 w-6" />
                  <div className="text-center">
                    <div className="text-sm font-semibold">Simulador</div>
                    <div className="text-xs opacity-80">Cenários</div>
                  </div>
                </TabsTrigger>
                <TabsTrigger 
                  value="benchmarking" 
                  className="flex flex-col items-center gap-2 py-4 data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-indigo-600 data-[state=active]:text-white"
                >
                  <GlobeAltIcon className="h-6 w-6" />
                  <div className="text-center">
                    <div className="text-sm font-semibold">Benchmarking</div>
                    <div className="text-xs opacity-80">Compare</div>
                  </div>
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="context" className="mt-8">
                <div className="mb-4 text-center">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">🎯 Configure o Contexto</h3>
                  <p className="text-gray-600 text-sm">Adicione informações sobre seu negócio para análises mais precisas</p>
                </div>
                <ContextInput 
                  onContextUpdate={(context) => {
                    setBusinessContext(context);
                    toast.success('Contexto atualizado! As próximas análises serão mais personalizadas.');
                    // Força nova análise com contexto
                    if (aiInsightsData) {
                      setForceRefresh(true);
                      setShouldFetchAnalysis(true);
                      setCurrentStep(2);
                      setTimeout(() => refetchAIInsights(), 100);
                    }
                  }}
                  initialContext={businessContext || undefined}
                />
              </TabsContent>
              
              <TabsContent value="simulator" className="mt-8">
                <div className="mb-4 text-center">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">🧪 Simule Cenários</h3>
                  <p className="text-gray-600 text-sm">Teste diferentes situações e veja o impacto no seu negócio</p>
                </div>
                <EnhancedScenarioSimulator
                  currentData={{
                    income: aiInsightsData.key_metrics?.income || 0,
                    expenses: aiInsightsData.key_metrics?.expenses || 0,
                    categories: aiInsightsData.top_expense_categories || [],
                    monthlyTrend: aiInsightsData.monthly_trend
                  }}
                  predictions={aiInsightsData.predictions}
                  businessContext={businessContext}
                  onSimulationComplete={(results) => {
                    console.log('Simulation results:', results);
                    toast.success('🎆 Simulação concluída com sucesso!');
                  }}
                />
              </TabsContent>
              
              <TabsContent value="benchmarking" className="mt-8">
                <div className="mb-4 text-center">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">🏆 Compare com o Mercado</h3>
                  <p className="text-gray-600 text-sm">Veja como sua empresa se compara com outras do setor</p>
                </div>
                <MarketBenchmarking
                  companyData={{
                    industry: businessContext?.industry || 'services',
                    size: 'small',
                    revenue: aiInsightsData.key_metrics?.income || 0,
                    expenses: aiInsightsData.key_metrics?.expenses || 0,
                    profitMargin: aiInsightsData.key_metrics?.profit_margin || 0,
                    expenseRatio: aiInsightsData.key_metrics?.expense_ratio || 0,
                    categories: aiInsightsData.top_expense_categories || []
                  }}
                  keyMetrics={aiInsightsData.key_metrics}
                />
              </TabsContent>
            </Tabs>
            
            <div className="mt-8 text-center">
              <Button
                onClick={() => setCurrentStep(1)}
                variant="outline"
                className="mr-4"
              >
                ← Nova Análise
              </Button>
              <Button
                onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                variant="ghost"
              >
                ↑ Voltar ao topo
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Saved AI Analyses Section - Always visible */}
      <AIAnalysesSection />
    </div>
  );
}