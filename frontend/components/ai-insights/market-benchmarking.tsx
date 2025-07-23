'use client';

import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
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
  BuildingOfficeIcon,
  UserGroupIcon,
  GlobeAltIcon,
  TrophyIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
} from 'recharts';

interface MarketBenchmarkingProps {
  companyData: {
    industry?: string;
    size?: 'micro' | 'small' | 'medium' | 'large';
    revenue: number;
    expenses: number;
    profitMargin: number;
    expenseRatio: number;
    categories: Array<{
      name: string;
      amount: number;
      percentage: number;
    }>;
  };
  keyMetrics?: {
    health_score: number;
    efficiency_score: number;
    growth_potential: number;
  };
}

// Dados de mercado simulados (em produção, viriam de uma API)
const MARKET_DATA = {
  industries: {
    'technology': {
      name: 'Tecnologia',
      avgProfitMargin: 22,
      avgExpenseRatio: 78,
      topExpenseCategories: ['Folha de Pagamento', 'Marketing', 'Infraestrutura'],
      avgGrowthRate: 25,
      bestPractices: [
        'Automação de processos',
        'Trabalho remoto para reduzir custos',
        'Investimento em P&D'
      ]
    },
    'retail': {
      name: 'Varejo',
      avgProfitMargin: 8,
      avgExpenseRatio: 92,
      topExpenseCategories: ['Estoque', 'Aluguel', 'Folha de Pagamento'],
      avgGrowthRate: 12,
      bestPractices: [
        'Gestão eficiente de estoque',
        'Omnichannel',
        'Programa de fidelidade'
      ]
    },
    'services': {
      name: 'Serviços',
      avgProfitMargin: 15,
      avgExpenseRatio: 85,
      topExpenseCategories: ['Folha de Pagamento', 'Marketing', 'Aluguel'],
      avgGrowthRate: 18,
      bestPractices: [
        'Upselling e cross-selling',
        'Automação de atendimento',
        'Contratos recorrentes'
      ]
    },
    'manufacturing': {
      name: 'Indústria',
      avgProfitMargin: 12,
      avgExpenseRatio: 88,
      topExpenseCategories: ['Matéria Prima', 'Folha de Pagamento', 'Energia'],
      avgGrowthRate: 10,
      bestPractices: [
        'Lean manufacturing',
        'Manutenção preventiva',
        'Gestão de fornecedores'
      ]
    },
    'food': {
      name: 'Alimentação',
      avgProfitMargin: 10,
      avgExpenseRatio: 90,
      topExpenseCategories: ['Insumos', 'Folha de Pagamento', 'Aluguel'],
      avgGrowthRate: 15,
      bestPractices: [
        'Controle rigoroso de desperdício',
        'Negociação com fornecedores',
        'Menu engineering'
      ]
    }
  },
  sizeCategories: {
    'micro': { revenueRange: '0-100k', avgEmployees: '1-5' },
    'small': { revenueRange: '100k-1M', avgEmployees: '6-20' },
    'medium': { revenueRange: '1M-10M', avgEmployees: '21-100' },
    'large': { revenueRange: '10M+', avgEmployees: '100+' }
  }
};

export function MarketBenchmarking({ 
  companyData,
  keyMetrics 
}: MarketBenchmarkingProps) {
  const [selectedIndustry, setSelectedIndustry] = useState<string>(
    companyData.industry || 'services'
  );
  const [selectedSize, setSelectedSize] = useState<string>(
    companyData.size || 'small'
  );
  const [showDetails, setShowDetails] = useState(false);

  const industryData = MARKET_DATA.industries[selectedIndustry as keyof typeof MARKET_DATA.industries];

  // Calcular comparações
  const comparisons = useMemo(() => {
    const profitMarginDiff = companyData.profitMargin - industryData.avgProfitMargin;
    const expenseRatioDiff = companyData.expenseRatio - industryData.avgExpenseRatio;
    
    return {
      profitMargin: {
        company: companyData.profitMargin,
        industry: industryData.avgProfitMargin,
        difference: profitMarginDiff,
        performance: profitMarginDiff > 0 ? 'above' : profitMarginDiff < -5 ? 'below' : 'average'
      },
      expenseRatio: {
        company: companyData.expenseRatio,
        industry: industryData.avgExpenseRatio,
        difference: expenseRatioDiff,
        performance: expenseRatioDiff < 0 ? 'above' : expenseRatioDiff > 5 ? 'below' : 'average'
      }
    };
  }, [companyData, industryData]);

  // Dados para o gráfico radar
  const radarData = useMemo(() => {
    const metrics = [
      {
        metric: 'Margem de Lucro',
        company: Math.min(100, (companyData.profitMargin / industryData.avgProfitMargin) * 100),
        industry: 100
      },
      {
        metric: 'Eficiência de Custos',
        company: Math.min(100, (industryData.avgExpenseRatio / companyData.expenseRatio) * 100),
        industry: 100
      },
      {
        metric: 'Saúde Financeira',
        company: keyMetrics?.health_score || 70,
        industry: 75
      },
      {
        metric: 'Eficiência Operacional',
        company: keyMetrics?.efficiency_score || 70,
        industry: 80
      },
      {
        metric: 'Potencial de Crescimento',
        company: keyMetrics?.growth_potential || 70,
        industry: industryData.avgGrowthRate * 4 // Normalizado para 100
      }
    ];
    
    return metrics;
  }, [companyData, industryData, keyMetrics]);

  // Calcular ranking estimado
  const estimatedRanking = useMemo(() => {
    let score = 0;
    if (comparisons.profitMargin.performance === 'above') score += 30;
    else if (comparisons.profitMargin.performance === 'average') score += 15;
    
    if (comparisons.expenseRatio.performance === 'above') score += 30;
    else if (comparisons.expenseRatio.performance === 'average') score += 15;
    
    if (keyMetrics) {
      if (keyMetrics.health_score > 80) score += 20;
      else if (keyMetrics.health_score > 60) score += 10;
      
      if (keyMetrics.efficiency_score > 80) score += 20;
      else if (keyMetrics.efficiency_score > 60) score += 10;
    }
    
    if (score >= 80) return { position: 'Top 10%', color: 'text-green-600' };
    if (score >= 60) return { position: 'Top 25%', color: 'text-blue-600' };
    if (score >= 40) return { position: 'Top 50%', color: 'text-yellow-600' };
    return { position: 'Abaixo da média', color: 'text-red-600' };
  }, [comparisons, keyMetrics]);

  // Recomendações baseadas na comparação
  const recommendations = useMemo(() => {
    const recs = [];
    
    if (comparisons.profitMargin.performance === 'below') {
      recs.push({
        type: 'warning',
        title: 'Margem Abaixo do Mercado',
        description: `Sua margem está ${Math.abs(comparisons.profitMargin.difference).toFixed(1)}% abaixo da média do setor`,
        action: 'Revisar estrutura de preços e custos'
      });
    }
    
    if (comparisons.expenseRatio.performance === 'below') {
      recs.push({
        type: 'warning',
        title: 'Custos Acima da Média',
        description: `Seus custos estão ${comparisons.expenseRatio.difference.toFixed(1)}% acima do mercado`,
        action: 'Implementar programa de redução de custos'
      });
    }
    
    // Comparar categorias de gastos
    const topCategory = companyData.categories[0];
    if (topCategory && !industryData.topExpenseCategories.includes(topCategory.name)) {
      recs.push({
        type: 'info',
        title: 'Padrão de Gastos Diferente',
        description: `"${topCategory.name}" não é uma categoria típica de alto gasto neste setor`,
        action: 'Avaliar se este gasto é estratégico ou pode ser otimizado'
      });
    }
    
    return recs;
  }, [comparisons, companyData, industryData]);

  return (
    <div className="space-y-6">
      {/* Seletores de Contexto */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GlobeAltIcon className="h-5 w-5 text-purple-600" />
            Benchmarking de Mercado
          </CardTitle>
          <CardDescription>
            Compare seu desempenho com empresas similares do mercado
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 mb-6">
            <div>
              <Label className="mb-2 block">Setor de Atuação</Label>
              <Select value={selectedIndustry} onValueChange={setSelectedIndustry}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(MARKET_DATA.industries).map(([key, data]) => (
                    <SelectItem key={key} value={key}>
                      <div className="flex items-center gap-2">
                        <BuildingOfficeIcon className="h-4 w-4" />
                        {data.name}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label className="mb-2 block">Porte da Empresa</Label>
              <Select value={selectedSize} onValueChange={setSelectedSize}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(MARKET_DATA.sizeCategories).map(([key, data]) => (
                    <SelectItem key={key} value={key}>
                      <div className="flex items-center gap-2">
                        <UserGroupIcon className="h-4 w-4" />
                        <span className="capitalize">{key}</span>
                        <span className="text-xs text-gray-500">({data.revenueRange})</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Cards de Comparação Rápida */}
          <div className="grid gap-4 md:grid-cols-3 mb-6">
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Posição no Mercado</span>
                <TrophyIcon className="h-5 w-5 text-yellow-500" />
              </div>
              <div className={cn("text-2xl font-bold", estimatedRanking.color)}>
                {estimatedRanking.position}
              </div>
              <p className="text-xs text-gray-600 mt-1">
                Baseado em métricas financeiras
              </p>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-4 rounded-lg border border-green-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Margem vs Mercado</span>
                {comparisons.profitMargin.performance === 'above' ? (
                  <ArrowTrendingUpIcon className="h-5 w-5 text-green-600" />
                ) : (
                  <ArrowTrendingDownIcon className="h-5 w-5 text-red-600" />
                )}
              </div>
              <div className="text-2xl font-bold">
                {comparisons.profitMargin.difference > 0 ? '+' : ''}
                {comparisons.profitMargin.difference.toFixed(1)}%
              </div>
              <p className="text-xs text-gray-600 mt-1">
                Média do setor: {industryData.avgProfitMargin}%
              </p>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-4 rounded-lg border border-purple-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Eficiência de Custos</span>
                {comparisons.expenseRatio.performance === 'above' ? (
                  <CheckCircleIcon className="h-5 w-5 text-green-600" />
                ) : (
                  <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />
                )}
              </div>
              <div className="text-2xl font-bold">
                {companyData.expenseRatio.toFixed(1)}%
              </div>
              <p className="text-xs text-gray-600 mt-1">
                Média do setor: {industryData.avgExpenseRatio}%
              </p>
            </div>
          </div>

          {/* Gráfico Radar de Comparação */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="text-sm font-medium mb-4 text-center">
              Comparação de Performance
            </h4>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="metric" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                <Radar
                  name="Sua Empresa"
                  dataKey="company"
                  stroke="#8b5cf6"
                  fill="#8b5cf6"
                  fillOpacity={0.6}
                />
                <Radar
                  name="Média do Setor"
                  dataKey="industry"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.3}
                />
                <Tooltip />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <Button
            onClick={() => setShowDetails(!showDetails)}
            variant="outline"
            className="w-full"
          >
            <InformationCircleIcon className="h-4 w-4 mr-2" />
            {showDetails ? 'Ocultar' : 'Ver'} Análise Detalhada
          </Button>
        </CardContent>
      </Card>

      {/* Análise Detalhada */}
      {showDetails && (
        <>
          {/* Melhores Práticas do Setor */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <LightBulbIcon className="h-5 w-5 text-yellow-500" />
                Melhores Práticas do Setor
              </CardTitle>
              <CardDescription>
                Estratégias comprovadas de empresas líderes em {industryData.name}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {industryData.bestPractices.map((practice, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <div className="p-2 bg-blue-100 rounded-full">
                      <CheckCircleIcon className="h-4 w-4 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <h5 className="font-medium">{practice}</h5>
                      <p className="text-sm text-gray-600 mt-1">
                        Implementado por empresas top 20% do setor
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Análise de Categorias de Gastos */}
          <Card>
            <CardHeader>
              <CardTitle>Distribuição de Gastos vs Mercado</CardTitle>
              <CardDescription>
                Compare sua alocação de recursos com o padrão do setor
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <h5 className="text-sm font-medium mb-2">
                    Top 3 Categorias do Setor {industryData.name}:
                  </h5>
                  <div className="flex gap-2">
                    {industryData.topExpenseCategories.map((cat, index) => (
                      <Badge key={index} variant="secondary">
                        {index + 1}. {cat}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <h5 className="text-sm font-medium">Suas Top 5 Categorias:</h5>
                  {companyData.categories.slice(0, 5).map((category, index) => {
                    const isTypical = industryData.topExpenseCategories.includes(category.name);
                    
                    return (
                      <div key={index} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-sm">{index + 1}. {category.name}</span>
                          {isTypical && (
                            <Badge variant="outline" className="text-xs">
                              Típico do setor
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">
                            {category.percentage.toFixed(1)}%
                          </span>
                          <div className="w-24">
                            <Progress value={category.percentage} className="h-2" />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recomendações Personalizadas */}
          {recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recomendações Baseadas no Benchmarking</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {recommendations.map((rec, index) => (
                    <div
                      key={index}
                      className={cn(
                        "p-4 rounded-lg border",
                        rec.type === 'warning' && "bg-yellow-50 border-yellow-200",
                        rec.type === 'info' && "bg-blue-50 border-blue-200"
                      )}
                    >
                      <div className="flex items-start gap-3">
                        {rec.type === 'warning' ? (
                          <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 flex-shrink-0" />
                        ) : (
                          <InformationCircleIcon className="h-5 w-5 text-blue-600 flex-shrink-0" />
                        )}
                        <div className="flex-1">
                          <h5 className="font-medium">{rec.title}</h5>
                          <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
                          <p className="text-sm font-medium mt-2">
                            💡 Ação sugerida: {rec.action}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Insights de Crescimento */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ArrowTrendingUpIcon className="h-5 w-5 text-green-600" />
                Potencial de Crescimento
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg">
                  <h5 className="font-medium mb-2">Taxa de Crescimento do Setor</h5>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold text-green-600">
                      {industryData.avgGrowthRate}%
                    </span>
                    <span className="text-sm text-gray-600">ao ano</span>
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    Empresas líderes crescem até {industryData.avgGrowthRate * 1.5}% ao ano
                  </p>
                </div>

                <div className="space-y-2">
                  <h5 className="text-sm font-medium">Oportunidades de Crescimento:</h5>
                  <ul className="space-y-2">
                    <li className="flex items-start gap-2 text-sm">
                      <CheckCircleIcon className="h-4 w-4 text-green-500 flex-shrink-0 mt-0.5" />
                      <span>Expansão para novos mercados geográficos</span>
                    </li>
                    <li className="flex items-start gap-2 text-sm">
                      <CheckCircleIcon className="h-4 w-4 text-green-500 flex-shrink-0 mt-0.5" />
                      <span>Diversificação de produtos/serviços</span>
                    </li>
                    <li className="flex items-start gap-2 text-sm">
                      <CheckCircleIcon className="h-4 w-4 text-green-500 flex-shrink-0 mt-0.5" />
                      <span>Parcerias estratégicas no setor</span>
                    </li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function Label({ children, className }: { children: React.ReactNode; className?: string }) {
  return <label className={cn("text-sm font-medium text-gray-700", className)}>{children}</label>;
}