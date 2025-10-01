'use client';

import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { formatCurrency } from '@/lib/utils';

interface CategoryBreakdownData {
  labels: string[];
  datasets: Array<{
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }>;
  percentages?: number[];
  summary?: {
    total_amount?: number;
    categories_count?: number;
    transaction_type?: string;
  };
}

interface CategoryBreakdownChartProps {
  data?: CategoryBreakdownData;
  loading?: boolean;
  title?: string;
}

const COLORS = [
  '#ef4444', // red
  '#f97316', // orange
  '#eab308', // yellow
  '#84cc16', // lime
  '#22c55e', // green
  '#10b981', // emerald
  '#06b6d4', // cyan
  '#0ea5e9', // sky
  '#3b82f6', // blue
  '#6366f1', // indigo
  '#8b5cf6', // violet
  '#a855f7', // purple
];

export default function CategoryBreakdownChart({
  data,
  loading = false,
  title = 'Distribuição por Categoria'
}: CategoryBreakdownChartProps) {
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
    value: data.datasets[0].data[index],
    percentage: data.percentages ? data.percentages[index] : 0,
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-popover p-2 rounded-lg border shadow-lg">
          <p className="font-semibold">{payload[0].name}</p>
          <p className="text-sm">{formatCurrency(payload[0].value)}</p>
          <p className="text-sm text-muted-foreground">{payload[0].payload.percentage}%</p>
        </div>
      );
    }
    return null;
  };

  const renderCustomizedLabel = ({
    cx, cy, midAngle, innerRadius, outerRadius, percent
  }: any) => {
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    if (percent < 0.05) return null; // Don't show label for small slices

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        className="text-xs font-medium"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {data.summary && (
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div>
              <p className="text-sm text-muted-foreground">Total</p>
              <p className="text-lg font-semibold">
                {formatCurrency(data.summary.total_amount || 0)}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Categorias</p>
              <p className="text-lg font-semibold">
                {data.summary.categories_count || 0}
              </p>
            </div>
          </div>
        )}
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={renderCustomizedLabel}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="bottom"
              height={36}
              formatter={(value: string) => (
                <span className="text-xs">{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}