'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';
import {
  BellIcon,
  SparklesIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  LightBulbIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ClockIcon,
  CalendarIcon,
  ChartBarIcon,
  BoltIcon,
  FireIcon,
  ShieldCheckIcon,
  ArrowRightIcon,
  XMarkIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';

interface ProactiveInsight {
  id: string;
  type: 'alert' | 'opportunity' | 'achievement' | 'recommendation' | 'prediction';
  priority: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  metric?: {
    value: number | string;
    change?: number;
    trend?: 'up' | 'down' | 'stable';
  };
  action?: {
    label: string;
    handler: () => void;
  };
  timeframe?: string;
  impact?: string;
  category: string;
  isNew?: boolean;
  expiresAt?: Date;
}

interface ProactiveInsightsSystemProps {
  financialData: any;
  businessContext?: any;
  onActionTaken?: (insight: ProactiveInsight) => void;
}

export function ProactiveInsightsSystem({ 
  financialData, 
  businessContext,
  onActionTaken 
}: ProactiveInsightsSystemProps) {
  const [insights, setInsights] = useState<ProactiveInsight[]>([]);
  const [dismissedInsights, setDismissedInsights] = useState<string[]>([]);
  const [activeFilter, setActiveFilter] = useState<string>('all');
  const [showNotifications, setShowNotifications] = useState(true);
  const [insightStats, setInsightStats] = useState({
    total: 0,
    acted: 0,
    dismissed: 0,
    successRate: 0
  });

  // Gerar insights proativos baseados em análise em tempo real
  useEffect(() => {
    const generateProactiveInsights = () => {
      const newInsights: ProactiveInsight[] = [];
      
      // Análise de tendências
      if (financialData?.expenses > financialData?.income * 0.9) {
        newInsights.push({
          id: 'high-expense-ratio',
          type: 'alert',
          priority: 'high',
          title: 'Despesas próximas do limite crítico',
          description: 'Suas despesas estão consumindo 90% da receita. Ação imediata necessária.',
          metric: {
            value: `${((financialData.expenses / financialData.income) * 100).toFixed(0)}%`,
            trend: 'up'
          },
          action: {
            label: 'Ver plano de redução',
            handler: () => toast.info('Abrindo plano de redução de custos...')
          },
          category: 'financial_health',
          isNew: true
        });
      }
      
      // Oportunidades baseadas em padrões
      const topCategory = financialData?.top_expense_categories?.[0];
      if (topCategory && topCategory.percentage > 30) {
        newInsights.push({
          id: `optimize-${topCategory.name}`,
          type: 'opportunity',
          priority: 'medium',
          title: `Oportunidade de economia em ${topCategory.name}`,
          description: `Esta categoria representa ${topCategory.percentage.toFixed(0)}% dos gastos. Análise indica potencial de redução de 15%.`,
          metric: {
            value: `R$ ${(topCategory.amount * 0.15).toFixed(2)}`,
            trend: 'down'
          },
          action: {
            label: 'Analisar fornecedores',
            handler: () => toast.info('Análise de fornecedores iniciada...')
          },
          impact: 'Economia mensal estimada',
          category: 'cost_optimization',
          isNew: true
        });
      }
      
      // Conquistas e marcos
      if (financialData?.net_flow > 0) {
        const profitMargin = (financialData.net_flow / financialData.income) * 100;
        if (profitMargin > 20) {
          newInsights.push({
            id: 'high-profit-achievement',
            type: 'achievement',
            priority: 'low',
            title: 'Excelente margem de lucro! 🎉',
            description: `Margem de ${profitMargin.toFixed(1)}% está acima da média do mercado.`,
            metric: {
              value: `${profitMargin.toFixed(1)}%`,
              trend: 'up'
            },
            category: 'achievements',
            isNew: true
          });
        }
      }
      
      // Previsões e alertas futuros
      if (businessContext?.seasonality) {
        newInsights.push({
          id: 'seasonal-alert',
          type: 'prediction',
          priority: 'medium',
          title: 'Prepare-se para variação sazonal',
          description: businessContext.seasonality,
          timeframe: 'Próximos 30 dias',
          action: {
            label: 'Criar plano sazonal',
            handler: () => toast.info('Criando plano sazonal...')
          },
          category: 'planning',
          isNew: true
        });
      }
      
      // Recomendações personalizadas baseadas em metas
      if (businessContext?.businessGoals?.length > 0) {
        const mainGoal = businessContext.businessGoals[0];
        newInsights.push({
          id: `goal-${mainGoal.toLowerCase().replace(/\s/g, '-')}`,
          type: 'recommendation',
          priority: 'high',
          title: 'Ação para alcançar sua meta',
          description: `Para "${mainGoal}", recomendamos focar em aumentar receita recorrente.`,
          action: {
            label: 'Ver estratégias',
            handler: () => toast.info('Carregando estratégias personalizadas...')
          },
          category: 'goals',
          isNew: true,
          expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 dias
        });
      }
      
      // Alertas de segurança financeira
      const monthsOfRunway = financialData?.income > 0 ? 
        (financialData.balance || 0) / (financialData.expenses - financialData.income) : 0;
      
      if (monthsOfRunway > 0 && monthsOfRunway < 3) {
        newInsights.push({
          id: 'low-runway',
          type: 'alert',
          priority: 'critical',
          title: 'Atenção: Runway baixo',
          description: `Apenas ${monthsOfRunway.toFixed(1)} meses de operação com recursos atuais.`,
          metric: {
            value: `${monthsOfRunway.toFixed(1)} meses`,
            trend: 'down'
          },
          action: {
            label: 'Plano de emergência',
            handler: () => toast.error('Abrindo plano de contingência...')
          },
          category: 'risk_management',
          isNew: true
        });
      }
      
      setInsights(newInsights.filter(i => !dismissedInsights.includes(i.id)));
    };
    
    // Gerar insights iniciais
    generateProactiveInsights();
    
    // Atualizar periodicamente (em produção seria via WebSocket)
    const interval = setInterval(generateProactiveInsights, 60000); // 1 minuto
    
    return () => clearInterval(interval);
  }, [financialData, businessContext, dismissedInsights]);

  // Calcular estatísticas
  useEffect(() => {
    const total = insights.length + dismissedInsights.length;
    const acted = insights.filter(i => i.action && dismissedInsights.includes(i.id)).length;
    const dismissed = dismissedInsights.length;
    const successRate = total > 0 ? (acted / total) * 100 : 0;
    
    setInsightStats({ total, acted, dismissed, successRate });
  }, [insights, dismissedInsights]);

  const getInsightIcon = (type: ProactiveInsight['type']) => {
    switch (type) {
      case 'alert': return ExclamationTriangleIcon;
      case 'opportunity': return ArrowTrendingUpIcon;
      case 'achievement': return CheckCircleIcon;
      case 'recommendation': return LightBulbIcon;
      case 'prediction': return ChartBarIcon;
    }
  };

  const getPriorityColor = (priority: ProactiveInsight['priority']) => {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
    }
  };

  const dismissInsight = (id: string) => {
    setDismissedInsights([...dismissedInsights, id]);
    setInsights(insights.filter(i => i.id !== id));
    toast.success('Insight arquivado');
  };

  const handleAction = (insight: ProactiveInsight) => {
    if (insight.action) {
      insight.action.handler();
      if (onActionTaken) {
        onActionTaken(insight);
      }
      dismissInsight(insight.id);
    }
  };

  const filteredInsights = insights.filter(insight => {
    if (activeFilter === 'all') return true;
    return insight.type === activeFilter;
  });

  const filters = [
    { id: 'all', label: 'Todos', count: insights.length },
    { id: 'alert', label: 'Alertas', count: insights.filter(i => i.type === 'alert').length },
    { id: 'opportunity', label: 'Oportunidades', count: insights.filter(i => i.type === 'opportunity').length },
    { id: 'recommendation', label: 'Recomendações', count: insights.filter(i => i.type === 'recommendation').length },
  ];

  return (
    <div className="space-y-6">
      {/* Header com estatísticas */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <BellIcon className="h-6 w-6 text-purple-600" />
                Central de Insights Proativos
              </CardTitle>
              <p className="text-sm text-gray-600 mt-1">
                Monitoramento inteligente 24/7 com IA
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowNotifications(!showNotifications)}
            >
              {showNotifications ? 'Ocultar' : 'Mostrar'} Notificações
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{insights.length}</div>
              <div className="text-sm text-gray-600">Insights Ativos</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{insightStats.acted}</div>
              <div className="text-sm text-gray-600">Ações Tomadas</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">{insightStats.dismissed}</div>
              <div className="text-sm text-gray-600">Arquivados</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{insightStats.successRate.toFixed(0)}%</div>
              <div className="text-sm text-gray-600">Taxa de Ação</div>
              <Progress value={insightStats.successRate} className="mt-2" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filtros */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {filters.map(filter => (
          <Button
            key={filter.id}
            variant={activeFilter === filter.id ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveFilter(filter.id)}
            className="whitespace-nowrap"
          >
            {filter.label}
            {filter.count > 0 && (
              <Badge variant="secondary" className="ml-2">
                {filter.count}
              </Badge>
            )}
          </Button>
        ))}
      </div>

      {/* Lista de Insights com animações */}
      <AnimatePresence mode="wait">
        {showNotifications && filteredInsights.length > 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-4"
          >
            {filteredInsights.map((insight, index) => {
              const Icon = getInsightIcon(insight.type);
              
              return (
                <motion.div
                  key={insight.id}
                  initial={{ opacity: 0, x: -50 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ scale: 1.02 }}
                  className={cn(
                    "relative overflow-hidden rounded-lg border-2 p-4 transition-all",
                    getPriorityColor(insight.priority),
                    insight.isNew && "ring-2 ring-purple-400 ring-offset-2"
                  )}
                >
                  {/* Indicador de novo */}
                  {insight.isNew && (
                    <div className="absolute top-0 right-0 bg-purple-600 text-white text-xs px-2 py-1 rounded-bl-lg">
                      NOVO
                    </div>
                  )}

                  <div className="flex items-start gap-4">
                    {/* Ícone */}
                    <div className={cn(
                      "p-3 rounded-full",
                      insight.type === 'alert' && "bg-red-100",
                      insight.type === 'opportunity' && "bg-green-100",
                      insight.type === 'achievement' && "bg-blue-100",
                      insight.type === 'recommendation' && "bg-purple-100",
                      insight.type === 'prediction' && "bg-yellow-100"
                    )}>
                      <Icon className="h-6 w-6" />
                    </div>

                    {/* Conteúdo */}
                    <div className="flex-1">
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-semibold text-lg">{insight.title}</h4>
                          <p className="text-sm mt-1 opacity-90">{insight.description}</p>
                          
                          {/* Métricas */}
                          {insight.metric && (
                            <div className="flex items-center gap-4 mt-3">
                              <div className="flex items-center gap-2">
                                <span className="text-2xl font-bold">{insight.metric.value}</span>
                                {insight.metric.trend && (
                                  <>
                                    {insight.metric.trend === 'up' && <ArrowTrendingUpIcon className="h-5 w-5 text-green-500" />}
                                    {insight.metric.trend === 'down' && <ArrowTrendingDownIcon className="h-5 w-5 text-red-500" />}
                                  </>
                                )}
                              </div>
                              {insight.impact && (
                                <span className="text-sm text-gray-600">{insight.impact}</span>
                              )}
                            </div>
                          )}
                          
                          {/* Timeframe */}
                          {insight.timeframe && (
                            <div className="flex items-center gap-1 mt-2 text-sm text-gray-600">
                              <ClockIcon className="h-4 w-4" />
                              {insight.timeframe}
                            </div>
                          )}
                        </div>

                        {/* Botão de fechar */}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => dismissInsight(insight.id)}
                          className="opacity-60 hover:opacity-100"
                        >
                          <XMarkIcon className="h-4 w-4" />
                        </Button>
                      </div>

                      {/* Ação */}
                      {insight.action && (
                        <div className="mt-4">
                          <Button
                            onClick={() => handleAction(insight)}
                            size="sm"
                            className={cn(
                              "group",
                              insight.priority === 'critical' && "bg-red-600 hover:bg-red-700",
                              insight.priority === 'high' && "bg-orange-600 hover:bg-orange-700",
                              insight.priority === 'medium' && "bg-yellow-600 hover:bg-yellow-700",
                              insight.priority === 'low' && "bg-green-600 hover:bg-green-700"
                            )}
                          >
                            {insight.action.label}
                            <ChevronRightIcon className="h-4 w-4 ml-1 group-hover:translate-x-1 transition-transform" />
                          </Button>
                        </div>
                      )}

                      {/* Expiração */}
                      {insight.expiresAt && (
                        <div className="mt-3 text-xs text-gray-500">
                          Expira em {Math.ceil((insight.expiresAt.getTime() - Date.now()) / (1000 * 60 * 60 * 24))} dias
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        ) : showNotifications ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <CheckCircleIcon className="h-16 w-16 mx-auto text-green-500 mb-4" />
            <h3 className="text-lg font-medium text-gray-900">Tudo em dia!</h3>
            <p className="text-gray-600 mt-1">
              Nenhum insight pendente no momento. Continue o ótimo trabalho!
            </p>
          </motion.div>
        ) : null}
      </AnimatePresence>

      {/* Configurações de notificação */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Configurações de Notificação</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <label className="flex items-center justify-between">
              <span className="text-sm">Alertas críticos</span>
              <input type="checkbox" defaultChecked className="toggle" />
            </label>
            <label className="flex items-center justify-between">
              <span className="text-sm">Oportunidades de economia</span>
              <input type="checkbox" defaultChecked className="toggle" />
            </label>
            <label className="flex items-center justify-between">
              <span className="text-sm">Conquistas e marcos</span>
              <input type="checkbox" defaultChecked className="toggle" />
            </label>
            <label className="flex items-center justify-between">
              <span className="text-sm">Previsões semanais</span>
              <input type="checkbox" defaultChecked className="toggle" />
            </label>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}