'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { aiInsightsService, AIInsight } from '@/services/ai-insights.service';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { ArrowLeft, TrendingUp, TrendingDown } from 'lucide-react';
import Link from 'next/link';

export default function HistoryPage() {
  const router = useRouter();
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const data = await aiInsightsService.getHistory();
      setInsights(data);
    } catch (err) {
      console.error('Error loading history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link href="/ai-insights">
            <Button variant="ghost" size="sm" className="mb-2">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Voltar
            </Button>
          </Link>
          <h1 className="text-3xl font-bold tracking-tight">Histórico de Análises</h1>
          <p className="text-muted-foreground mt-1">
            Veja a evolução dos seus insights ao longo do tempo
          </p>
        </div>
      </div>

      {/* Insights List */}
      {insights.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center py-12">
            <p className="text-muted-foreground">Nenhuma análise encontrada</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {insights.map((insight) => {
            const numericScore = typeof insight.health_score === 'string' ? parseFloat(insight.health_score) : insight.health_score;
            const numericScoreChange = insight.score_change !== null && typeof insight.score_change === 'string' ? parseFloat(insight.score_change) : insight.score_change;

            return (
            <Card key={insight.id} className={insight.has_error ? 'border-red-200 bg-red-50/30' : ''}>
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  {/* Left Side - Main Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-2">
                      <div className="text-3xl font-bold">{numericScore.toFixed(1)}</div>
                      <div>
                        <div className={`px-3 py-1 rounded-full text-sm font-semibold inline-block ${
                          aiInsightsService.getHealthStatusBgColor(insight.health_status)
                        } ${aiInsightsService.getHealthStatusColor(insight.health_status)}`}>
                          {aiInsightsService.getHealthStatusLabel(insight.health_status)}
                        </div>
                        {numericScoreChange !== null && (
                          <div className="flex items-center gap-1 mt-1">
                            {numericScoreChange >= 0 ? (
                              <TrendingUp className="h-4 w-4 text-green-500" />
                            ) : (
                              <TrendingDown className="h-4 w-4 text-red-500" />
                            )}
                            <span className={`text-sm ${numericScoreChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {numericScoreChange >= 0 ? '+' : ''}{numericScoreChange.toFixed(1)}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    <p className="text-sm text-muted-foreground mb-3">
                      {insight.summary}
                    </p>

                    <div className="flex gap-4 text-xs text-muted-foreground">
                      <div>
                        📅 {format(new Date(insight.period_start), 'dd/MM/yyyy')} - {format(new Date(insight.period_end), 'dd/MM/yyyy')}
                      </div>
                      <div>
                        🕐 {format(new Date(insight.generated_at), "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })}
                      </div>
                    </div>

                    {insight.has_error && (
                      <div className="mt-3 text-sm text-red-600">
                        ⚠️ {insight.error_message || 'Erro ao gerar análise'}
                      </div>
                    )}
                  </div>

                  {/* Right Side - Stats */}
                  {!insight.has_error && (
                    <div className="flex gap-6 text-center">
                      <div>
                        <div className="text-2xl font-bold text-red-600">{insight.alerts.length}</div>
                        <div className="text-xs text-muted-foreground">Alertas</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-yellow-600">{insight.opportunities.length}</div>
                        <div className="text-xs text-muted-foreground">Oportunidades</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-blue-600">{insight.recommendations.length}</div>
                        <div className="text-xs text-muted-foreground">Dicas</div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          );
          })}
        </div>
      )}
    </div>
  );
}
