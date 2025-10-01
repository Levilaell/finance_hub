'use client';

import React from 'react';
import {
  LineChart,
  Line,
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

interface CashFlowData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    borderColor?: string;
    backgroundColor?: string;
  }>;
  summary?: {
    total_income: number;
    total_expenses: number;
    net_cash_flow: number;
    period: string;
  };
}

interface CashFlowChartProps {
  data?: CashFlowData;
  loading?: boolean;
  title?: string;
}

export default function CashFlowChart({
  data,
  loading = false,
  title = 'Fluxo de Caixa'
}: CashFlowChartProps) {
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
  const chartData = data.labels.map((label, index) => {
    const point: any = { name: label };
    data.datasets.forEach(dataset => {
      point[dataset.label] = dataset.data[index];
    });
    return point;
  });

  const formatTooltipValue = (value: number) => formatCurrency(value);
  const formatYAxisTick = (value: number) => {
    if (value >= 1000000) {
      return `R$ ${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `R$ ${(value / 1000).toFixed(0)}K`;
    }
    return `R$ ${value}`;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {data.summary && (
          <div className="grid grid-cols-3 gap-4 mt-4">
            <div>
              <p className="text-sm text-muted-foreground">Receitas</p>
              <p className="text-lg font-semibold text-green-600">
                {formatCurrency(data.summary.total_income)}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Despesas</p>
              <p className="text-lg font-semibold text-red-600">
                {formatCurrency(data.summary.total_expenses)}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Saldo</p>
              <p className={`text-lg font-semibold ${data.summary.net_cash_flow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(data.summary.net_cash_flow)}
              </p>
            </div>
          </div>
        )}
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
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
            {data.datasets.map((dataset, index) => (
              <Line
                key={dataset.label}
                type="monotone"
                dataKey={dataset.label}
                stroke={dataset.borderColor || (index === 0 ? '#10b981' : '#ef4444')}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}