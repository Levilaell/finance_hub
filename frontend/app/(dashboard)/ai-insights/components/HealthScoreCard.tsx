'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { aiInsightsService } from '@/services/ai-insights.service';

interface HealthScoreCardProps {
  score: number;
  status: string;
  scoreChange: number | null;
}

export function HealthScoreCard({ score, status, scoreChange }: HealthScoreCardProps) {
  const statusLabel = aiInsightsService.getHealthStatusLabel(status);
  const statusColor = aiInsightsService.getHealthStatusColor(status);
  const statusBgColor = aiInsightsService.getHealthStatusBgColor(status);

  // Ensure score is a number (backend sends Decimal as string)
  const numericScore = typeof score === 'string' ? parseFloat(score) : score;
  const numericScoreChange = scoreChange !== null && typeof scoreChange === 'string' ? parseFloat(scoreChange) : scoreChange;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Health Status */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Saúde Financeira</CardTitle>
          <div className={`px-3 py-1 rounded-full ${statusBgColor}`}>
            <span className={`text-sm font-semibold ${statusColor}`}>
              {statusLabel}
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-4xl font-bold">{numericScore.toFixed(1)}/10</div>
          {numericScoreChange !== null && (
            <div className="flex items-center gap-2 mt-2">
              {numericScoreChange >= 0 ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500" />
              )}
              <span className={`text-sm ${numericScoreChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {numericScoreChange >= 0 ? '+' : ''}{numericScoreChange.toFixed(1)} pontos vs mês anterior
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Score Progress */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Score de Saúde</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Pontuação</span>
              <span className="font-bold">{numericScore.toFixed(1)}/10</span>
            </div>
            <Progress value={numericScore * 10} className="h-3" />
          </div>
          <div className="grid grid-cols-4 gap-2 text-xs text-center">
            <div>
              <div className={`font-semibold ${numericScore <= 2.5 ? 'text-red-600' : 'text-muted-foreground'}`}>
                Ruim
              </div>
              <div className="text-muted-foreground">0-2.5</div>
            </div>
            <div>
              <div className={`font-semibold ${numericScore > 2.5 && numericScore <= 5 ? 'text-yellow-600' : 'text-muted-foreground'}`}>
                Regular
              </div>
              <div className="text-muted-foreground">2.5-5</div>
            </div>
            <div>
              <div className={`font-semibold ${numericScore > 5 && numericScore <= 7.5 ? 'text-blue-600' : 'text-muted-foreground'}`}>
                Bom
              </div>
              <div className="text-muted-foreground">5-7.5</div>
            </div>
            <div>
              <div className={`font-semibold ${numericScore > 7.5 ? 'text-green-600' : 'text-muted-foreground'}`}>
                Excelente
              </div>
              <div className="text-muted-foreground">7.5-10</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
