'use client';

import { Sparkles, Brain, TrendingUp, Bell, BarChart3 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

export default function AIInsightsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white">Insights com IA</h1>
        <p className="text-muted-foreground mt-1">
          Análises inteligentes das suas finanças
        </p>
      </div>

      {/* Coming Soon Card */}
      <div className="flex items-center justify-center min-h-[500px]">
        <Card className="max-w-2xl w-full border-blue-500/20 bg-gradient-to-br from-blue-500/5 to-purple-500/5">
          <CardContent className="pt-12 pb-12 text-center space-y-8">
            {/* Icon */}
            <div className="relative mx-auto w-24 h-24">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full opacity-20 animate-pulse" />
              <div className="relative bg-gradient-to-br from-blue-500 to-purple-500 rounded-full p-6 w-24 h-24 flex items-center justify-center">
                <Sparkles className="h-12 w-12 text-white" />
              </div>
            </div>

            {/* Title */}
            <div className="space-y-3">
              <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Em Breve
              </h2>
              <p className="text-lg text-muted-foreground max-w-md mx-auto">
                Estamos trabalhando em algo incrível para você.
                Análises financeiras inteligentes com IA estão chegando.
              </p>
            </div>

            {/* Features Preview */}
            <div className="grid grid-cols-2 gap-4 max-w-lg mx-auto pt-4">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5 border border-white/10">
                <Brain className="h-5 w-5 text-blue-400" />
                <span className="text-sm text-muted-foreground">Score de Saúde</span>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5 border border-white/10">
                <Bell className="h-5 w-5 text-orange-400" />
                <span className="text-sm text-muted-foreground">Alertas Inteligentes</span>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5 border border-white/10">
                <TrendingUp className="h-5 w-5 text-green-400" />
                <span className="text-sm text-muted-foreground">Previsões</span>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5 border border-white/10">
                <BarChart3 className="h-5 w-5 text-purple-400" />
                <span className="text-sm text-muted-foreground">Recomendações</span>
              </div>
            </div>

            {/* Footer */}
            <p className="text-xs text-muted-foreground pt-4">
              Fique atento! Você será notificado quando estiver disponível.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
