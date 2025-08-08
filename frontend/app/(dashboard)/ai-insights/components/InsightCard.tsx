'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Lightbulb,
  DollarSign,
  BarChart3,
  Target,
  AlertCircle,
  CheckCircle2,
  X,
} from 'lucide-react';
import { cn, formatCurrency } from '@/lib/utils';
import { AIInsight } from '../types/ai-insights.types';
import { testId, TEST_IDS, testIdWithIndex } from '@/utils/test-helpers';

interface InsightCardProps {
  insight: AIInsight;
  compact?: boolean;
  onAction?: (insightId: string, action: 'complete' | 'dismiss') => void;
}

const insightIcons = {
  cost_saving: DollarSign,
  cash_flow: BarChart3,
  anomaly: AlertTriangle,
  opportunity: Lightbulb,
  risk: AlertCircle,
  trend: TrendingUp,
  benchmark: Target,
  tax: DollarSign,
  growth: TrendingUp,
};

const priorityColors = {
  critical: 'bg-gradient-to-r from-red-100 to-pink-100 text-red-800 border-red-200',
  high: 'bg-gradient-to-r from-orange-100 to-pink-100 text-orange-800 border-orange-200',
  medium: 'bg-gradient-to-r from-yellow-100 to-pink-100 text-yellow-800 border-yellow-200',
  low: 'bg-gradient-to-r from-blue-100 to-purple-100 text-blue-800 border-blue-200',
};

const priorityLabels = {
  critical: 'Crítico',
  high: 'Alto',
  medium: 'Médio',
  low: 'Baixo',
};

export function InsightCard({ insight, compact = false, onAction }: InsightCardProps) {
  const [expanded, setExpanded] = useState(false);
  const Icon = insightIcons[insight.type] || AlertCircle;

  if (compact) {
    return (
      <Card className="p-3 bg-white/50 backdrop-blur-sm hover:shadow-xl transition-all duration-300 cursor-pointer border border-white/20 hover:border-pink-200/50 transform hover:scale-[1.02]" onClick={() => setExpanded(!expanded)} {...testId(TEST_IDS.aiInsights.insightCardCompact)}>
        <div className="flex items-start gap-3">
          <div className={cn(
            'h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-md',
            priorityColors[insight.priority].replace('text-', 'bg-').replace('-800', '-100')
          )}>
            <Icon className={cn('h-4 w-4', priorityColors[insight.priority].replace('bg-', 'text-').replace('-100', '-600'))} />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-sm truncate">{insight.title}</h4>
            {insight.potential_impact && (
              <p className="text-xs text-gray-500 mt-1">
                Impacto: {formatCurrency(insight.potential_impact)}
              </p>
            )}
          </div>
          <Badge variant="outline" className={cn('text-xs', priorityColors[insight.priority])}>
            {priorityLabels[insight.priority]}
          </Badge>
        </div>

        {expanded && (
          <div className="mt-3 pt-3 border-t">
            <p className="text-sm text-gray-600">{insight.description}</p>
            {insight.action_items && insight.action_items.length > 0 && (
              <div className="mt-2">
                <p className="text-xs font-medium text-gray-700 mb-1">Ações sugeridas:</p>
                <ul className="space-y-1">
                  {insight.action_items.map((action, index) => (
                    <li key={index} className="text-xs text-gray-600 flex items-start gap-1">
                      <span className="text-gray-400 mt-0.5">•</span>
                      <span>{action}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </Card>
    );
  }

  return (
    <Card className="p-6 bg-white/50 backdrop-blur-sm shadow-lg hover:shadow-xl transition-all duration-300 border border-white/20 hover:border-pink-200/50" {...testId(TEST_IDS.aiInsights.insightCard)}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-4">
          <div className={cn(
            'h-12 w-12 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg',
            priorityColors[insight.priority].replace('text-', 'bg-').replace('-800', '-100')
          )}>
            <Icon className={cn('h-6 w-6', priorityColors[insight.priority].replace('bg-', 'text-').replace('-100', '-600'))} />
          </div>
          <div>
            <h3 className="font-semibold text-lg">{insight.title}</h3>
            <p className="text-gray-600 mt-1">{insight.description}</p>
          </div>
        </div>
        <Badge className={cn(priorityColors[insight.priority])}>
          {priorityLabels[insight.priority]}
        </Badge>
      </div>

      {/* Impact and metrics */}
      {(insight.potential_impact || insight.impact_percentage) && (
        <div className="flex items-center gap-6 mb-4">
          {insight.potential_impact && (
            <div>
              <p className="text-sm text-gray-500">Impacto potencial</p>
              <p className="text-xl font-semibold text-gray-900">
                {formatCurrency(insight.potential_impact)}
              </p>
            </div>
          )}
          {insight.impact_percentage && (
            <div>
              <p className="text-sm text-gray-500">Variação</p>
              <p className="text-xl font-semibold text-gray-900">
                {insight.impact_percentage > 0 ? '+' : ''}{insight.impact_percentage}%
              </p>
            </div>
          )}
        </div>
      )}

      {/* Action items */}
      {insight.action_items && insight.action_items.length > 0 && (
        <div className="mb-4">
          <h4 className="font-medium text-sm text-gray-700 mb-2">Ações recomendadas:</h4>
          <div className="space-y-2">
            {insight.action_items.map((action, index) => (
              <div key={index} className="flex items-start gap-2">
                <Checkbox 
                  id={`action-${insight.id}-${index}`} 
                  className="mt-0.5" 
                  {...testIdWithIndex(TEST_IDS.aiInsights.insightActionCheckbox, index)}
                />
                <label
                  htmlFor={`action-${insight.id}-${index}`}
                  className="text-sm text-gray-600 cursor-pointer"
                >
                  {action}
                </label>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      {onAction && insight.status !== 'completed' && insight.status !== 'dismissed' && (
        <div className="flex items-center gap-2 pt-4 border-t">
          <Button
            size="sm"
            onClick={() => onAction(insight.id, 'complete')}
            className="flex-1 bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white shadow-md hover:shadow-lg transition-all duration-300 transform hover:scale-105"
            {...testId(TEST_IDS.aiInsights.insightCompleteButton)}
          >
            <CheckCircle2 className="h-4 w-4 mr-2" />
            Marcar como concluído
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => onAction(insight.id, 'dismiss')}
            className="border-pink-200 text-pink-700 hover:bg-pink-50 hover:border-pink-300 transition-all duration-300"
            {...testId(TEST_IDS.aiInsights.insightDismissButton)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Status indicators */}
      {insight.status === 'completed' && (
        <div className="flex items-center gap-2 pt-4 border-t text-green-600">
          <CheckCircle2 className="h-4 w-4" />
          <span className="text-sm font-medium">Concluído</span>
          {insight.actual_impact && (
            <span className="text-sm">
              - Economia real: {formatCurrency(insight.actual_impact)}
            </span>
          )}
        </div>
      )}
    </Card>
  );
}