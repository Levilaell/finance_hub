'use client';

import { useState } from 'react';
import { InsightCard } from './InsightCard';
import { AIInsight } from '../types/ai-insights.types';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Loader2 } from 'lucide-react';
import { testId, TEST_IDS } from '@/utils/test-helpers';

interface InsightsListProps {
  insights: AIInsight[];
  loading?: boolean;
  onInsightAction?: (insightId: string, action: 'complete' | 'dismiss') => void;
}

export function InsightsList({ insights, loading, onInsightAction }: InsightsListProps) {
  const [activeTab, setActiveTab] = useState('all');

  // Group insights by status
  const newInsights = insights.filter(i => i.status === 'new');
  const viewedInsights = insights.filter(i => i.status === 'viewed');
  const inProgressInsights = insights.filter(i => i.status === 'in_progress');
  const completedInsights = insights.filter(i => i.status === 'completed');

  // Filter by priority for the active tab
  const getFilteredInsights = () => {
    switch (activeTab) {
      case 'critical':
        return insights.filter(i => i.priority === 'critical' && i.status !== 'completed' && i.status !== 'dismissed');
      case 'high':
        return insights.filter(i => i.priority === 'high' && i.status !== 'completed' && i.status !== 'dismissed');
      case 'pending':
        return insights.filter(i => i.status !== 'completed' && i.status !== 'dismissed');
      case 'completed':
        return completedInsights;
      default:
        return insights;
    }
  };

  const filteredInsights = getFilteredInsights();

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Carregando insights...</p>
        </div>
      </div>
    );
  }

  if (insights.length === 0) {
    return (
      <div className="text-center p-8">
        <p className="text-gray-500">Nenhum insight disponível no momento.</p>
        <p className="text-sm text-gray-400 mt-2">
          Continue conversando com o AI para receber recomendações personalizadas.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6" {...testId(TEST_IDS.aiInsights.insightsList)}>
      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4" {...testId(TEST_IDS.aiInsights.insightsStats)}>
        <Card className="border-border">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Novos</p>
            <p className="text-2xl font-bold text-foreground">{newInsights.length}</p>
            <p className="text-xs text-info-subtle mt-1">Aguardando ação</p>
          </CardContent>
        </Card>
        <Card className="border-border">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Em Progresso</p>
            <p className="text-2xl font-bold text-foreground">{inProgressInsights.length}</p>
            <p className="text-xs text-warning-subtle mt-1">Em andamento</p>
          </CardContent>
        </Card>
        <Card className="border-border">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Concluídos</p>
            <p className="text-2xl font-bold text-foreground">{completedInsights.length}</p>
            <p className="text-xs text-success-subtle mt-1">Finalizados</p>
          </CardContent>
        </Card>
        <Card className="border-border">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Taxa de Conclusão</p>
            <p className="text-2xl font-bold text-foreground">
              {insights.length > 0 
                ? Math.round((completedInsights.length / insights.length) * 100) 
                : 0}%
            </p>
            <Progress 
              value={insights.length > 0 ? (completedInsights.length / insights.length) * 100 : 0} 
              className="h-1 mt-2" 
            />
          </CardContent>
        </Card>
      </div>

      {/* Tabs for filtering */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="w-full">
          <TabsTrigger value="all" className="flex items-center gap-2" {...testId(TEST_IDS.aiInsights.insightsTabAll)}>
            Todos
            <Badge variant="secondary" className="text-xs">
              {insights.length}
            </Badge>
          </TabsTrigger>
          <TabsTrigger value="critical" className="flex items-center gap-2" {...testId(TEST_IDS.aiInsights.insightsTabCritical)}>
            Crítico
            <Badge variant="destructive" className="text-xs">
              {insights.filter(i => i.priority === 'critical' && i.status !== 'completed').length}
            </Badge>
          </TabsTrigger>
          <TabsTrigger value="high" className="flex items-center gap-2" {...testId(TEST_IDS.aiInsights.insightsTabHigh)}>
            Alta Prioridade
            <Badge variant="secondary" className="text-xs">
              {insights.filter(i => i.priority === 'high' && i.status !== 'completed').length}
            </Badge>
          </TabsTrigger>
          <TabsTrigger value="pending" className="flex items-center gap-2" {...testId(TEST_IDS.aiInsights.insightsTabPending)}>
            Pendentes
            <Badge variant="secondary" className="text-xs">
              {insights.filter(i => i.status !== 'completed' && i.status !== 'dismissed').length}
            </Badge>
          </TabsTrigger>
          <TabsTrigger value="completed" className="flex items-center gap-2" {...testId(TEST_IDS.aiInsights.insightsTabCompleted)}>
            Concluídos
            <Badge variant="secondary" className="text-xs">
              {completedInsights.length}
            </Badge>
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-4 mt-6">
          {filteredInsights.length === 0 ? (
            <p className="text-center text-gray-500 py-8">
              Nenhum insight nesta categoria.
            </p>
          ) : (
            filteredInsights.map((insight) => (
              <InsightCard
                key={insight.id}
                insight={insight}
                onAction={onInsightAction}
              />
            ))
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}