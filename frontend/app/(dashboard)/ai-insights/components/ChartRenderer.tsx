'use client';

import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { formatCurrency } from '@/lib/utils';

interface ChartRendererProps {
  data: any;
}

const COLORS = [
  '#d946ef', // pink (primary)
  '#9333ea', // purple
  '#22c55e', // green
  '#3b82f6', // blue
  '#f59e0b', // amber
  '#ef4444', // red
  '#a78bfa', // violet
  '#f472b6', // pink-400
];

export function ChartRenderer({ data }: ChartRendererProps) {
  const chartConfig = useMemo(() => {
    if (!data || typeof data !== 'object') return null;

    // Detect chart type
    if (data.chart_type) {
      return {
        type: data.chart_type,
        data: data.data || [],
        config: data.config || {},
      };
    }

    // Auto-detect based on data structure
    if (Array.isArray(data)) {
      // If all items have 'value' and 'name', assume pie chart
      if (data.every(item => 'value' in item && 'name' in item)) {
        return { type: 'pie', data };
      }
      // Otherwise assume bar chart
      return { type: 'bar', data };
    }

    return null;
  }, [data]);

  if (!chartConfig) {
    return (
      <div className="text-center text-muted-foreground py-8">
        Formato de gráfico não reconhecido
      </div>
    );
  }

  const { type, data: chartData, config } = chartConfig;

  switch (type) {
    case 'pie':
      return (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value: any) => formatCurrency(value)}
                contentStyle={{
                  backgroundColor: 'hsl(var(--background))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                  color: 'hsl(var(--foreground))'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      );

    case 'bar':
      return (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey={config.xAxisKey || 'name'} 
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis tickFormatter={(value) => formatCurrency(value)} />
              <Tooltip 
                formatter={(value: any) => formatCurrency(value)}
                contentStyle={{
                  backgroundColor: 'hsl(var(--background))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                  color: 'hsl(var(--foreground))'
                }}
              />
              <Legend />
              <Bar 
                dataKey={config.yAxisKey || 'value'} 
                fill={COLORS[0]}
                name={config.yAxisLabel || 'Valor'}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      );

    case 'line':
      return (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey={config.xAxisKey || 'date'}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis tickFormatter={(value) => formatCurrency(value)} />
              <Tooltip 
                formatter={(value: any) => formatCurrency(value)}
                contentStyle={{
                  backgroundColor: 'hsl(var(--background))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                  color: 'hsl(var(--foreground))'
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey={config.yAxisKey || 'value'}
                stroke={COLORS[0]}
                name={config.yAxisLabel || 'Valor'}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      );

    case 'table':
      return (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {Object.keys(chartData[0] || {}).map((key) => (
                  <th
                    key={key}
                    className="px-4 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider"
                  >
                    {key}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {chartData.map((row: any, index: number) => (
                <tr key={index}>
                  {Object.values(row).map((value: any, cellIndex: number) => (
                    <td key={cellIndex} className="px-4 py-2 text-sm text-foreground">
                      {typeof value === 'number' && value > 100
                        ? formatCurrency(value)
                        : value}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );

    default:
      return (
        <div className="text-center text-muted-foreground py-8">
          Tipo de gráfico não suportado: {type}
        </div>
      );
  }
}