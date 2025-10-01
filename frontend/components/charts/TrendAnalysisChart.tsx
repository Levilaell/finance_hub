'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { formatCurrency } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface TrendAnalysisData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    borderColor?: string;
    backgroundColor?: string;
  }>;
  analysis?: {
    income_trend_percentage: number;
    expense_trend_percentage: number;
    income_direction: 'up' | 'down' | 'stable';
    expense_direction: 'up' | 'down' | 'stable';
    avg_monthly_income: number;
    avg_monthly_expenses: number;
    months_analyzed: number;
  };
}

interface TrendAnalysisChartProps {
  data?: TrendAnalysisData;
  loading?: boolean;
  title?: string;
}

export default function TrendAnalysisChart({
  data,
  loading = false,
  title = 'Análise de Tendências'
}: TrendAnalysisChartProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="w-full h-[300px]" />
        </CardContent>
      </Card>
    );
  }

  if (!data || !data.labels || data.labels.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[300px] text-muted-foreground">
          Nenhum dado disponível
        </CardContent>
      </Card>
    );
  }

  // Transform data for Recharts
  const chartData = data.labels.map((label, index) => ({
    name: label,
    Receitas: data.datasets[0]?.data[index] || 0,
    Despesas: data.datasets[1]?.data[index] || 0,
  }));

  const formatTooltipValue = (value: number) => formatCurrency(value);

  const formatYAxisTick = (value: number) => {
    if (value >= 1000000) {
      return `R$ ${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `R$ ${(value / 1000).toFixed(0)}K`;
    }
    return `R$ ${value}`;
  };

  const getTrendIcon = (direction: 'up' | 'down' | 'stable') => {
    switch (direction) {
      case 'up':
        return <TrendingUp className="w-4 h-4" />;
      case 'down':
        return <TrendingDown className="w-4 h-4" />;
      case 'stable':
        return <Minus className="w-4 h-4" />;
    }
  };

  const getTrendColor = (direction: 'up' | 'down' | 'stable', type: 'income' | 'expense') => {
    if (direction === 'stable') return 'text-gray-600';
    if (type === 'income') {
      return direction === 'up' ? 'text-green-600' : 'text-red-600';
    } else {
      return direction === 'up' ? 'text-red-600' : 'text-green-600';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {data.analysis && (
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div className="p-3 bg-green-50 dark:bg-green-950 rounded-lg">
              <div className="flex items-center justify-between mb-1">
                <p className="text-sm font-medium">Tendência de Receitas</p>
                <div className={`flex items-center ${getTrendColor(data.analysis.income_direction, 'income')}`}>
                  {getTrendIcon(data.analysis.income_direction)}
                  <span className="ml-1 text-sm font-semibold">
                    {data.analysis.income_trend_percentage > 0 ? '+' : ''}{data.analysis.income_trend_percentage}%
                  </span>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">Média mensal</p>
              <p className="text-lg font-semibold">
                {formatCurrency(data.analysis.avg_monthly_income)}
              </p>
            </div>
            <div className="p-3 bg-red-50 dark:bg-red-950 rounded-lg">
              <div className="flex items-center justify-between mb-1">
                <p className="text-sm font-medium">Tendência de Despesas</p>
                <div className={`flex items-center ${getTrendColor(data.analysis.expense_direction, 'expense')}`}>
                  {getTrendIcon(data.analysis.expense_direction)}
                  <span className="ml-1 text-sm font-semibold">
                    {data.analysis.expense_trend_percentage > 0 ? '+' : ''}{data.analysis.expense_trend_percentage}%
                  </span>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">Média mensal</p>
              <p className="text-lg font-semibold">
                {formatCurrency(data.analysis.avg_monthly_expenses)}
              </p>
            </div>
          </div>
        )}
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={formatYAxisTick}
            />
            <Tooltip formatter={formatTooltipValue} />
            <Legend />
            <Bar dataKey="Receitas" fill="#10b981" />
            <Bar dataKey="Despesas" fill="#ef4444" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}