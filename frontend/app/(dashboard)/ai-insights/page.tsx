'use client';

import { useEffect, useState } from 'react';
import { Sparkles, Clock, Calendar, RefreshCw, History } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { aiInsightsService, AIInsight, AIInsightConfig } from '@/services/ai-insights.service';
import { HealthScoreCard } from './components/HealthScoreCard';
import { InsightCard } from './components/InsightCard';
import { PredictionsCard } from './components/PredictionsCard';
import { EnableInsightsModal } from './components/EnableInsightsModal';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import Link from 'next/link';

export default function AIInsightsPage() {
  const [config, setConfig] = useState<AIInsightConfig | null>(null);
  const [latestInsight, setLatestInsight] = useState<AIInsight | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showEnableModal, setShowEnableModal] = useState(false);
  const [canEnable, setCanEnable] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Check if can enable
      const canEnableResponse = await aiInsightsService.canEnable();
      setCanEnable(canEnableResponse.can_enable);

      // Get config
      const configData = await aiInsightsService.getConfig();
      setConfig(configData);

      // If enabled, get latest insight
      if (configData.is_enabled) {
        try {
          const insight = await aiInsightsService.getLatest();
          setLatestInsight(insight);
        } catch (err: any) {
          // No insights yet - that's okay
          if (err.response?.status !== 404) {
            throw err;
          }
        }
      }
    } catch (err: any) {
      console.error('Error loading AI insights:', err);
      setError(err.response?.data?.error || 'Erro ao carregar insights');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEnableSuccess = () => {
    // Reload after enabling
    setTimeout(() => {
      loadData();
    }, 2000); // Give backend time to generate first insight
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <LoadingSpinner />
      </div>
    );
  }

  // Not enabled - show activation screen
  if (!config?.is_enabled) {
    return (
      <>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Insights com IA</h1>
              <p className="text-muted-foreground mt-1">
                Análises inteligentes das suas finanças
              </p>
            </div>
          </div>

          {/* Coming Soon Section */}
          <div className="flex items-center justify-center min-h-[500px]">
            <div className="text-center space-y-6 max-w-2xl px-4">
              {/* Icon */}
              <div className="flex justify-center">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full blur-xl opacity-50 animate-pulse"></div>
                  <div className="relative bg-gradient-to-br from-blue-500 to-purple-500 rounded-full p-6">
                    <Sparkles className="h-16 w-16 text-white" />
                  </div>
                </div>
              </div>

              {/* Title */}
              <div className="space-y-2">
                <h2 className="text-4xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
                  Ative Agora
                </h2>
                <p className="text-xl text-muted-foreground">
                  Obtenha insights poderosos gerados por IA
                </p>
              </div>

              {/* Description */}
              <div className="space-y-4 text-left">
                <p className="text-muted-foreground">
                  Com Insights com IA, você terá acesso a:
                </p>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="flex items-start gap-3 p-4 rounded-lg border bg-card">
                    <div className="text-2xl">🎯</div>
                    <div>
                      <h3 className="font-medium mb-1">Score de Saúde Financeira</h3>
                      <p className="text-sm text-muted-foreground">
                        Avaliação de 0 a 10 da situação da empresa
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-4 rounded-lg border bg-card">
                    <div className="text-2xl">🚨</div>
                    <div>
                      <h3 className="font-medium mb-1">Alertas Inteligentes</h3>
                      <p className="text-sm text-muted-foreground">
                        Notificações sobre padrões incomuns
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-4 rounded-lg border bg-card">
                    <div className="text-2xl">💡</div>
                    <div>
                      <h3 className="font-medium mb-1">Recomendações Personalizadas</h3>
                      <p className="text-sm text-muted-foreground">
                        Sugestões para otimizar suas finanças
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-4 rounded-lg border bg-card">
                    <div className="text-2xl">📈</div>
                    <div>
                      <h3 className="font-medium mb-1">Previsões Financeiras</h3>
                      <p className="text-sm text-muted-foreground">
                        Análise preditiva do fluxo de caixa
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* CTA */}
              <div className="pt-4">
                {canEnable ? (
                  <Button
                    size="lg"
                    onClick={() => setShowEnableModal(true)}
                    className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
                  >
                    <Sparkles className="mr-2 h-5 w-5" />
                    Ativar Insights com IA
                  </Button>
                ) : (
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">
                      Configure sua empresa em <Link href="/settings" className="text-blue-600 hover:underline">Configurações</Link> para ativar.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <EnableInsightsModal
          open={showEnableModal}
          onClose={() => setShowEnableModal(false)}
          onSuccess={handleEnableSuccess}
        />
      </>
    );
  }

  // Enabled but no insights yet
  if (!latestInsight) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Insights com IA</h1>
            <p className="text-muted-foreground mt-1">
              Análises inteligentes das suas finanças
            </p>
          </div>
        </div>

        <div className="flex items-center justify-center min-h-[500px]">
          <Card className="max-w-md">
            <CardContent className="pt-6 text-center space-y-4">
              <div className="bg-blue-100 rounded-full p-4 w-16 h-16 mx-auto flex items-center justify-center">
                <Clock className="h-8 w-8 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold mb-2">Gerando sua primeira análise</h3>
                <p className="text-sm text-muted-foreground">
                  Estamos analisando seus dados financeiros. Isso pode levar alguns instantes.
                </p>
              </div>
              <Button onClick={loadData} variant="outline">
                <RefreshCw className="mr-2 h-4 w-4" />
                Atualizar
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Show error if insight has error
  if (latestInsight.has_error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Insights com IA</h1>
            <p className="text-muted-foreground mt-1">
              Análises inteligentes das suas finanças
            </p>
          </div>
        </div>

        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="bg-red-100 rounded-full p-3">
                <Sparkles className="h-6 w-6 text-red-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-red-900 mb-2">
                  Erro ao Gerar Análise
                </h3>
                <p className="text-sm text-red-700 mb-4">
                  {latestInsight.error_message || 'Ocorreu um erro ao gerar a análise. Tente novamente mais tarde.'}
                </p>
                <Button onClick={loadData} variant="outline" size="sm">
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Tentar Novamente
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show insights
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Insights com IA</h1>
          <p className="text-muted-foreground mt-1">
            Análises inteligentes das suas finanças
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/ai-insights/history">
            <Button variant="outline">
              <History className="mr-2 h-4 w-4" />
              Histórico
            </Button>
          </Link>
        </div>
      </div>

      {/* Analysis Info */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span>
                  Última análise: {format(new Date(latestInsight.generated_at), "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })}
                </span>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Calendar className="h-4 w-4" />
                <span>
                  Período: {format(new Date(latestInsight.period_start), 'dd/MM/yyyy')} - {format(new Date(latestInsight.period_end), 'dd/MM/yyyy')}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Health Score */}
      <HealthScoreCard
        score={latestInsight.health_score}
        status={latestInsight.health_status}
        scoreChange={latestInsight.score_change}
      />

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle>📝 Resumo Executivo</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground leading-relaxed">
            {latestInsight.summary}
          </p>
        </CardContent>
      </Card>

      {/* Alerts */}
      {latestInsight.alerts.length > 0 && (
        <InsightCard
          title="Alertas"
          items={latestInsight.alerts}
          type="alert"
        />
      )}

      {/* Opportunities */}
      {latestInsight.opportunities.length > 0 && (
        <InsightCard
          title="Oportunidades"
          items={latestInsight.opportunities}
          type="opportunity"
        />
      )}

      {/* Predictions */}
      <PredictionsCard predictions={latestInsight.predictions} />

      {/* Recommendations */}
      {latestInsight.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>✅ Top Recomendações</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {latestInsight.recommendations.map((recommendation, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-semibold">
                    {index + 1}
                  </span>
                  <span className="text-muted-foreground">{recommendation}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
