'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { bankingService } from '@/services/banking.service';
import { Transaction, FinancialSummary } from '@/types/banking';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { formatCurrency } from '@/lib/utils';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import {
  DocumentArrowDownIcon,
  CalendarIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon
} from '@heroicons/react/24/outline';
import { format, startOfMonth, endOfMonth, subMonths, subYears, parseISO, startOfYear, endOfYear } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface PeriodFilter {
  label: string;
  startDate: Date | null;
  endDate: Date | null;
}

const CHART_COLORS = [
  '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
  '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'
];

export default function ReportsPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [isLoading, setIsLoading] = useState(true);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [summary, setSummary] = useState<FinancialSummary | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<PeriodFilter>({
    label: 'Mês atual',
    startDate: startOfMonth(new Date()),
    endDate: endOfMonth(new Date())
  });

  const periods: PeriodFilter[] = [
    {
      label: 'Todas',
      startDate: new Date('2020-01-01'), // Far enough back to get all transactions
      endDate: new Date()
    },
    {
      label: 'Mês atual',
      startDate: startOfMonth(new Date()),
      endDate: endOfMonth(new Date())
    },
    {
      label: 'Últimos 3 meses',
      startDate: new Date(new Date().setDate(new Date().getDate() - 90)),
      endDate: new Date()
    },
    {
      label: 'Últimos 6 meses',
      startDate: new Date(new Date().setDate(new Date().getDate() - 180)),
      endDate: new Date()
    },
    {
      label: 'Ano atual',
      startDate: startOfYear(new Date()),
      endDate: new Date()
    },
    {
      label: 'Ano anterior',
      startDate: startOfYear(subYears(new Date(), 1)),
      endDate: endOfYear(subYears(new Date(), 1))
    }
  ];

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    let cancelled = false;

    const fetchReportData = async () => {
      setIsLoading(true);
      try {
        const filters: any = {};
        if (selectedPeriod.startDate) {
          filters.date_from = selectedPeriod.startDate.toISOString().split('T')[0];
        }
        if (selectedPeriod.endDate) {
          filters.date_to = selectedPeriod.endDate.toISOString().split('T')[0];
        }

        const [transactionsData, summaryData] = await Promise.all([
          bankingService.getTransactions(filters),
          bankingService.getTransactionsSummary(
            filters.date_from,
            filters.date_to
          )
        ]);

        if (!cancelled) {
          console.log('Transações carregadas:', transactionsData);
          console.log('Summary:', summaryData);
          setTransactions(transactionsData);
          setSummary(summaryData);
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Erro ao carregar relatórios:', error);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    fetchReportData();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, router, selectedPeriod.label]);

  const handleExportPDF = () => {
    window.print();
  };

  const handleExportExcel = () => {
    const csvContent = [
      ['Data', 'Descrição', 'Categoria', 'Tipo', 'Valor'],
      ...transactions.map(t => [
        format(parseISO(t.date), 'dd/MM/yyyy'),
        t.description,
        t.category || 'Sem categoria',
        t.type === 'CREDIT' ? 'Receita' : 'Despesa',
        t.amount.toString()
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `relatorio-${format(new Date(), 'yyyy-MM-dd')}.csv`;
    link.click();
  };

  // Processar dados para gráficos
  const getCategoryData = () => {
    if (!transactions || transactions.length === 0) {
      console.log('No transactions for categories');
      return [];
    }

    console.log('Processing categories from transactions:', transactions);

    const categoryMap: Record<string, number> = {};

    // Processar todas as despesas (amount negativo OU type DEBIT)
    transactions.forEach(t => {
      console.log(`Transaction: ${t.description}, type: ${t.type}, amount: ${t.amount}, is_expense: ${t.is_expense}`);

      // Usar is_expense do backend
      if (t.is_expense) {
        const cat = t.category || 'Sem categoria';
        categoryMap[cat] = (categoryMap[cat] || 0) + Math.abs(t.amount);
      }
    });

    console.log('Category map:', categoryMap);

    const result = Object.entries(categoryMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([name, value]) => ({ name, value }));

    console.log('Category data result:', result);
    return result;
  };

  const getMonthlyData = () => {
    if (!transactions || transactions.length === 0) return [];

    const monthMap: Record<string, { receitas: number; despesas: number }> = {};

    transactions.forEach(t => {
      const month = format(parseISO(t.date), 'MMM/yy', { locale: ptBR });
      if (!monthMap[month]) {
        monthMap[month] = { receitas: 0, despesas: 0 };
      }

      // Usar is_income e is_expense do backend
      if (t.is_income) {
        monthMap[month].receitas += Math.abs(t.amount);
      }
      if (t.is_expense) {
        monthMap[month].despesas += Math.abs(t.amount);
      }
    });

    const result = Object.entries(monthMap)
      .map(([mes, data]) => ({
        mes,
        receitas: data.receitas,
        despesas: data.despesas
      }))
      .slice(-12);

    console.log('Monthly data:', result);
    return result;
  };

  const getDailyBalanceData = () => {
    if (!transactions || transactions.length === 0) return [];

    const dailyMap: Record<string, number> = {};
    let runningBalance = 0;

    transactions
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .forEach(t => {
        const day = format(parseISO(t.date), 'dd MMM', { locale: ptBR });

        // Usar is_income e is_expense do backend
        if (t.is_income) {
          runningBalance += Math.abs(t.amount);
        }
        if (t.is_expense) {
          runningBalance -= Math.abs(t.amount);
        }

        dailyMap[day] = runningBalance;
      });

    const result = Object.entries(dailyMap)
      .map(([dia, saldo]) => ({ dia, saldo }))
      .slice(-30);

    console.log('Daily balance data:', result);
    return result;
  };

  if (!isAuthenticated || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  const categoryData = getCategoryData();
  const monthlyData = getMonthlyData();
  const dailyBalanceData = getDailyBalanceData();
  // Expenses come as negative from API, balance is already calculated
  const monthlyResult = summary?.balance || 0;

  return (
    <div className="space-y-6 print:space-y-4">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 print:hidden">
        <div>
          <h1 className="text-3xl font-bold text-white">Relatórios Financeiros</h1>
          <p className="text-white/70 mt-1">
            Análise detalhada do seu desempenho financeiro
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExportExcel}>
            <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
            Excel
          </Button>
          <Button variant="outline" onClick={handleExportPDF}>
            <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
            PDF
          </Button>
        </div>
      </div>

      {/* Filtros de Período */}
      <Card className="print:hidden">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CalendarIcon className="h-5 w-5" />
            Período
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {periods.map((period) => (
              <Button
                key={period.label}
                variant={selectedPeriod.label === period.label ? 'default' : 'outline'}
                onClick={() => setSelectedPeriod(period)}
              >
                {period.label}
              </Button>
            ))}
          </div>
          <p className="text-sm text-white/60 mt-3">
            {selectedPeriod.startDate && selectedPeriod.endDate ? (
              <>
                {format(selectedPeriod.startDate, 'dd MMM yyyy', { locale: ptBR })} até{' '}
                {format(selectedPeriod.endDate, 'dd MMM yyyy', { locale: ptBR })}
              </>
            ) : (
              'Todas as transações disponíveis'
            )}
          </p>
        </CardContent>
      </Card>

      {/* Resumo Principal */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-white/70">
              Receitas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">
              {formatCurrency(summary?.income || 0)}
            </div>
            <div className="flex items-center gap-1 text-xs text-white/60 mt-1">
              <ArrowTrendingUpIcon className="h-3 w-3" />
              Entradas no período
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-white/70">
              Despesas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">
              {formatCurrency(Math.abs(summary?.expenses || 0))}
            </div>
            <div className="flex items-center gap-1 text-xs text-white/60 mt-1">
              <ArrowTrendingDownIcon className="h-3 w-3" />
              Saídas no período
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-white/70">
              Resultado
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${monthlyResult >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {monthlyResult >= 0 && '+'}{formatCurrency(monthlyResult)}
            </div>
            <div className="flex items-center gap-1 text-xs text-white/60 mt-1">
              <ChartBarIcon className="h-3 w-3" />
              Balanço do período
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-white/70">
              Transações
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {summary?.transactions_count || 0}
            </div>
            <div className="text-xs text-white/60 mt-1">
              Operações registradas
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gráfico de Evolução Mensal */}
        <Card>
          <CardHeader>
            <CardTitle>Receitas vs Despesas</CardTitle>
          </CardHeader>
          <CardContent>
            {monthlyData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={monthlyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="mes" stroke="rgba(255,255,255,0.7)" />
                  <YAxis stroke="rgba(255,255,255,0.7)" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px'
                    }}
                    formatter={(value: number) => formatCurrency(value)}
                  />
                  <Legend />
                  <Bar dataKey="receitas" fill="#10b981" name="Receitas" />
                  <Bar dataKey="despesas" fill="#ef4444" name="Despesas" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-white/60">
                <p>Nenhuma transação no período selecionado</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Gráfico de Categorias */}
        <Card>
          <CardHeader>
            <CardTitle>Despesas por Categoria</CardTitle>
          </CardHeader>
          <CardContent>
            {categoryData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px'
                    }}
                    formatter={(value: number) => formatCurrency(value)}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-white/60">
                <p>Nenhuma despesa categorizada no período</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Gráfico de Saldo ao Longo do Tempo */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Evolução do Saldo</CardTitle>
          </CardHeader>
          <CardContent>
            {dailyBalanceData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={dailyBalanceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="dia" stroke="rgba(255,255,255,0.7)" />
                  <YAxis stroke="rgba(255,255,255,0.7)" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px'
                    }}
                    formatter={(value: number) => formatCurrency(value)}
                  />
                  <Line
                    type="monotone"
                    dataKey="saldo"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ fill: '#3b82f6' }}
                    name="Saldo"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-white/60">
                <p>Nenhum dado de saldo disponível</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tabela de Categorias Detalhada */}
      <Card>
        <CardHeader>
          <CardTitle>Análise por Categoria</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left py-3 px-4 text-sm font-medium text-white/70">Categoria</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-white/70">Total</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-white/70">% do Total</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-white/70">Transações</th>
                </tr>
              </thead>
              <tbody>
                {categoryData.map((cat, index) => {
                  const totalExpenses = categoryData.reduce((sum, c) => sum + c.value, 0);
                  const percentage = (cat.value / totalExpenses) * 100;
                  const transactionCount = transactions.filter(
                    t => t.type === 'DEBIT' && (t.category || 'Sem categoria') === cat.name
                  ).length;

                  return (
                    <tr key={cat.name} className="border-b border-white/5 hover:bg-white/5">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }}
                          />
                          <span className="text-sm">{cat.name}</span>
                        </div>
                      </td>
                      <td className="text-right py-3 px-4 text-sm font-medium">
                        {formatCurrency(cat.value)}
                      </td>
                      <td className="text-right py-3 px-4 text-sm text-white/70">
                        {percentage.toFixed(1)}%
                      </td>
                      <td className="text-right py-3 px-4 text-sm text-white/70">
                        {transactionCount}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}