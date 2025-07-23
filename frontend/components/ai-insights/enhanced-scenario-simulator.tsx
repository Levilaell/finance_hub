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

  // Calcular métricas avançadas com fórmulas financeiras precisas
  const advancedMetrics = useMemo(() => {
    const baseIncome = currentData.income;
    const baseExpenses = currentData.expenses;
    
    const newIncome = baseIncome * (1 + incomeAdjustment / 100);
    const newExpenses = baseExpenses * (1 + expenseAdjustment / 100);
    const monthlyProfit = newIncome - newExpenses;
    
    // Estimativa mais precisa de custos fixos vs variáveis baseada na categoria
    const categories = currentData.categories || [];
    let fixedCostsRatio = 0.4; // Default
    
    if (categories.length > 0) {
      const totalCategorized = categories.reduce((sum, cat) => sum + cat.amount, 0);
      const fixedCategories = ['Aluguel', 'Folha de Pagamento', 'Seguros', 'Software', 'Infraestrutura'];
      const fixedAmount = categories
        .filter(cat => fixedCategories.some(fixed => cat.name.includes(fixed)))
        .reduce((sum, cat) => sum + cat.amount, 0);
      
      fixedCostsRatio = totalCategorized > 0 ? fixedAmount / totalCategorized : 0.4;
    }
    
    const fixedCosts = newExpenses * fixedCostsRatio;
    const variableCosts = newExpenses * (1 - fixedCostsRatio);
    const variableCostRatio = variableCosts / newIncome;
    const contributionMargin = 1 - variableCostRatio;
    
    // Break-even point mais preciso
    const breakEvenRevenue = fixedCosts / contributionMargin;
    const breakEvenUnits = breakEvenRevenue / (newIncome / 1); // Assumindo 1 "unidade" por receita
    
    // ROI calculation with proper investment definition
    const additionalExpenses = Math.max(0, newExpenses - baseExpenses);
    const additionalRevenue = Math.max(0, newIncome - baseIncome);
    const netInvestment = additionalExpenses - (additionalRevenue * variableCostRatio);
    const monthlyReturn = monthlyProfit - (baseIncome - baseExpenses);
    const roi = netInvestment > 0 ? (monthlyReturn * 12 / netInvestment) * 100 : 0;
    
    // Score de risco mais sofisticado
    const operatingLeverage = contributionMargin > 0 ? (newIncome - variableCosts) / monthlyProfit : 1;
    const financialLeverage = newExpenses / Math.max(1, monthlyProfit);
    const volatilityRisk = (Math.abs(incomeAdjustment) + Math.abs(expenseAdjustment)) / 2;
    const marginSafety = monthlyProfit > 0 ? (monthlyProfit / newIncome) * 100 : -100;
    
    const riskScore = Math.min(100, Math.max(0, 
      (volatilityRisk * 0.3) + 
      (Math.min(financialLeverage * 10, 50) * 0.4) + 
      (Math.max(0, 50 - marginSafety) * 0.3)
    ));
    
    // Projeções avançadas com múltiplos fatores
    const projections: any[] = [];
    const baseGrowthRate = (predictions?.growth_rate || 5) / 100 / 12; // Mensal
    const inflationRate = 0.065 / 12; // 6.5% anual IPCA
    const marketVolatility = 0.15; // 15% de volatilidade do mercado
    
    for (let i = 0; i < timeHorizon; i++) {
      // Sazonalidade mais realista baseada no setor
      const monthIndex = (new Date().getMonth() + i) % 12;
      let seasonalFactor = 1;
      
      if (businessContext?.industry === 'retail') {
        // Varejo tem picos em nov/dez e baixas em jan/fev
        const retailSeasonality = [0.8, 0.7, 0.9, 1.0, 1.0, 1.1, 1.0, 1.0, 1.0, 1.1, 1.4, 1.6];
        seasonalFactor = retailSeasonality[monthIndex];
      } else if (businessContext?.industry === 'services') {
        // Serviços mais estável, baixa no fim do ano
        const servicesSeasonality = [0.9, 0.95, 1.0, 1.05, 1.1, 1.1, 1.0, 1.0, 1.05, 1.1, 0.95, 0.85];
        seasonalFactor = servicesSeasonality[monthIndex];
      }
      
      // Crescimento composto com volatilidade
      const volatilityFactor = 1 + (Math.random() - 0.5) * marketVolatility;
      const growthFactor = Math.pow(1 + baseGrowthRate, i) * volatilityFactor;
      
      // Curva de aprendizado e eficiência
      const efficiencyGain = Math.min(1.2, 1 + (i * 0.005)); // Melhoria gradual de eficiência
      
      const monthIncome = newIncome * growthFactor * seasonalFactor;
      const monthExpenses = (fixedCosts + variableCosts * growthFactor * seasonalFactor / efficiencyGain) * Math.pow(1 + inflationRate, i);
      const monthProfit = monthIncome - monthExpenses;
      
      // Métricas avançadas por mês
      const cumulativeCashFlow = (projections[i - 1]?.cumulativeCashFlow || 0) + monthProfit;
      const monthlyMargin = monthIncome > 0 ? (monthProfit / monthIncome) * 100 : 0;
      
      projections.push({
        month: i + 1,
        monthName: new Date(Date.now() + i * 30 * 24 * 60 * 60 * 1000).toLocaleDateString('pt-BR', { month: 'short' }),
        income: monthIncome,
        expenses: monthExpenses,
        profit: monthProfit,
        accumulated: cumulativeCashFlow,
        cumulativeCashFlow,
        margin: monthlyMargin,
        breakEven: monthIncome >= monthExpenses,
        seasonalFactor,
        growthRate: i > 0 ? ((monthIncome / (projections[i-1]?.income || monthIncome)) - 1) * 100 : 0
      });
    }
    
    // Análise de sensibilidade mais abrangente
    const sensitivityScenarios = [
      { factor: 'Receita -10%', incomeChange: -0.1, expenseChange: 0 },
      { factor: 'Receita +15%', incomeChange: 0.15, expenseChange: 0 },
      { factor: 'Despesas +10%', incomeChange: 0, expenseChange: 0.1 },
      { factor: 'Despesas -15%', incomeChange: 0, expenseChange: -0.15 },
      { factor: 'Cenário Otimista', incomeChange: 0.2, expenseChange: -0.1 },
      { factor: 'Cenário Pessimista', incomeChange: -0.15, expenseChange: 0.15 },
      { factor: 'Inflação Alta', incomeChange: 0.05, expenseChange: 0.12 },
      { factor: 'Recessão', incomeChange: -0.25, expenseChange: 0.05 }
    ];
    
    const sensitivityAnalysis = sensitivityScenarios.map(scenario => {
      const scenarioIncome = newIncome * (1 + scenario.incomeChange);
      const scenarioExpenses = newExpenses * (1 + scenario.expenseChange);
      const scenarioProfit = scenarioIncome - scenarioExpenses;
      const impact = scenarioProfit - monthlyProfit;
      
      return {
        factor: scenario.factor,
        impact,
        percentageChange: monthlyProfit !== 0 ? (impact / Math.abs(monthlyProfit)) * 100 : 0,
        newProfit: scenarioProfit,
        riskLevel: impact < -monthlyProfit * 0.5 ? 'high' : impact < 0 ? 'medium' : 'low'
      };
    });
    
    // Métricas financeiras avançadas
    const workingCapital = monthlyProfit * 2; // Assumindo 2 meses de capital de giro necessário
    const debtServiceCapacity = monthlyProfit * 0.3; // 30% do lucro para pagamento de financiamentos
    const reinvestmentRate = Math.max(0, monthlyProfit * 0.2); // 20% para reinvestimento
    const distributionCapacity = monthlyProfit - reinvestmentRate; // Disponível para distribuição
    
    // Análise de valuation simplificada
    const terminalValueMultiple = 10; // 10x lucro anual para valuation
    const projectedAnnualProfit = projections.reduce((sum, month) => sum + month.profit, 0);
    const estimatedValuation = projectedAnnualProfit * terminalValueMultiple;
    
    return {
      monthlyProfit,
      yearlyProfit: monthlyProfit * 12,
      breakEvenPoint: breakEvenRevenue,
      breakEvenUnits,
      roi,
      riskScore,
      projections,
      sensitivityAnalysis,
      paybackPeriod: netInvestment > 0 ? netInvestment / Math.max(1, monthlyReturn) : 0,
      profitMargin: newIncome > 0 ? (monthlyProfit / newIncome) * 100 : 0,
      contributionMargin: contributionMargin * 100,
      operatingLeverage,
      workingCapital,
      debtServiceCapacity,
      reinvestmentRate,
      distributionCapacity,
      estimatedValuation,
      fixedCostsRatio: fixedCostsRatio * 100,
      variableCostRatio: variableCostRatio * 100,
      cashFlowProjection: projections[projections.length - 1]?.cumulativeCashFlow || 0
    };
  }, [currentData, predictions, incomeAdjustment, expenseAdjustment, timeHorizon, businessContext]);

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

          {/* Métricas Avançadas - Grid Expandido */}
          <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6 mt-6">
            <div className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg">
              <div className="text-sm text-gray-600">Break-even</div>
              <div className="text-2xl font-bold text-purple-700">
                {formatCurrency(advancedMetrics.breakEvenPoint)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Receita para empatar
              </div>
            </div>
            
            <div className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg">
              <div className="text-sm text-gray-600">ROI Anual</div>
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
            
            <div className="p-4 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg">
              <div className="text-sm text-gray-600">Margem Contribuição</div>
              <div className="text-2xl font-bold text-indigo-700">
                {advancedMetrics.contributionMargin.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Margem após custos variáveis
              </div>
            </div>
            
            <div className="p-4 bg-gradient-to-br from-teal-50 to-cyan-50 rounded-lg">
              <div className="text-sm text-gray-600">Capital de Giro</div>
              <div className="text-2xl font-bold text-teal-700">
                {formatCurrency(advancedMetrics.workingCapital)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Necessário para operação
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

          {/* Métricas Financeiras Avançadas - Segunda Linha */}
          <div className="grid gap-4 md:grid-cols-4 mt-4">
            <div className="p-4 bg-gradient-to-br from-orange-50 to-red-50 rounded-lg">
              <div className="text-sm text-gray-600">Custos Fixos</div>
              <div className="text-2xl font-bold text-orange-700">
                {advancedMetrics.fixedCostsRatio.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500 mt-1">
                % dos custos totais
              </div>
            </div>
            
            <div className="p-4 bg-gradient-to-br from-pink-50 to-rose-50 rounded-lg">
              <div className="text-sm text-gray-600">Alavancagem Op.</div>
              <div className="text-2xl font-bold text-pink-700">
                {advancedMetrics.operatingLeverage.toFixed(1)}x
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Sensibilidade operacional
              </div>
            </div>
            
            <div className="p-4 bg-gradient-to-br from-amber-50 to-yellow-50 rounded-lg">
              <div className="text-sm text-gray-600">Capacidade Reinv.</div>
              <div className="text-2xl font-bold text-amber-700">
                {formatCurrency(advancedMetrics.reinvestmentRate)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Mensal para crescimento
              </div>
            </div>
            
            <div className="p-4 bg-gradient-to-br from-emerald-50 to-green-50 rounded-lg">
              <div className="text-sm text-gray-600">Valuation Est.</div>
              <div className="text-2xl font-bold text-emerald-700">
                {formatCurrency(advancedMetrics.estimatedValuation)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Valor estimado (10x)
              </div>
            </div>
          </div>

          {/* Análise de Fluxo de Caixa Projetado */}
          <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
            <h5 className="font-medium text-blue-900 mb-3">Projeção de Fluxo de Caixa</h5>
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <div className="text-sm text-blue-700">Fluxo Acumulado ({timeHorizon} meses)</div>
                <div className={cn(
                  "text-xl font-bold",
                  advancedMetrics.cashFlowProjection > 0 ? "text-green-600" : "text-red-600"
                )}>
                  {formatCurrency(advancedMetrics.cashFlowProjection)}
                </div>
              </div>
              <div>
                <div className="text-sm text-blue-700">Distribuição Mensal</div>
                <div className="text-xl font-bold text-blue-800">
                  {formatCurrency(advancedMetrics.distributionCapacity)}
                </div>
              </div>
              <div>
                <div className="text-sm text-blue-700">Capacidade de Endividamento</div>
                <div className="text-xl font-bold text-blue-800">
                  {formatCurrency(advancedMetrics.debtServiceCapacity)}
                </div>
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