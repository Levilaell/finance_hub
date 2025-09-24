'use client';

import { useState, useEffect } from 'react';
import { FinancialSummary, CategorySummary } from '@/types/banking';
import { bankingService } from '@/services/banking.service';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  BanknotesIcon,
  CalendarDaysIcon,
  ChartPieIcon,
} from '@heroicons/react/24/outline';
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
import { format, subMonths } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { cn } from '@/lib/utils';

interface FinancialDashboardProps {
  className?: string;
}

export function FinancialDashboard({ className }: FinancialDashboardProps) {
  const [summary, setSummary] = useState<FinancialSummary | null>(null);
  const [categories, setCategories] = useState<CategorySummary | null>(null);
  const [monthlyData, setMonthlyData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [dateRange, setDateRange] = useState({
    from: format(subMonths(new Date(), 3), 'yyyy-MM-dd'), // Last 3 months
    to: format(new Date(), 'yyyy-MM-dd'),
  });

  useEffect(() => {
    fetchData();
  }, [dateRange]);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [summaryData, categoryData] = await Promise.all([
        bankingService.getTransactionsSummary(dateRange.from, dateRange.to),
        bankingService.getTransactionsByCategory(dateRange.from, dateRange.to),
      ]);

      setSummary(summaryData);
      setCategories(categoryData);

      // Generate monthly data for charts (mock for now, should come from API)
      const months = [];
      for (let i = 5; i >= 0; i--) {
        const date = subMonths(new Date(), i);
        months.push({
          month: format(date, 'MMM', { locale: ptBR }),
          income: Math.random() * 10000 + 5000,
          expenses: Math.random() * 8000 + 3000,
        });
      }
      setMonthlyData(months);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <LoadingSpinner />
      </div>
    );
  }

  if (!summary) {
    return null;
  }

  // Process category data for pie chart
  const categoryChartData = Object.entries(categories || {})
    .filter(([key]) => key.includes('_DEBIT'))
    .map(([key, value]) => ({
      name: key.replace('_DEBIT', ''),
      value: value,
    }))
    .slice(0, 5); // Top 5 categories

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

  return (
    <div className={cn('space-y-6', className)}>
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Balance */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-gray-600">
                Saldo Total
              </CardTitle>
              <BanknotesIcon className="h-4 w-4 text-gray-400" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {bankingService.formatCurrency(summary.balance, 'BRL')}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {summary.accounts_count} contas conectadas
            </p>
          </CardContent>
        </Card>

        {/* Income */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-gray-600">
                Entradas
              </CardTitle>
              <ArrowTrendingUpIcon className="h-4 w-4 text-green-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {bankingService.formatCurrency(summary.income, 'BRL')}
            </div>
            <p className="text-xs text-gray-500 mt-1">Período atual</p>
          </CardContent>
        </Card>

        {/* Expenses */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-gray-600">
                Saídas
              </CardTitle>
              <ArrowTrendingDownIcon className="h-4 w-4 text-red-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {bankingService.formatCurrency(summary.expenses, 'BRL')}
            </div>
            <p className="text-xs text-gray-500 mt-1">Período atual</p>
          </CardContent>
        </Card>

        {/* Transactions Count */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-gray-600">
                Transações
              </CardTitle>
              <CalendarDaysIcon className="h-4 w-4 text-gray-400" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.transactions_count}</div>
            <p className="text-xs text-gray-500 mt-1">
              {format(new Date(summary.period_start), 'dd/MM', { locale: ptBR })} -{' '}
              {format(new Date(summary.period_end), 'dd/MM', { locale: ptBR })}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Income vs Expenses */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-medium">
                Receitas vs Despesas
              </CardTitle>
              <ChartBarIcon className="h-5 w-5 text-gray-400" />
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value: any) => bankingService.formatCurrency(value, 'BRL')} />
                <Legend />
                <Bar dataKey="income" name="Entradas" fill="#10B981" />
                <Bar dataKey="expenses" name="Saídas" fill="#EF4444" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Category Breakdown */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-medium">
                Despesas por Categoria
              </CardTitle>
              <ChartPieIcon className="h-5 w-5 text-gray-400" />
            </div>
          </CardHeader>
          <CardContent>
            {categoryChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={categoryChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => entry.name}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {categoryChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: any) => bankingService.formatCurrency(value, 'BRL')} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-gray-500">
                Sem dados de categoria disponíveis
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Trend Line */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-medium">Tendência Mensal</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(value: any) => bankingService.formatCurrency(value, 'BRL')} />
              <Legend />
              <Line
                type="monotone"
                dataKey="income"
                name="Entradas"
                stroke="#10B981"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="expenses"
                name="Saídas"
                stroke="#EF4444"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}