'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { aiAnalysisService } from '@/services/ai-analysis.service';
import { formatCurrency, formatDate, cn } from '@/lib/utils';
import { toast } from 'sonner';
import {
  SparklesIcon,
  ArrowLeftIcon,
  CheckCircleIcon,
  TrashIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CalendarIcon,
  ClockIcon,
  BookmarkIcon,
} from '@heroicons/react/24/outline';

export default function AIAnalysisDetailPage() {
  const params = useParams();
  const router = useRouter();
  const analysisId = Number(params.id);

  // Query para buscar a análise
  const { 
    data: analysis, 
    isLoading, 
    error,
    refetch
  } = useQuery({
    queryKey: ['ai-analysis', analysisId],
    queryFn: () => aiAnalysisService.get(analysisId),
    enabled: !!analysisId,
  });

  // Toggle favorite mutation
  const toggleFavoriteMutation = useMutation({
    mutationFn: () => aiAnalysisService.toggleFavorite(analysisId),
    onSuccess: () => {
      refetch();
      toast.success('Favorito atualizado!');
    },
    onError: () => {
      toast.error('Erro ao atualizar favorito');
    }
  });

  // Delete analysis mutation
  const deleteAnalysisMutation = useMutation({
    mutationFn: () => aiAnalysisService.delete(analysisId),
    onSuccess: () => {
      toast.success('Análise excluída com sucesso!');
      router.push('/ai-insights');
    },
    onError: () => {
      toast.error('Erro ao excluir análise');
    }
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner className="h-8 w-8" />
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="h-12 w-12 mx-auto text-red-500 mb-4" />
        <h3 className="text-lg font-medium mb-2">Análise não encontrada</h3>
        <p className="text-gray-600 mb-4">A análise solicitada não existe ou foi removida.</p>
        <Button onClick={() => router.push('/ai-insights')}>
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Voltar para AI Insights
        </Button>
      </div>
    );
  }

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'success':
        return CheckCircleIcon;
      case 'warning':
        return ExclamationTriangleIcon;
      case 'info':
        return LightBulbIcon;
      case 'danger':
        return ExclamationTriangleIcon;
      default:
        return LightBulbIcon;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            onClick={() => router.push('/ai-insights')}
          >
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            Voltar
          </Button>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <SparklesIcon className="h-6 w-6 text-purple-600" />
              {analysis.title}
            </h1>
            <div className="flex items-center space-x-4 text-sm text-gray-600 mt-1">
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
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            onClick={() => toggleFavoriteMutation.mutate()}
            disabled={toggleFavoriteMutation.isPending}
            title={analysis.is_favorite ? "Remover dos favoritos" : "Adicionar aos favoritos"}
          >
            <CheckCircleIcon className={cn(
              "h-4 w-4",
              analysis.is_favorite ? "text-yellow-500" : "text-gray-400"
            )} />
            <span className="ml-2">
              {analysis.is_favorite ? 'Remover Favorito' : 'Favoritar'}
            </span>
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              if (confirm(`Tem certeza que deseja excluir a análise "${analysis.title}"?`)) {
                deleteAnalysisMutation.mutate();
              }
            }}
            disabled={deleteAnalysisMutation.isPending}
            className="text-red-600 hover:text-red-700 hover:bg-red-50"
          >
            <TrashIcon className="h-4 w-4 mr-2" />
            {deleteAnalysisMutation.isPending ? 'Excluindo...' : 'Excluir'}
          </Button>
        </div>
      </div>

      {/* Summary */}
      {analysis.summary && (
        <Card>
          <CardHeader>
            <CardTitle>Resumo Executivo</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analysis.summary.status_message && (
                <div>
                  <h4 className="font-medium">{analysis.summary.status_message}</h4>
                  {analysis.summary.key_message && (
                    <p className="text-gray-600 mt-1">{analysis.summary.key_message}</p>
                  )}
                </div>
              )}
              
              {analysis.summary.executive_takeaway && (
                <div className="p-4 bg-blue-50 rounded-lg">
                  <strong>Resumo:</strong> {analysis.summary.executive_takeaway}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {analysis.summary.main_opportunity && (
                  <div>
                    <h5 className="font-medium text-green-700">Principal Oportunidade</h5>
                    <p className="text-sm text-gray-600 mt-1">{analysis.summary.main_opportunity}</p>
                  </div>
                )}
                {analysis.summary.recommended_action && (
                  <div>
                    <h5 className="font-medium text-blue-700">Ação Recomendada</h5>
                    <p className="text-sm text-gray-600 mt-1">{analysis.summary.recommended_action}</p>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Insights */}
      {analysis.insights && analysis.insights.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Insights Detalhados</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analysis.insights.map((insight: any, index: number) => {
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
                          <div className="mt-2 text-lg font-bold">{insight.value}</div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Predictions */}
      {analysis.predictions && (
        <Card>
          <CardHeader>
            <CardTitle>Previsões</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-3 mb-4">
              {analysis.predictions.next_month_income && (
                <div className="bg-green-50 p-3 rounded-lg">
                  <div className="text-sm text-gray-600">Receita Prevista</div>
                  <div className="text-xl font-bold text-green-600">
                    {formatCurrency(analysis.predictions.next_month_income)}
                  </div>
                </div>
              )}
              {analysis.predictions.next_month_expenses && (
                <div className="bg-red-50 p-3 rounded-lg">
                  <div className="text-sm text-gray-600">Despesas Previstas</div>
                  <div className="text-xl font-bold text-red-600">
                    {formatCurrency(analysis.predictions.next_month_expenses)}
                  </div>
                </div>
              )}
              {analysis.predictions.projected_savings && (
                <div className="bg-blue-50 p-3 rounded-lg">
                  <div className="text-sm text-gray-600">Economia Estimada</div>
                  <div className="text-xl font-bold text-blue-600">
                    {formatCurrency(analysis.predictions.projected_savings)}
                  </div>
                </div>
              )}
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {analysis.predictions.opportunities && analysis.predictions.opportunities.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium mb-2">Oportunidades</h5>
                  <ul className="space-y-1">
                    {analysis.predictions.opportunities.map((opp: string, idx: number) => (
                      <li key={idx} className="text-sm flex items-start">
                        <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1 flex-shrink-0 mt-0.5" />
                        {opp}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {analysis.predictions.threats && analysis.predictions.threats.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium mb-2">Ameaças</h5>
                  <ul className="space-y-1">
                    {analysis.predictions.threats.map((threat: string, idx: number) => (
                      <li key={idx} className="text-sm flex items-start">
                        <ExclamationTriangleIcon className="h-4 w-4 text-red-500 mr-1 flex-shrink-0 mt-0.5" />
                        {threat}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      {analysis.recommendations && analysis.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recomendações</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analysis.recommendations.map((rec: any, index: number) => (
                <div 
                  key={index} 
                  className="p-4 border rounded-lg bg-gray-50"
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
          </CardContent>
        </Card>
      )}

      {/* Technical Info */}
      <Card>
        <CardHeader>
          <CardTitle>Informações Técnicas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            {analysis.confidence_score && (
              <div>
                <span className="text-gray-600">Confiança:</span>
                <div className="font-medium">{analysis.confidence_score}%</div>
              </div>
            )}
            {analysis.health_score && (
              <div>
                <span className="text-gray-600">Saúde Financeira:</span>
                <div className="font-medium">{analysis.health_score}/100</div>
              </div>
            )}
            <div>
              <span className="text-gray-600">Criado por:</span>
              <div className="font-medium">{analysis.created_by_name}</div>
            </div>
            <div>
              <span className="text-gray-600">Data de criação:</span>
              <div className="font-medium">{analysis.created_at ? formatDate(analysis.created_at) : 'N/A'}</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}