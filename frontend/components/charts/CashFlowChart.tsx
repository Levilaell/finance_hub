import React, { memo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Line,
} from 'recharts';
import { formatCurrency } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';

interface CashFlowData {
  date: string;
  income: number;
  expenses: number;
  balance: number;
}

interface CashFlowChartProps {
  data: CashFlowData[] | null;
  isLoading?: boolean;
  height?: number;
}

const CashFlowChart = memo(({ data, isLoading = false, height = 320 }: CashFlowChartProps) => {
  if (isLoading) {
    return (
      <div className="w-full" style={{ height }}>
        <Skeleton className="w-full h-full" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <p className="text-muted-foreground">Sem dados disponíveis</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="colorIncome" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#d946ef" stopOpacity={0.8} />
            <stop offset="95%" stopColor="#d946ef" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="colorExpenses" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#9333ea" stopOpacity={0.8} />
            <stop offset="95%" stopColor="#9333ea" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="date" 
          tick={{ fontSize: 12 }}
          className="text-foreground"
          tickFormatter={(value) => {
            const date = new Date(value);
            return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
          }}
        />
        <YAxis 
          tick={{ fontSize: 12 }}
          className="text-foreground"
          tickFormatter={(value) => formatCurrency(value, 'compact')}
        />
        <Tooltip 
          formatter={(value: number) => formatCurrency(value)}
          labelFormatter={(label) => {
            const date = new Date(label);
            return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'long', year: 'numeric' });
          }}
          contentStyle={{
            backgroundColor: 'hsl(var(--background))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '6px',
            color: 'hsl(var(--foreground))'
          }}
        />
        <Legend />
        <Area
          type="monotone"
          dataKey="income"
          stroke="#d946ef"
          fillOpacity={1}
          fill="url(#colorIncome)"
          name="Receitas"
        />
        <Area
          type="monotone"
          dataKey="expenses"
          stroke="#9333ea"
          fillOpacity={1}
          fill="url(#colorExpenses)"
          name="Despesas"
        />
        <Line
          type="monotone"
          dataKey="balance"
          stroke="#3b82f6"
          strokeWidth={3}
          name="Saldo"
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
});

CashFlowChart.displayName = 'CashFlowChart';

export { CashFlowChart };