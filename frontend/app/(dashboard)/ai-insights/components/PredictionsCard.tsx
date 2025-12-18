'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp } from 'lucide-react';
import { Predictions } from '@/services/ai-insights.service';
import { formatCurrency } from '@/lib/utils';

interface PredictionsCardProps {
  predictions: Predictions;
}

export function PredictionsCard({ predictions }: PredictionsCardProps) {
  if (!predictions || !predictions.next_month_cash_flow) {
    return null;
  }

  const confidenceColors = {
    high: 'text-green-400 bg-green-500/20',
    medium: 'text-yellow-400 bg-yellow-500/20',
    low: 'text-red-400 bg-red-500/20'
  };

  const confidenceLabels = {
    high: 'Alta',
    medium: 'Média',
    low: 'Baixa'
  };

  const confidenceColor = confidenceColors[predictions.confidence || 'medium'];
  const confidenceLabel = confidenceLabels[predictions.confidence || 'medium'];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-blue-500" />
          Previsões
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Prediction Value */}
          <div className="text-center py-4 bg-muted/30 rounded-lg">
            <div className="text-sm text-muted-foreground mb-1">
              Fluxo de Caixa Previsto (Próximo Mês)
            </div>
            <div className="text-3xl font-bold text-blue-600">
              {formatCurrency(predictions.next_month_cash_flow)}
            </div>
          </div>

          {/* Confidence */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Confiança da Previsão:</span>
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${confidenceColor}`}>
              {confidenceLabel}
            </span>
          </div>

          {/* Reasoning */}
          {predictions.reasoning && (
            <div className="border-l-4 border-blue-500 pl-4 py-2 bg-muted/20 rounded-r-lg">
              <p className="text-xs font-medium text-muted-foreground mb-1">
                📊 Justificativa:
              </p>
              <p className="text-sm">{predictions.reasoning}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
