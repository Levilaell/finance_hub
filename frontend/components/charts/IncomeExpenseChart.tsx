import React, { memo } from 'react';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { formatCurrency } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';

interface IncomeExpenseData {
  month: string;
  income: number;
  expenses: number;
  profit: number;
}

interface IncomeExpenseChartProps {
  data: IncomeExpenseData[] | null;
  isLoading?: boolean;
  height?: number;
}

const IncomeExpenseChart = memo(({ data, isLoading = false, height = 320 }: IncomeExpenseChartProps) => {
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
        <p className="text-gray-500">Sem dados disponíveis</p>
      </div>
    );
  }

  // Format month labels
  const formattedData = data.map(item => ({
    ...item,
    monthLabel: new Date(item.month + '-01').toLocaleDateString('pt-BR', { 
      month: 'short', 
      year: 'numeric' 
    }),
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={formattedData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="monthLabel" 
          tick={{ fontSize: 12 }}
          angle={-45}
          textAnchor="end"
          height={60}
        />
        <YAxis 
          tick={{ fontSize: 12 }}
          tickFormatter={(value) => formatCurrency(value, 'compact')}
        />
        <Tooltip 
          formatter={(value: number, name: string) => [formatCurrency(value), name]}
          contentStyle={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid #e5e7eb',
            borderRadius: '6px',
          }}
        />
        <Legend wrapperStyle={{ paddingTop: '10px' }} />
        <Bar 
          dataKey="income" 
          fill="#22c55e" 
          name="Receitas"
          radius={[4, 4, 0, 0]}
        />
        <Bar 
          dataKey="expenses" 
          fill="#ef4444" 
          name="Despesas"
          radius={[4, 4, 0, 0]}
        />
        <Line
          type="monotone"
          dataKey="profit"
          stroke="#3b82f6"
          strokeWidth={3}
          name="Lucro/Prejuízo"
          dot={{ fill: '#3b82f6', r: 4 }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
});

IncomeExpenseChart.displayName = 'IncomeExpenseChart';

export { IncomeExpenseChart };