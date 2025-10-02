'use client';

import { Sparkles, Lightbulb, TrendingUp, AlertCircle } from 'lucide-react';

export default function AIInsightsPage() {
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
              Em Breve
            </h2>
            <p className="text-xl text-muted-foreground">
              Estamos preparando algo incrível para você
            </p>
          </div>

          {/* Description */}
          <div className="space-y-4 text-left">
            <p className="text-muted-foreground">
              Em breve você terá acesso a insights poderosos gerados por inteligência artificial, incluindo:
            </p>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex items-start gap-3 p-4 rounded-lg border bg-card">
                <Lightbulb className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-medium mb-1">Recomendações Personalizadas</h3>
                  <p className="text-sm text-muted-foreground">
                    Sugestões inteligentes para otimizar suas finanças
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 rounded-lg border bg-card">
                <TrendingUp className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-medium mb-1">Previsões Financeiras</h3>
                  <p className="text-sm text-muted-foreground">
                    Análise preditiva do seu fluxo de caixa
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 rounded-lg border bg-card">
                <AlertCircle className="h-5 w-5 text-orange-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-medium mb-1">Alertas Inteligentes</h3>
                  <p className="text-sm text-muted-foreground">
                    Notificações sobre padrões incomuns de gastos
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 rounded-lg border bg-card">
                <Sparkles className="h-5 w-5 text-purple-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-medium mb-1">Análise de Padrões</h3>
                  <p className="text-sm text-muted-foreground">
                    Identificação automática de tendências financeiras
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Call to Action */}
          <div className="pt-4">
            <p className="text-sm text-muted-foreground">
              Continue usando o CaixaHub e você será notificado quando este recurso estiver disponível.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
