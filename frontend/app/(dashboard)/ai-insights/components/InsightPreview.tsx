'use client';

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Lightbulb,
  DollarSign,
  BarChart3,
  Target,
  AlertCircle,
} from 'lucide-react';
import { cn, formatCurrency } from '@/lib/utils';
import { AIInsightPreview } from '../types/ai-insights.types';

interface InsightPreviewProps {
  insight: AIInsightPreview;
  compact?: boolean;
}

const insightIcons = {
  cost_saving: DollarSign,
  cash_flow: TrendingUp,
  anomaly: AlertTriangle,
  opportunity: Lightbulb,
  risk: AlertCircle,
  trend: BarChart3,
  benchmark: Target,
  tax: DollarSign,
  growth: TrendingUp,
};

const priorityColors = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low: 'bg-blue-100 text-blue-800 border-blue-200',
};

export function InsightPreview({ insight, compact = false }: InsightPreviewProps) {
  const Icon = insightIcons[insight.type as keyof typeof insightIcons] || Lightbulb;

  return (
    <Card className={cn(
      'p-4 border-l-4',
      insight.priority === 'critical' && 'border-l-red-500',
      insight.priority === 'high' && 'border-l-orange-500',
      insight.priority === 'medium' && 'border-l-yellow-500',
      insight.priority === 'low' && 'border-l-blue-500',
      compact && 'p-3'
    )}>
      <div className="flex items-start gap-3">
        <div className={cn(
          'p-2 rounded-lg',
          insight.priority === 'critical' && 'bg-red-100 text-red-600',
          insight.priority === 'high' && 'bg-orange-100 text-orange-600',
          insight.priority === 'medium' && 'bg-yellow-100 text-yellow-600',
          insight.priority === 'low' && 'bg-blue-100 text-blue-600'
        )}>
          <Icon className="h-4 w-4" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <h4 className={cn(
              'font-medium',
              compact ? 'text-sm' : 'text-base'
            )}>
              {insight.title}
            </h4>
            <Badge className={cn(
              'text-xs',
              priorityColors[insight.priority]
            )}>
              {insight.priority === 'critical' && 'Crítico'}
              {insight.priority === 'high' && 'Alto'}
              {insight.priority === 'medium' && 'Médio'}
              {insight.priority === 'low' && 'Baixo'}
            </Badge>
          </div>
          
          <p className={cn(
            'text-gray-600',
            compact ? 'text-sm' : 'text-base'
          )}>
            {insight.description}
          </p>
          
          {insight.potential_impact && (
            <div className="mt-2 flex items-center gap-1 text-sm text-green-600">
              <TrendingUp className="h-3 w-3" />
              <span>Impacto potencial: {formatCurrency(insight.potential_impact)}</span>
            </div>
          )}
          
          {insight.action_items && insight.action_items.length > 0 && (
            <div className="mt-3">
              <h5 className="text-sm font-medium text-gray-700 mb-1">Ações recomendadas:</h5>
              <ul className="space-y-1">
                {insight.action_items.slice(0, compact ? 2 : 3).map((item, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-start gap-1">
                    <span className="text-gray-400 mt-1">•</span>
                    <span>{item}</span>
                  </li>
                ))}
                {compact && insight.action_items.length > 2 && (
                  <li className="text-xs text-gray-500">
                    +{insight.action_items.length - 2} mais...
                  </li>
                )}
              </ul>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}