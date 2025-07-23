'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatCurrency, cn } from '@/lib/utils';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  LightBulbIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  SparklesIcon,
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
} from 'recharts';

interface ScenarioSimulatorProps {
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
  onSimulationComplete?: (results: any) => void;
}

interface Scenario {
  id: string;
  name: string;
  icon: React.ComponentType<any>;
  description: string;
  adjustments: {
    income: number;
    expenses: number;
    categories: Record<string, number>;
  };
}

const PRESET_SCENARIOS: Scenario[] = [
  {
    id: 'optimistic',
    name: 'Otimista',
    icon: ArrowTrendingUpIcon,
    description: '20% mais receita, 10% menos despesas',
    adjustments: {
      income: 20,
      expenses: -10,
      categories: {}
    }
  },
  {
    id: 'realistic',
    name: 'Realista',
    icon: ChartBarIcon,
    description: '5% mais receita, despesas estáveis',
    adjustments: {
      income: 5,
      expenses: 0,
      categories: {}
    }
  },
  {
    id: 'pessimistic',
    name: 'Pessimista',
    icon: ArrowTrendingDownIcon,
    description: '10% menos receita, 5% mais despesas',
    adjustments: {
      income: -10,
      expenses: 5,
      categories: {}
    }
  },
  {
    id: 'cost_cutting',
    name: 'Corte de Custos',
    icon: ExclamationTriangleIcon,
    description: 'Receita estável, 20% menos despesas',
    adjustments: {
      income: 0,
      expenses: -20,
      categories: {
        'Alimentação': -30,
        'Transporte': -25,
        'Outros': -15
      }
    }
  }
];

export function ScenarioSimulator({ 
  currentData, 
  predictions,
  onSimulationComplete 
}: ScenarioSimulatorProps) {
  const [selectedScenario, setSelectedScenario] = useState<string>('custom');
  const [incomeAdjustment, setIncomeAdjustment] = useState<number>(0);
  const [expenseAdjustment, setExpenseAdjustment] = useState<number>(0);
  const [categoryAdjustments, setCategoryAdjustments] = useState<Record<string, number>>({});
  const [showComparison, setShowComparison] = useState(false);
  const [simulationHistory, setSimulationHistory] = useState<any[]>([]);

  // Calcular valores simulados
  const simulatedValues = useMemo(() => {
    const baseIncome = currentData.income;
    const baseExpenses = currentData.expenses;
    
    // Aplicar ajustes
    const newIncome = baseIncome * (1 + incomeAdjustment / 100);
    
    // Calcular despesas por categoria com ajustes
    let newExpenses = 0;
    const adjustedCategories = currentData.categories.map(cat => {
      const categoryAdjustment = categoryAdjustments[cat.name] || expenseAdjustment;
      const newAmount = cat.amount * (1 + categoryAdjustment / 100);
      newExpenses += newAmount;
      
      return {
        ...cat,
        amount: newAmount,
        percentage: 0, // Será recalculado
        adjustment: categoryAdjustment
      };
    });
    
    // Recalcular percentuais
    adjustedCategories.forEach(cat => {
      cat.percentage = (cat.amount / newExpenses) * 100;
    });
    
    // Se não há ajustes por categoria, usar ajuste geral
    if (Object.keys(categoryAdjustments).length === 0) {
      newExpenses = baseExpenses * (1 + expenseAdjustment / 100);
    }
    
    const newProfit = newIncome - newExpenses;
    const profitMargin = newIncome > 0 ? (newProfit / newIncome) * 100 : 0;
    
    // Calcular impacto
    const incomeImpact = newIncome - baseIncome;
    const expenseImpact = newExpenses - baseExpenses;
    const profitImpact = newProfit - (baseIncome - baseExpenses);
    
    // Projeções para 12 meses
    const monthlyProjections = [];
    for (let i = 0; i < 12; i++) {
      const monthIncome = newIncome * (1 + (predictions?.growth_rate || 0) / 100 / 12) ** i;
      const monthExpenses = newExpenses * (1 + 0.02) ** i; // 2% de inflação anual
      
      monthlyProjections.push({
        month: `Mês ${i + 1}`,
        income: monthIncome,
        expenses: monthExpenses,
        profit: monthIncome - monthExpenses,
        profitMargin: monthIncome > 0 ? ((monthIncome - monthExpenses) / monthIncome) * 100 : 0
      });
    }
    
    return {
      income: newIncome,
      expenses: newExpenses,
      profit: newProfit,
      profitMargin,
      incomeImpact,
      expenseImpact,
      profitImpact,
      categories: adjustedCategories,
      monthlyProjections,
      yearEndProfit: monthlyProjections[11].profit * 12,
      avgMonthlyProfit: monthlyProjections.reduce((sum, m) => sum + m.profit, 0) / 12
    };
  }, [currentData, predictions, incomeAdjustment, expenseAdjustment, categoryAdjustments]);

  // Aplicar cenário pré-definido
  const applyScenario = useCallback((scenario: Scenario) => {
    setIncomeAdjustment(scenario.adjustments.income);
    setExpenseAdjustment(scenario.adjustments.expenses);
    setCategoryAdjustments(scenario.adjustments.categories);
    setSelectedScenario(scenario.id);
  }, []);

  // Resetar simulação
  const resetSimulation = useCallback(() => {
    setIncomeAdjustment(0);
    setExpenseAdjustment(0);
    setCategoryAdjustments({});
    setSelectedScenario('custom');
  }, []);

  // Salvar simulação
  const saveSimulation = useCallback(() => {
    const simulation = {
      id: Date.now(),
      timestamp: new Date(),
      scenario: selectedScenario,
      adjustments: {
        income: incomeAdjustment,
        expenses: expenseAdjustment,
        categories: categoryAdjustments
      },
      results: simulatedValues
    };
    
    setSimulationHistory([...simulationHistory, simulation]);
    
    if (onSimulationComplete) {
      onSimulationComplete(simulation);
    }
  }, [selectedScenario, incomeAdjustment, expenseAdjustment, categoryAdjustments, simulatedValues, simulationHistory, onSimulationComplete]);

  // Dados para gráficos de comparação
  const comparisonData = useMemo(() => {
    return [
      {
        metric: 'Receita',
        atual: currentData.income,
        simulado: simulatedValues.income,
        diferenca: simulatedValues.incomeImpact
      },
      {
        metric: 'Despesas',
        atual: currentData.expenses,
        simulado: simulatedValues.expenses,
        diferenca: simulatedValues.expenseImpact
      },
      {
        metric: 'Lucro',
        atual: currentData.income - currentData.expenses,
        simulado: simulatedValues.profit,
        diferenca: simulatedValues.profitImpact
      }
    ];
  }, [currentData, simulatedValues]);

  return (
    <div className="space-y-6">
      {/* Seletor de Cenários */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <SparklesIcon className="h-5 w-5 text-purple-600" />
            Simulador de Cenários
          </CardTitle>
          <CardDescription>
            Explore diferentes cenários e veja o impacto nas suas finanças
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4 mb-6">
            {PRESET_SCENARIOS.map((scenario) => {
              const Icon = scenario.icon;
              const isSelected = selectedScenario === scenario.id;
              
              return (
                <Button
                  key={scenario.id}
                  variant={isSelected ? "default" : "outline"}
                  className={cn(
                    "h-auto p-4 flex flex-col items-start gap-2",
                    isSelected && "ring-2 ring-purple-600"
                  )}
                  onClick={() => applyScenario(scenario)}
                >
                  <div className="flex items-center gap-2 w-full">
                    <Icon className="h-5 w-5" />
                    <span className="font-medium">{scenario.name}</span>
                  </div>
                  <span className="text-xs text-left opacity-80">
                    {scenario.description}
                  </span>
                </Button>
              );
            })}
          </div>

          {/* Controles Customizados */}
          <div className="space-y-6 border-t pt-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label>Ajuste de Receita</Label>
                <span className={cn(
                  "text-sm font-medium",
                  incomeAdjustment > 0 ? "text-green-600" : 
                  incomeAdjustment < 0 ? "text-red-600" : "text-gray-600"
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

            <div>
              <div className="flex items-center justify-between mb-2">
                <Label>Ajuste Geral de Despesas</Label>
                <span className={cn(
                  "text-sm font-medium",
                  expenseAdjustment > 0 ? "text-red-600" : 
                  expenseAdjustment < 0 ? "text-green-600" : "text-gray-600"
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

            {/* Ajustes por Categoria */}
            <div>
              <Label className="mb-3 block">Ajustes por Categoria (opcional)</Label>
              <div className="space-y-3">
                {currentData.categories.slice(0, 5).map((category) => {
                  const adjustment = categoryAdjustments[category.name] || 0;
                  
                  return (
                    <div key={category.name} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span>{category.name}</span>
                        <span className={cn(
                          "font-medium",
                          adjustment > 0 ? "text-red-600" : 
                          adjustment < 0 ? "text-green-600" : "text-gray-600"
                        )}>
                          {adjustment > 0 ? '+' : ''}{adjustment}%
                        </span>
                      </div>
                      <Slider
                        value={[adjustment]}
                        onValueChange={([value]) => {
                          setCategoryAdjustments({
                            ...categoryAdjustments,
                            [category.name]: value
                          });
                          setSelectedScenario('custom');
                        }}
                        min={-50}
                        max={50}
                        step={5}
                        className="h-2"
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Resultados da Simulação */}
          <div className="mt-6 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
            <h4 className="font-medium mb-4 flex items-center gap-2">
              <ChartBarIcon className="h-5 w-5 text-purple-600" />
              Resultado da Simulação
            </h4>
            
            <div className="grid gap-4 md:grid-cols-3">
              <div className="bg-white p-3 rounded-lg">
                <div className="text-sm text-gray-600">Nova Receita</div>
                <div className="text-xl font-bold text-green-600">
                  {formatCurrency(simulatedValues.income)}
                </div>
                <div className={cn(
                  "text-xs mt-1",
                  simulatedValues.incomeImpact >= 0 ? "text-green-600" : "text-red-600"
                )}>
                  {simulatedValues.incomeImpact >= 0 ? '+' : ''}
                  {formatCurrency(simulatedValues.incomeImpact)}
                </div>
              </div>
              
              <div className="bg-white p-3 rounded-lg">
                <div className="text-sm text-gray-600">Novas Despesas</div>
                <div className="text-xl font-bold text-red-600">
                  {formatCurrency(simulatedValues.expenses)}
                </div>
                <div className={cn(
                  "text-xs mt-1",
                  simulatedValues.expenseImpact <= 0 ? "text-green-600" : "text-red-600"
                )}>
                  {simulatedValues.expenseImpact >= 0 ? '+' : ''}
                  {formatCurrency(simulatedValues.expenseImpact)}
                </div>
              </div>
              
              <div className="bg-white p-3 rounded-lg">
                <div className="text-sm text-gray-600">Novo Lucro</div>
                <div className={cn(
                  "text-xl font-bold",
                  simulatedValues.profit >= 0 ? "text-blue-600" : "text-red-600"
                )}>
                  {formatCurrency(simulatedValues.profit)}
                </div>
                <div className={cn(
                  "text-xs mt-1",
                  simulatedValues.profitImpact >= 0 ? "text-green-600" : "text-red-600"
                )}>
                  {simulatedValues.profitImpact >= 0 ? '+' : ''}
                  {formatCurrency(simulatedValues.profitImpact)}
                </div>
              </div>
            </div>

            <div className="mt-4 grid gap-2 md:grid-cols-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Margem de Lucro</span>
                <Badge variant={simulatedValues.profitMargin >= 20 ? "default" : "secondary"}>
                  {simulatedValues.profitMargin.toFixed(1)}%
                </Badge>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Lucro Anual Projetado</span>
                <span className="font-medium">
                  {formatCurrency(simulatedValues.yearEndProfit)}
                </span>
              </div>
            </div>
          </div>

          {/* Ações */}
          <div className="mt-6 flex gap-3">
            <Button
              onClick={() => setShowComparison(!showComparison)}
              variant="outline"
            >
              <ChartBarIcon className="h-4 w-4 mr-2" />
              {showComparison ? 'Ocultar' : 'Ver'} Comparação
            </Button>
            <Button
              onClick={saveSimulation}
              className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
            >
              <CheckCircleIcon className="h-4 w-4 mr-2" />
              Salvar Simulação
            </Button>
            <Button
              onClick={resetSimulation}
              variant="outline"
            >
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Resetar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Gráficos de Comparação */}
      {showComparison && (
        <Card>
          <CardHeader>
            <CardTitle>Comparação Visual</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 md:grid-cols-2">
              {/* Gráfico de Barras - Comparação */}
              <div>
                <h4 className="text-sm font-medium mb-4">Atual vs Simulado</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={comparisonData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="metric" />
                    <YAxis tickFormatter={(value) => `R$ ${(value / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(value: any) => formatCurrency(value)} />
                    <Legend />
                    <Bar dataKey="atual" fill="#8884d8" />
                    <Bar dataKey="simulado" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Gráfico de Linha - Projeção Mensal */}
              <div>
                <h4 className="text-sm font-medium mb-4">Projeção de 12 Meses</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={simulatedValues.monthlyProjections}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis tickFormatter={(value) => `R$ ${(value / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(value: any) => formatCurrency(value)} />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="income" 
                      stroke="#10b981" 
                      name="Receita"
                      strokeWidth={2}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="expenses" 
                      stroke="#ef4444" 
                      name="Despesas"
                      strokeWidth={2}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="profit" 
                      stroke="#3b82f6" 
                      name="Lucro"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Insights da Simulação */}
            <div className="mt-6 space-y-3">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <LightBulbIcon className="h-4 w-4 text-yellow-500" />
                Insights da Simulação
              </h4>
              
              {simulatedValues.profitImpact > 0 && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm">
                  <strong>Impacto Positivo:</strong> Esta simulação resultaria em um aumento de {formatCurrency(simulatedValues.profitImpact)} no lucro mensal.
                </div>
              )}
              
              {simulatedValues.profitImpact < 0 && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm">
                  <strong>Atenção:</strong> Esta simulação resultaria em uma redução de {formatCurrency(Math.abs(simulatedValues.profitImpact))} no lucro mensal.
                </div>
              )}
              
              {simulatedValues.profitMargin > 20 && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm">
                  <strong>Margem Saudável:</strong> A margem de lucro de {simulatedValues.profitMargin.toFixed(1)}% está acima do recomendado.
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Histórico de Simulações */}
      {simulationHistory.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Histórico de Simulações</CardTitle>
            <CardDescription>
              Compare diferentes cenários que você explorou
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {simulationHistory.map((sim) => (
                <div
                  key={sim.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                >
                  <div>
                    <div className="font-medium">
                      Cenário: {PRESET_SCENARIOS.find(s => s.id === sim.scenario)?.name || 'Customizado'}
                    </div>
                    <div className="text-sm text-gray-600">
                      Receita: {sim.adjustments.income > 0 ? '+' : ''}{sim.adjustments.income}% | 
                      Despesas: {sim.adjustments.expenses > 0 ? '+' : ''}{sim.adjustments.expenses}%
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={cn(
                      "font-medium",
                      sim.results.profitImpact >= 0 ? "text-green-600" : "text-red-600"
                    )}>
                      {sim.results.profitImpact >= 0 ? '+' : ''}
                      {formatCurrency(sim.results.profitImpact)}
                    </div>
                    <div className="text-xs text-gray-500">
                      Impacto no Lucro
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}