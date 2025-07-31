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
  '#3B82F6', // blue-500
  '#10B981', // green-500
  '#F59E0B', // amber-500
  '#EF4444', // red-500
  '#8B5CF6', // violet-500
  '#EC4899', // pink-500
  '#14B8A6', // teal-500
  '#F97316', // orange-500
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
      <div className="text-center text-gray-500 py-8">
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
              <Tooltip formatter={(value: any) => formatCurrency(value)} />
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
              <Tooltip formatter={(value: any) => formatCurrency(value)} />
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
              <Tooltip formatter={(value: any) => formatCurrency(value)} />
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
                    className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
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
                    <td key={cellIndex} className="px-4 py-2 text-sm text-gray-900">
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
        <div className="text-center text-gray-500 py-8">
          Tipo de gráfico não suportado: {type}
        </div>
      );
  }
}