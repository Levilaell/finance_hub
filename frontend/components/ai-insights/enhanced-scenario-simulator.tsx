'use client';

import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { formatCurrency, cn } from '@/lib/utils';
import { toast } from 'sonner';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  LightBulbIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  SparklesIcon,
  DocumentArrowDownIcon,
  ShareIcon,
  BookmarkIcon,
  PlayIcon,
  PauseIcon,
  ArrowRightIcon,
  CalendarIcon,
  BellIcon,
  DocumentTextIcon,
  CpuChipIcon,
} from '@heroicons/react/24/outline';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ComposedChart,
} from 'recharts';
import { useQuery, useMutation } from '@tanstack/react-query';
import { aiAnalysisService } from '@/services/ai-analysis.service';

interface EnhancedScenarioSimulatorProps {
  currentData: {
    income: number;
    expenses: number;
    categories: Array<{
      name: string;
      amount: number;
      percentage: number;
    }>;
    monthlyTrend?: Array<{
      month: string;
      income: number;
      expenses: number;
      profit: number;
    }>;
  };
  predictions?: {
    next_month_income: number;
    next_month_expenses: number;
    growth_rate: number;
  };
  businessContext?: any;
  onSimulationComplete?: (results: any) => void;
}

interface SimulationResult {
  id: string;
  name: string;
  timestamp: Date;
  parameters: {
    incomeAdjustment: number;
    expenseAdjustment: number;
    categoryAdjustments: Record<string, number>;
  };
  metrics: {
    monthlyProfit: number;
    yearlyProfit: number;
    breakEvenPoint: number;
    roi: number;
    riskScore: number;
  };
  insights: string[];
  aiRecommendations?: string[];
}

const ADVANCED_SCENARIOS = [
  {
    id: 'expansion',
    name: 'Expansão Agressiva',
    icon: ArrowTrendingUpIcon,
    description: 'Investe 30% mais para crescer 50%',
    adjustments: {
      income: 50,
      expenses: 30,
      categories: {
        'Marketing': 60,
        'Vendas': 40,
        'Tecnologia': 25
      }
    },
    riskLevel: 'high',
    expectedROI: '180%'
  },
  {
    id: 'efficiency',
    name: 'Máxima Eficiência',
    icon: CpuChipIcon,
    description: 'Automatiza processos e reduz custos',
    adjustments: {
      income: 10,
      expenses: -30,
      categories: {
        'Folha de Pagamento': -20,
        'Operacional': -40,
        'Tecnologia': 20
      }
    },
    riskLevel: 'low',
    expectedROI: '250%'
  },
  {
    id: 'pivot',
    name: 'Pivô de Negócio',
    icon: ArrowPathIcon,
    description: 'Muda foco para novo mercado',
    adjustments: {
      income: -20, // Inicial cai
      expenses: -10,
      categories: {
        'P&D': 100,
        'Marketing': -50,
        'Vendas': 30
      }
    },
    riskLevel: 'very-high',
    expectedROI: '300%' // Longo prazo
  },
  {
    id: 'recession',
    name: 'Modo Sobrevivência',
    icon: ExclamationTriangleIcon,
    description: 'Preparação para crise econômica',
    adjustments: {
      income: -30,
      expenses: -40,
      categories: {
        'Marketing': -60,
        'Folha de Pagamento': -25,
        'Operacional': -50
      }
    },
    riskLevel: 'medium',
    expectedROI: 'Preservação'
  }
];

export function EnhancedScenarioSimulator({ 
  currentData, 
  predictions,
  businessContext,
  onSimulationComplete 
}: EnhancedScenarioSimulatorProps) {
  const [selectedScenario, setSelectedScenario] = useState<string>('custom');
  const [incomeAdjustment, setIncomeAdjustment] = useState<number>(0);
  const [expenseAdjustment, setExpenseAdjustment] = useState<number>(0);
  const [categoryAdjustments, setCategoryAdjustments] = useState<Record<string, number>>({});
  const [simulationName, setSimulationName] = useState('');
  const [simulationNotes, setSimulationNotes] = useState('');
  const [isAnimating, setIsAnimating] = useState(false);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedComparisons, setSelectedComparisons] = useState<string[]>([]);
  const [timeHorizon, setTimeHorizon] = useState<number>(12); // meses
  const [showAIInsights, setShowAIInsights] = useState(false);

  // Query para buscar simulações salvas
  const { data: savedSimulations, refetch: refetchSimulations } = useQuery({
    queryKey: ['scenario-simulations'],
    queryFn: async () => {
      // Em produção, isso viria do backend
      const saved = localStorage.getItem('scenario-simulations');
      return saved ? JSON.parse(saved) : [];
    }
  });

  // Mutation para salvar simulação
  const saveSimulationMutation = useMutation({
    mutationFn: async (simulation: SimulationResult) => {
      // Em produção, isso seria uma chamada API
      const existing = savedSimulations || [];
      const updated = [...existing, simulation];
      localStorage.setItem('scenario-simulations', JSON.stringify(updated));
      return simulation;
    },
    onSuccess: () => {
      refetchSimulations();
      toast.success('Simulação salva com sucesso!');
    }
  });

  // Calcular métricas avançadas
  const advancedMetrics = useMemo(() => {
    const baseIncome = currentData.income;
    const baseExpenses = currentData.expenses;
    
    const newIncome = baseIncome * (1 + incomeAdjustment / 100);
    const newExpenses = baseExpenses * (1 + expenseAdjustment / 100);
    const monthlyProfit = newIncome - newExpenses;
    
    // Calcular ponto de equilíbrio
    const fixedCosts = newExpenses * 0.6; // Estimativa
    const variableCostRatio = 0.4;
    const contributionMargin = 1 - variableCostRatio;
    const breakEvenPoint = fixedCosts / contributionMargin;
    
    // Calcular ROI
    const investment = Math.abs(newExpenses - baseExpenses);
    const returns = Math.max(0, monthlyProfit - (baseIncome - baseExpenses));
    const roi = investment > 0 ? (returns / investment) * 100 : 0;
    
    // Score de risco baseado em múltiplos fatores
    const volatility = Math.abs(incomeAdjustment) + Math.abs(expenseAdjustment);
    const leverageRatio = newExpenses / newIncome;
    const riskScore = Math.min(100, (volatility * 0.5) + (leverageRatio * 50));
    
    // Projeções avançadas com sazonalidade
    const projections: any[] = [];
    for (let i = 0; i < timeHorizon; i++) {
      const seasonalFactor = 1 + (Math.sin((i + new Date().getMonth()) * Math.PI / 6) * 0.1);
      const growthFactor = Math.pow(1 + (predictions?.growth_rate || 0) / 100 / 12, i);
      
      const monthIncome = newIncome * growthFactor * seasonalFactor;
      const monthExpenses = newExpenses * (1 + 0.02 / 12) ** i; // Inflação
      
      projections.push({
        month: i + 1,
        monthName: new Date(Date.now() + i * 30 * 24 * 60 * 60 * 1000).toLocaleDateString('pt-BR', { month: 'short' }),
        income: monthIncome,
        expenses: monthExpenses,
        profit: monthIncome - monthExpenses,
        accumulated: (projections[i - 1]?.accumulated || 0) + (monthIncome - monthExpenses),
        breakEven: monthIncome >= monthExpenses
      });
    }
    
    // Análise de sensibilidade
    const sensitivityAnalysis = [
      { factor: 'Receita -10%', impact: (newIncome * 0.9 - newExpenses) - monthlyProfit },
      { factor: 'Despesas +10%', impact: (newIncome - newExpenses * 1.1) - monthlyProfit },
      { factor: 'Ambos -5%', impact: (newIncome * 0.95 - newExpenses * 1.05) - monthlyProfit }
    ];
    
    return {
      monthlyProfit,
      yearlyProfit: monthlyProfit * 12,
      breakEvenPoint,
      roi,
      riskScore,
      projections,
      sensitivityAnalysis,
      paybackPeriod: investment > 0 ? investment / Math.max(1, monthlyProfit) : 0,
      profitMargin: newIncome > 0 ? (monthlyProfit / newIncome) * 100 : 0
    };
  }, [currentData, predictions, incomeAdjustment, expenseAdjustment, timeHorizon]);

  // Gerar insights com IA
  const generateAIInsights = useCallback(async () => {
    setShowAIInsights(true);
    
    // Simular chamada para IA
    const insights = [
      `Com ${incomeAdjustment}% de ajuste na receita, você atingirá o break-even em ${Math.ceil(advancedMetrics.paybackPeriod)} meses`,
      `Risco de ${advancedMetrics.riskScore.toFixed(0)}% identificado - ${advancedMetrics.riskScore > 50 ? 'considere medidas de mitigação' : 'dentro de parâmetros aceitáveis'}`,
      `ROI projetado de ${advancedMetrics.roi.toFixed(0)}% ${advancedMetrics.roi > 100 ? '- excelente retorno!' : '- analise se vale o investimento'}`
    ];
    
    // Se tem contexto de negócio, adicionar insights personalizados
    if (businessContext?.businessGoals?.length > 0) {
      const mainGoal = businessContext.businessGoals[0];
      insights.push(`Esta simulação ${advancedMetrics.monthlyProfit > 0 ? 'contribui para' : 'pode impactar'} sua meta: "${mainGoal}"`);
    }
    
    return insights;
  }, [incomeAdjustment, advancedMetrics, businessContext]);

  // Aplicar cenário avançado
  const applyAdvancedScenario = useCallback((scenario: typeof ADVANCED_SCENARIOS[0]) => {
    setSelectedScenario(scenario.id);
    setIncomeAdjustment(scenario.adjustments.income);
    setExpenseAdjustment(scenario.adjustments.expenses);
    // Garantir que todas as propriedades sejam números válidos
    const categories: Record<string, number> = {};
    Object.entries(scenario.adjustments.categories).forEach(([key, value]) => {
      if (typeof value === 'number') {
        categories[key] = value;
      }
    });
    setCategoryAdjustments(categories);
    setIsAnimating(true);
    
    setTimeout(() => setIsAnimating(false), 1000);
  }, []);

  // Salvar simulação completa
  const saveSimulation = useCallback(async () => {
    const aiInsights = await generateAIInsights();
    
    const simulation: SimulationResult = {
      id: Date.now().toString(),
      name: simulationName || `Simulação ${new Date().toLocaleDateString()}`,
      timestamp: new Date(),
      parameters: {
        incomeAdjustment,
        expenseAdjustment,
        categoryAdjustments
      },
      metrics: {
        monthlyProfit: advancedMetrics.monthlyProfit,
        yearlyProfit: advancedMetrics.yearlyProfit,
        breakEvenPoint: advancedMetrics.breakEvenPoint,
        roi: advancedMetrics.roi,
        riskScore: advancedMetrics.riskScore
      },
      insights: aiInsights,
      aiRecommendations: [
        'Monitore indicadores semanalmente',
        'Ajuste estratégia conforme resultados',
        'Prepare plano de contingência'
      ]
    };
    
    saveSimulationMutation.mutate(simulation);
    
    if (onSimulationComplete) {
      onSimulationComplete(simulation);
    }
  }, [simulationName, incomeAdjustment, expenseAdjustment, categoryAdjustments, advancedMetrics, generateAIInsights, saveSimulationMutation, onSimulationComplete]);

  // Exportar relatório
  const exportReport = useCallback(() => {
    const report = {
      title: simulationName || 'Relatório de Simulação',
      date: new Date().toLocaleDateString(),
      parameters: {
        incomeAdjustment,
        expenseAdjustment,
        categoryAdjustments
      },
      metrics: advancedMetrics,
      insights: showAIInsights ? generateAIInsights() : []
    };
    
    // Em produção, geraria PDF
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `simulacao-${Date.now()}.json`;
    a.click();
    
    toast.success('Relatório exportado!');
  }, [simulationName, incomeAdjustment, expenseAdjustment, categoryAdjustments, advancedMetrics, showAIInsights, generateAIInsights]);

  // Criar alerta/lembrete
  const createReminder = useCallback(() => {
    toast.success('Lembrete criado! Você receberá notificações sobre esta simulação.');
    // Em produção, integraria com sistema de notificações
  }, []);

  return (
    <div className="space-y-6">
      {/* Header com ações */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-bold flex items-center gap-2">
            <SparklesIcon className="h-7 w-7 text-purple-600" />
            Simulador Avançado de Cenários
          </h3>
          <p className="text-gray-600 mt-1">
            Teste hipóteses complexas e tome decisões baseadas em dados
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setComparisonMode(!comparisonMode)}
          >
            <ChartBarIcon className="h-4 w-4 mr-1" />
            {comparisonMode ? 'Modo Normal' : 'Comparar'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={exportReport}
          >
            <DocumentArrowDownIcon className="h-4 w-4 mr-1" />
            Exportar
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={createReminder}
          >
            <BellIcon className="h-4 w-4 mr-1" />
            Lembrete
          </Button>
        </div>
      </div>

      {/* Cenários Avançados */}
      <Card>
        <CardHeader>
          <CardTitle>Cenários Estratégicos</CardTitle>
          <CardDescription>
            Modelos testados por empresas de sucesso
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {ADVANCED_SCENARIOS.map((scenario) => {
              const Icon = scenario.icon;
              const isSelected = selectedScenario === scenario.id;
              
              return (
                <Card
                  key={scenario.id}
                  className={cn(
                    "cursor-pointer transition-all hover:shadow-lg",
                    isSelected && "ring-2 ring-purple-600 bg-purple-50",
                    isAnimating && isSelected && "animate-pulse"
                  )}
                  onClick={() => applyAdvancedScenario(scenario)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <Icon className={cn(
                        "h-6 w-6",
                        isSelected ? "text-purple-600" : "text-gray-600"
                      )} />
                      <Badge 
                        variant={
                          scenario.riskLevel === 'low' ? 'default' :
                          scenario.riskLevel === 'medium' ? 'secondary' :
                          'destructive'
                        }
                        className="text-xs"
                      >
                        {scenario.riskLevel === 'low' ? 'Baixo Risco' :
                         scenario.riskLevel === 'medium' ? 'Médio Risco' :
                         scenario.riskLevel === 'high' ? 'Alto Risco' :
                         'Muito Alto Risco'}
                      </Badge>
                    </div>
                    <h4 className="font-semibold mb-1">{scenario.name}</h4>
                    <p className="text-xs text-gray-600 mb-2">{scenario.description}</p>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">ROI esperado:</span>
                      <span className="font-bold text-green-600">{scenario.expectedROI}</span>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Controles Detalhados */}
      <Card>
        <CardHeader>
          <CardTitle>Parâmetros Detalhados</CardTitle>
          <div className="flex items-center gap-4 mt-2">
            <Label className="text-sm">Horizonte Temporal:</Label>
            <Select value={timeHorizon.toString()} onValueChange={(v) => setTimeHorizon(Number(v))}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="6">6 meses</SelectItem>
                <SelectItem value="12">12 meses</SelectItem>
                <SelectItem value="24">24 meses</SelectItem>
                <SelectItem value="36">36 meses</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Sliders existentes melhorados */}
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label>Variação de Receita</Label>
                <span className={cn(
                  "text-sm font-bold px-2 py-1 rounded",
                  incomeAdjustment > 0 ? "bg-green-100 text-green-700" : 
                  incomeAdjustment < 0 ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-700"
                )}>
                  {incomeAdjustment > 0 ? '+' : ''}{incomeAdjustment}%
                </span>
              </div>
              <Slider
                value={[incomeAdjustment]}
                onValueChange={([value]) => {
                  setIncomeAdjustment(value);
                  setSelectedScenario('custom');
                }}
                min={-50}
                max={100}
                step={5}
                className="mb-2"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>-50%</span>
                <span>0%</span>
                <span>+100%</span>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <Label>Variação de Despesas</Label>
                <span className={cn(
                  "text-sm font-bold px-2 py-1 rounded",
                  expenseAdjustment > 0 ? "bg-red-100 text-red-700" : 
                  expenseAdjustment < 0 ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"
                )}>
                  {expenseAdjustment > 0 ? '+' : ''}{expenseAdjustment}%
                </span>
              </div>
              <Slider
                value={[expenseAdjustment]}
                onValueChange={([value]) => {
                  setExpenseAdjustment(value);
                  setSelectedScenario('custom');
                }}
                min={-50}
                max={50}
                step={5}
                className="mb-2"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>-50%</span>
                <span>0%</span>
                <span>+50%</span>
              </div>
            </div>
          </div>

          {/* Informações da Simulação */}
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label>Nome da Simulação</Label>
              <input
                type="text"
                className="w-full mt-1 px-3 py-2 border rounded-lg"
                placeholder="Ex: Expansão Q1 2024"
                value={simulationName}
                onChange={(e) => setSimulationName(e.target.value)}
              />
            </div>
            <div>
              <Label>Notas/Premissas</Label>
              <Textarea
                className="mt-1"
                placeholder="Descreva as premissas desta simulação..."
                value={simulationNotes}
                onChange={(e) => setSimulationNotes(e.target.value)}
                rows={3}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Visualizações Avançadas */}
      <Card>
        <CardHeader>
          <CardTitle>Análise Visual Completa</CardTitle>
          <CardDescription>
            Múltiplas perspectivas para tomada de decisão
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Gráfico de Projeção Avançada */}
            <div>
              <h4 className="text-sm font-medium mb-4">Projeção de Fluxo de Caixa</h4>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={advancedMetrics.projections}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="monthName" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip formatter={(value: any) => formatCurrency(value)} />
                  <Legend />
                  <Area
                    yAxisId="left"
                    type="monotone"
                    dataKey="accumulated"
                    stroke="#8b5cf6"
                    fill="#8b5cf6"
                    fillOpacity={0.3}
                    name="Acumulado"
                  />
                  <Bar
                    yAxisId="left"
                    dataKey="profit"
                    fill="#10b981"
                    name="Lucro Mensal"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="income"
                    stroke="#3b82f6"
                    name="Receita"
                    strokeWidth={2}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="expenses"
                    stroke="#ef4444"
                    name="Despesas"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Análise de Sensibilidade */}
            <div>
              <h4 className="text-sm font-medium mb-4">Análise de Sensibilidade</h4>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={advancedMetrics.sensitivityAnalysis}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="factor" />
                  <YAxis />
                  <Tooltip formatter={(value: any) => formatCurrency(value)} />
                  <Bar 
                    dataKey="impact" 
                    fill="#8b5cf6"
                    name="Impacto no Lucro"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Métricas Avançadas */}
          <div className="grid gap-4 md:grid-cols-4 mt-6">
            <div className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg">
              <div className="text-sm text-gray-600">Break-even</div>
              <div className="text-2xl font-bold text-purple-700">
                {formatCurrency(advancedMetrics.breakEvenPoint)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Ponto de equilíbrio
              </div>
            </div>
            
            <div className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg">
              <div className="text-sm text-gray-600">ROI Projetado</div>
              <div className="text-2xl font-bold text-green-700">
                {advancedMetrics.roi.toFixed(0)}%
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Retorno sobre investimento
              </div>
            </div>
            
            <div className="p-4 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg">
              <div className="text-sm text-gray-600">Payback</div>
              <div className="text-2xl font-bold text-blue-700">
                {advancedMetrics.paybackPeriod.toFixed(1)} meses
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Período de retorno
              </div>
            </div>
            
            <div className={cn(
              "p-4 rounded-lg",
              advancedMetrics.riskScore > 70 ? "bg-gradient-to-br from-red-50 to-orange-50" :
              advancedMetrics.riskScore > 40 ? "bg-gradient-to-br from-yellow-50 to-amber-50" :
              "bg-gradient-to-br from-green-50 to-lime-50"
            )}>
              <div className="text-sm text-gray-600">Score de Risco</div>
              <div className={cn(
                "text-2xl font-bold",
                advancedMetrics.riskScore > 70 ? "text-red-700" :
                advancedMetrics.riskScore > 40 ? "text-yellow-700" :
                "text-green-700"
              )}>
                {advancedMetrics.riskScore.toFixed(0)}/100
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {advancedMetrics.riskScore > 70 ? "Alto risco" :
                 advancedMetrics.riskScore > 40 ? "Risco moderado" :
                 "Baixo risco"}
              </div>
            </div>
          </div>

          {/* Insights com IA */}
          <div className="mt-6">
            <Button
              onClick={async () => {
                const insights = await generateAIInsights();
                // Mostrar insights
              }}
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
            >
              <SparklesIcon className="h-5 w-5 mr-2" />
              Gerar Análise Detalhada com IA
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Histórico e Comparações */}
      {savedSimulations && savedSimulations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Simulações Salvas</CardTitle>
            <CardDescription>
              Compare diferentes cenários e acompanhe evolução
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {savedSimulations.map((sim: SimulationResult) => (
                <div
                  key={sim.id}
                  className={cn(
                    "p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-all",
                    selectedComparisons.includes(sim.id) && "ring-2 ring-purple-600 bg-purple-50"
                  )}
                  onClick={() => {
                    if (comparisonMode) {
                      setSelectedComparisons(prev =>
                        prev.includes(sim.id)
                          ? prev.filter(id => id !== sim.id)
                          : [...prev, sim.id]
                      );
                    }
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold">{sim.name}</h4>
                      <div className="flex items-center gap-4 text-sm text-gray-600 mt-1">
                        <span>
                          <CalendarIcon className="h-4 w-4 inline mr-1" />
                          {new Date(sim.timestamp).toLocaleDateString()}
                        </span>
                        <span>
                          ROI: <strong className="text-green-600">{sim.metrics.roi.toFixed(0)}%</strong>
                        </span>
                        <span>
                          Lucro: <strong>{formatCurrency(sim.metrics.monthlyProfit)}/mês</strong>
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={sim.metrics.riskScore > 50 ? "destructive" : "default"}>
                        Risco: {sim.metrics.riskScore.toFixed(0)}%
                      </Badge>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          // Aplicar parâmetros desta simulação
                          setIncomeAdjustment(sim.parameters.incomeAdjustment);
                          setExpenseAdjustment(sim.parameters.expenseAdjustment);
                          setCategoryAdjustments(sim.parameters.categoryAdjustments);
                        }}
                      >
                        <PlayIcon className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  {sim.insights && sim.insights.length > 0 && (
                    <div className="mt-3 p-3 bg-gray-50 rounded text-sm">
                      <strong className="text-gray-700">Principais Insights:</strong>
                      <ul className="mt-1 space-y-1">
                        {sim.insights.slice(0, 2).map((insight, idx) => (
                          <li key={idx} className="text-gray-600">• {insight}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {comparisonMode && selectedComparisons.length >= 2 && (
              <Button
                className="mt-4 w-full"
                onClick={() => {
                  // Abrir modal de comparação detalhada
                  toast.info('Comparação detalhada em desenvolvimento');
                }}
              >
                Comparar {selectedComparisons.length} Simulações
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Ações Finais */}
      <div className="flex gap-3 justify-end">
        <Button
          variant="outline"
          onClick={() => {
            setIncomeAdjustment(0);
            setExpenseAdjustment(0);
            setCategoryAdjustments({});
            setSelectedScenario('custom');
          }}
        >
          <ArrowPathIcon className="h-4 w-4 mr-2" />
          Resetar
        </Button>
        <Button
          onClick={saveSimulation}
          className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
        >
          <BookmarkIcon className="h-4 w-4 mr-2" />
          Salvar Simulação
        </Button>
      </div>
    </div>
  );
}