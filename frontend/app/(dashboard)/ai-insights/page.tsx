'use client';

import { useEffect, useState } from 'react';
import { Sparkles, Clock, Calendar, RefreshCw, History } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { aiInsightsService, AIInsight, AIInsightConfig } from '@/services/ai-insights.service';
import { HealthScoreCard } from './components/HealthScoreCard';
import { InsightCard } from './components/InsightCard';
import { PredictionsCard } from './components/PredictionsCard';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import Link from 'next/link';

const companyTypes = [
  { value: 'mei', label: 'MEI' },
  { value: 'me', label: 'Microempresa' },
  { value: 'epp', label: 'Empresa de Pequeno Porte' },
  { value: 'ltda', label: 'Limitada' },
  { value: 'sa', label: 'Sociedade Anônima' },
  { value: 'other', label: 'Outros' },
];

const businessSectors = [
  { value: 'retail', label: 'Comércio' },
  { value: 'services', label: 'Serviços' },
  { value: 'industry', label: 'Indústria' },
  { value: 'technology', label: 'Tecnologia' },
  { value: 'healthcare', label: 'Saúde' },
  { value: 'education', label: 'Educação' },
  { value: 'food', label: 'Alimentação' },
  { value: 'construction', label: 'Construção' },
  { value: 'automotive', label: 'Automotivo' },
  { value: 'agriculture', label: 'Agricultura' },
  { value: 'other', label: 'Outros' },
];

export default function AIInsightsPage() {
  const [config, setConfig] = useState<AIInsightConfig | null>(null);
  const [latestInsight, setLatestInsight] = useState<AIInsight | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [canEnable, setCanEnable] = useState(false);

  // Form state
  const [companyType, setCompanyType] = useState('');
  const [businessSector, setBusinessSector] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  // Polling effect: check for new insight every 5 seconds if enabled but no insight yet
  // Stop after 3 minutes to prevent infinite loading
  useEffect(() => {
    if (config?.is_enabled && !latestInsight && !isLoading) {
      let pollCount = 0;
      const maxPolls = 36; // 3 minutes (36 * 5 seconds)

      const interval = setInterval(() => {
        pollCount++;
        if (pollCount >= maxPolls) {
          clearInterval(interval);
          setError('A geração está demorando mais que o esperado. Tente regenerar manualmente.');
        } else {
          loadData();
        }
      }, 5000); // Poll every 5 seconds

      return () => clearInterval(interval);
    }
  }, [config?.is_enabled, latestInsight, isLoading]);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const canEnableResponse = await aiInsightsService.canEnable();
      setCanEnable(canEnableResponse.can_enable);

      const configData = await aiInsightsService.getConfig();
      setConfig(configData);

      if (configData.is_enabled) {
        try {
          const insight = await aiInsightsService.getLatest();
          setLatestInsight(insight);
        } catch (err: any) {
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

  const handleActivate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!companyType || !businessSector) {
      setError('Por favor, preencha todos os campos');
      return;
    }

    setIsSubmitting(true);

    try {
      await aiInsightsService.enable({ company_type: companyType, business_sector: businessSector });

      // Reload config immediately to show "generating" state
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Erro ao habilitar insights');
      setIsSubmitting(false);
    }
  };

  const handleRegenerate = async () => {
    setIsRegenerating(true);
    setError(null);

    try {
      await aiInsightsService.regenerate();
      // Clear current insight to trigger loading state and polling
      setLatestInsight(null);
      // Reload data after a short delay
      setTimeout(() => {
        loadData();
      }, 2000);
    } catch (err: any) {
      console.error('Error regenerating insights:', err);
      setError(err.response?.data?.error || 'Erro ao forçar regeneração');
    } finally {
      setIsRegenerating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <LoadingSpinner />
      </div>
    );
  }

  // Not enabled - show activation form
  if (!config?.is_enabled) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">Insights com IA</h1>
            <p className="text-muted-foreground mt-1">
              Análises inteligentes das suas finanças
            </p>
          </div>
        </div>

        <div className="max-w-2xl mx-auto">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <div className="bg-gradient-to-br from-blue-500 to-purple-500 rounded-full p-3">
                  <Sparkles className="h-6 w-6 text-white" />
                </div>
                <div>
                  <CardTitle className="text-2xl">Ative os Insights com IA</CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">
                    Preencha as informações abaixo para começar
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleActivate} className="space-y-6">
                {/* Company Type */}
                <div className="space-y-2">
                  <Label htmlFor="company_type">Tipo de Empresa</Label>
                  <Select value={companyType} onValueChange={setCompanyType}>
                    <SelectTrigger id="company_type">
                      <SelectValue placeholder="Selecione o tipo" />
                    </SelectTrigger>
                    <SelectContent>
                      {companyTypes.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Business Sector */}
                <div className="space-y-2">
                  <Label htmlFor="business_sector">Setor de Atuação</Label>
                  <Select value={businessSector} onValueChange={setBusinessSector}>
                    <SelectTrigger id="business_sector">
                      <SelectValue placeholder="Selecione o setor" />
                    </SelectTrigger>
                    <SelectContent>
                      {businessSectors.map((sector) => (
                        <SelectItem key={sector.value} value={sector.value}>
                          {sector.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Error Message */}
                {error && (
                  <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                    <p className="text-sm text-red-400">{error}</p>
                  </div>
                )}

                {/* Info */}
                <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
                  <h4 className="font-semibold text-blue-300 mb-2">O que você terá acesso:</h4>
                  <ul className="space-y-2 text-sm text-blue-400 list-disc list-inside">
                    <li>Score de Saúde Financeira (0-10)</li>
                    <li>Alertas sobre riscos financeiros</li>
                    <li>Recomendações personalizadas</li>
                    <li>Previsões de fluxo de caixa</li>
                  </ul>
                  <p className="text-xs text-blue-500 mt-3">
                    Sua primeira análise será gerada em alguns instantes após ativar.
                  </p>
                </div>

                {/* Submit Button */}
                <Button
                  type="submit"
                  className="w-full bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
                  size="lg"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <LoadingSpinner />
                      <span className="ml-2">Ativando...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-5 w-5" />
                      Ativar Insights com IA
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Enabled but no insights yet
  if (!latestInsight) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">Insights com IA</h1>
            <p className="text-muted-foreground mt-1">
              Análises inteligentes das suas finanças
            </p>
          </div>
        </div>

        <div className="flex items-center justify-center min-h-[500px]">
          <Card className="max-w-md">
            <CardContent className="pt-6 text-center space-y-4">
              {error ? (
                <>
                  <div className="bg-yellow-500/20 rounded-full p-4 w-16 h-16 mx-auto flex items-center justify-center">
                    <Clock className="h-8 w-8 text-yellow-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold mb-2 text-yellow-400">Tempo Limite Excedido</h3>
                    <p className="text-sm text-muted-foreground">
                      {error}
                    </p>
                    <p className="text-xs text-muted-foreground mt-2">
                      Isso pode acontecer se houver muitos dados para processar ou problemas temporários no servidor.
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <div className="bg-muted rounded-full p-4 w-16 h-16 mx-auto flex items-center justify-center">
                    <RefreshCw className="h-8 w-8 animate-spin text-primary" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold mb-2">Gerando sua primeira análise</h3>
                    <p className="text-sm text-muted-foreground">
                      Estamos analisando seus dados financeiros. A página atualizará automaticamente quando pronto.
                    </p>
                    <p className="text-xs text-muted-foreground mt-2">
                      Isso pode levar de 10 a 30 segundos...
                    </p>
                  </div>
                  <div className="flex items-center justify-center gap-1">
                    <div className="h-2 w-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="h-2 w-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="h-2 w-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </>
              )}
              <Button
                onClick={handleRegenerate}
                variant="outline"
                disabled={isRegenerating}
              >
                {isRegenerating ? (
                  <>
                    <LoadingSpinner />
                    <span className="ml-2">Tentando novamente...</span>
                  </>
                ) : (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Tentar Novamente
                  </>
                )}
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
            <h1 className="text-3xl font-bold tracking-tight text-white">Insights com IA</h1>
            <p className="text-muted-foreground mt-1">
              Análises inteligentes das suas finanças
            </p>
          </div>
        </div>

        <Card className="border-red-500/20 bg-red-500/10">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="bg-red-500/20 rounded-full p-3">
                <Sparkles className="h-6 w-6 text-red-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-red-400 mb-2">
                  Erro ao Gerar Análise
                </h3>
                <p className="text-sm text-red-400/80 mb-4">
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

  // Check if insight is old (more than 7 days)
  const insightAge = latestInsight ? Math.floor((new Date().getTime() - new Date(latestInsight.generated_at).getTime()) / (1000 * 60 * 60 * 24)) : 0;
  const isOldInsight = insightAge > 7;

  // Show insights
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Insights com IA</h1>
          <p className="text-muted-foreground mt-1">
            Análises inteligentes das suas finanças
          </p>
        </div>
        <div className="flex gap-2">
          {isOldInsight && (
            <Button
              onClick={handleRegenerate}
              variant="default"
              disabled={isRegenerating}
              className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
            >
              {isRegenerating ? (
                <>
                  <LoadingSpinner />
                  <span className="ml-2">Gerando...</span>
                </>
              ) : (
                <>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Gerar Nova Análise
                </>
              )}
            </Button>
          )}
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

      {/* Old Insight Warning */}
      {isOldInsight && (
        <Card className="border-yellow-500/20 bg-yellow-500/10">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="bg-yellow-500/20 rounded-full p-2">
                <Clock className="h-5 w-5 text-yellow-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-yellow-400 mb-1">
                  Análise Desatualizada
                </h3>
                <p className="text-sm text-yellow-400/80">
                  Esta análise tem {insightAge} dias. Clique em "Gerar Nova Análise" para obter insights atualizados baseados nos seus dados mais recentes.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

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
                  <span className="flex-shrink-0 w-6 h-6 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center text-sm font-semibold">
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
