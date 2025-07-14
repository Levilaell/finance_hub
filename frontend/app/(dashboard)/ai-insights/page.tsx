'use client';

import { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { DatePicker } from '@/components/ui/date-picker';
import { Label } from '@/components/ui/label';
import { reportsService } from '@/services/reports.service';
import { formatCurrency, formatDate, cn } from '@/lib/utils';
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
} from '@heroicons/react/24/outline';

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

const QUICK_PERIODS = [
  { id: 'current_month', label: 'Mês Atual', icon: CalendarIcon },
  { id: 'last_month', label: 'Mês Anterior', icon: CalendarIcon },
  { id: 'quarterly', label: 'Trimestre', icon: ChartBarIcon },
  { id: 'year_to_date', label: 'Ano Atual', icon: ArrowTrendingUpIcon },
];

export default function AIInsightsPage() {
  // State
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

  // Query
  const { 
    data: aiInsightsData, 
    isLoading: aiInsightsLoading, 
    error: aiInsightsError,
    refetch: refetchAIInsights,
    dataUpdatedAt
  } = useQuery({
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
    staleTime: 7 * 24 * 60 * 60 * 1000, // 7 dias em milissegundos
    cacheTime: 7 * 24 * 60 * 60 * 1000, // Manter cache por 7 dias
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
      default:
        start = new Date(now.getFullYear(), now.getMonth(), 1);
    }
    
    setSelectedPeriod({ start_date: start, end_date: end });
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <SparklesIcon className="h-8 w-8 text-purple-600" />
            Insights com IA
          </h1>
          <p className="text-gray-600">
            Análise inteligente e previsões baseadas em seus dados financeiros
          </p>
        </div>
      </div>

      {/* Period Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Selecione o Período</CardTitle>
          <CardDescription>Escolha um período para análise</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4 mb-4">
            {QUICK_PERIODS.map((period) => {
              const Icon = period.icon;
              return (
                <Button
                  key={period.id}
                  variant="outline"
                  className="justify-start h-auto p-4"
                  onClick={() => handleQuickPeriod(period.id)}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  <div className="text-left">
                    <div className="font-medium">{period.label}</div>
                  </div>
                </Button>
              );
            })}
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label>Data Inicial</Label>
              <DatePicker
                date={selectedPeriod.start_date || undefined}
                onDateChange={(date) =>
                  setSelectedPeriod({ ...selectedPeriod, start_date: date || new Date() })
                }
              />
            </div>
            <div>
              <Label>Data Final</Label>
              <DatePicker
                date={selectedPeriod.end_date || undefined}
                onDateChange={(date) =>
                  setSelectedPeriod({ ...selectedPeriod, end_date: date || new Date() })
                }
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* AI Insights Content */}
      <AIInsightsErrorBoundary>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center">
                <SparklesIcon className="h-5 w-5 mr-2" />
                Análise com Inteligência Artificial
              </div>
              <div className="flex items-center gap-2">
                {aiInsightsData?.predictions?.confidence && (
                  <ConfidenceIndicator level={aiInsightsData.predictions.confidence} />
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refetchAIInsights()}
                  disabled={aiInsightsLoading}
                  title="Atualizar análise"
                >
                  <ArrowPathIcon className={cn("h-4 w-4", aiInsightsLoading && "animate-spin")} />
                  <span className="ml-2">Atualizar</span>
                </Button>
              </div>
            </CardTitle>
            <CardDescription className="flex items-center justify-between">
              <span>Insights automáticos e previsões baseadas em seus dados financeiros</span>
              {dataUpdatedAt && (
                <span className="text-xs text-gray-500">
                  Última análise: {formatDate(new Date(dataUpdatedAt))}
                </span>
              )}
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
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </AIInsightsErrorBoundary>
    </div>
  );
}