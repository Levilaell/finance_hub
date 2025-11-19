'use client';

import { useEffect, useState, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { bankingService } from '@/services/banking.service';
import { billsService } from '@/services/bills.service';
import { Transaction, FinancialSummary, CashFlowProjection } from '@/types/banking';
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
import { Input } from '@/components/ui/input';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import html2canvas from 'html2canvas';
import { toast } from 'sonner';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ChartHelpTooltip } from '@/components/ui/chart-help-tooltip';

interface PeriodFilter {
  label: string;
  startDate: Date | null;
  endDate: Date | null;
}

type ReportType = 'complete' | 'summary' | 'categories' | 'monthly';

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
  const [cashFlowProjection, setCashFlowProjection] = useState<CashFlowProjection[]>([]);
  const [actualCashFlow, setActualCashFlow] = useState<CashFlowProjection[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<PeriodFilter>({
    label: 'Mês atual',
    startDate: startOfMonth(new Date()),
    endDate: endOfMonth(new Date())
  });
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [showCustomPeriod, setShowCustomPeriod] = useState(false);

  const periods: PeriodFilter[] = [
    {
      label: 'Todas',
      startDate: null, // Sem filtros de data - carrega todas as transações
      endDate: null
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

        const [transactionsData, summaryData, cashFlowData, actualFlowData] = await Promise.all([
          bankingService.getTransactions(filters),
          // Se "Todas" (sem filtros de data), o backend retorna mês atual
          // Nesse caso, vamos calcular o summary localmente depois
          filters.date_from || filters.date_to
            ? bankingService.getTransactionsSummary(filters.date_from, filters.date_to)
            : Promise.resolve(null),
          billsService.getCashFlowProjection(),
          billsService.getActualCashFlow()
        ]);

        if (!cancelled) {
          setTransactions(transactionsData);

          // Se summaryData é null (período "Todas"), calcular localmente
          if (summaryData === null) {
            const income = transactionsData
              .filter(t => t.is_income)
              .reduce((sum, t) => sum + Math.abs(t.amount), 0);

            const expenses = transactionsData
              .filter(t => t.is_expense)
              .reduce((sum, t) => sum + Math.abs(t.amount), 0);

            setSummary({
              income,
              expenses: -expenses, // Negativo como o backend retorna
              balance: income - expenses,
              period_start: '',
              period_end: '',
              accounts_count: 0,
              transactions_count: transactionsData.length
            });
          } else {
            setSummary(summaryData);
          }

          setCashFlowProjection(cashFlowData);
          setActualCashFlow(actualFlowData);
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

  // Otimização: useCallback para memoizar funções
  const applyCustomPeriod = useCallback(() => {
    if (!customStartDate || !customEndDate) {
      toast.error('Selecione data inicial e final');
      return;
    }

    const start = new Date(customStartDate);
    const end = new Date(customEndDate);

    if (start > end) {
      toast.error('Data inicial deve ser anterior à data final');
      return;
    }

    setSelectedPeriod({
      label: 'Personalizado',
      startDate: start,
      endDate: end
    });
    setShowCustomPeriod(false);
    toast.success('Período personalizado aplicado');
  }, [customStartDate, customEndDate]);

  const generatePDF = async (reportType: ReportType) => {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();

    // Header
    doc.setFontSize(20);
    doc.text('Relatório Financeiro', pageWidth / 2, 20, { align: 'center' });

    doc.setFontSize(10);
    const periodText = selectedPeriod.startDate && selectedPeriod.endDate
      ? `${format(selectedPeriod.startDate, 'dd/MM/yyyy')} - ${format(selectedPeriod.endDate, 'dd/MM/yyyy')}`
      : 'Todas as transações';
    doc.text(periodText, pageWidth / 2, 28, { align: 'center' });

    let yPosition = 40;

    // Summary cards
    if (reportType === 'complete' || reportType === 'summary') {
      doc.setFontSize(14);
      doc.text('Resumo Financeiro', 14, yPosition);
      yPosition += 10;

      const summaryData = [
        ['Receitas', formatCurrency(summary?.income || 0)],
        ['Despesas', formatCurrency(Math.abs(summary?.expenses || 0))],
        ['Resultado', formatCurrency(summary?.balance || 0)],
        ['Transações', (summary?.transactions_count || 0).toString()]
      ];

      autoTable(doc, {
        startY: yPosition,
        head: [['Métrica', 'Valor']],
        body: summaryData,
        theme: 'grid',
        headStyles: { fillColor: [59, 130, 246] },
      });

      yPosition = (doc as any).lastAutoTable.finalY + 15;
    }

    // Income Categories table
    if (reportType === 'complete' || reportType === 'categories') {
      if (incomeCategoryData.length > 0) {
        doc.setFontSize(14);
        doc.text('Receitas por Categoria', 14, yPosition);
        yPosition += 10;

        const incomeCategoryTableData = incomeCategoryData.map((cat, index) => {
          const totalIncome = incomeCategoryData.reduce((sum, c) => sum + c.value, 0);
          const percentage = ((cat.value / totalIncome) * 100).toFixed(1);
          const transactionCount = transactions.filter(
            t => t.type === 'CREDIT' && (t.category || 'Sem categoria') === cat.name
          ).length;

          return [
            cat.name,
            formatCurrency(cat.value),
            `${percentage}%`,
            transactionCount.toString()
          ];
        });

        autoTable(doc, {
          startY: yPosition,
          head: [['Categoria', 'Total', '% do Total', 'Transações']],
          body: incomeCategoryTableData,
          theme: 'grid',
          headStyles: { fillColor: [16, 185, 129] },
        });

        yPosition = (doc as any).lastAutoTable.finalY + 15;
      }

      // Expense Categories table
      if (categoryData.length > 0) {
        if (yPosition > 230) {
          doc.addPage();
          yPosition = 20;
        }

        doc.setFontSize(14);
        doc.text('Despesas por Categoria', 14, yPosition);
        yPosition += 10;

        const categoryTableData = categoryData.map((cat, index) => {
          const totalExpenses = categoryData.reduce((sum, c) => sum + c.value, 0);
          const percentage = ((cat.value / totalExpenses) * 100).toFixed(1);
          const transactionCount = transactions.filter(
            t => t.type === 'DEBIT' && (t.category || 'Sem categoria') === cat.name
          ).length;

          return [
            cat.name,
            formatCurrency(cat.value),
            `${percentage}%`,
            transactionCount.toString()
          ];
        });

        autoTable(doc, {
          startY: yPosition,
          head: [['Categoria', 'Total', '% do Total', 'Transações']],
          body: categoryTableData,
          theme: 'grid',
          headStyles: { fillColor: [239, 68, 68] },
        });

        yPosition = (doc as any).lastAutoTable.finalY + 15;
      }
    }

    // Monthly data
    if (reportType === 'complete' || reportType === 'monthly') {
      if (yPosition > 250) {
        doc.addPage();
        yPosition = 20;
      }

      doc.setFontSize(14);
      doc.text('Receitas vs Despesas Mensais', 14, yPosition);
      yPosition += 10;

      const monthlyTableData = monthlyData.map(month => [
        month.mes,
        formatCurrency(month.receitas),
        formatCurrency(month.despesas),
        formatCurrency(month.receitas - month.despesas)
      ]);

      autoTable(doc, {
        startY: yPosition,
        head: [['Mês', 'Receitas', 'Despesas', 'Saldo']],
        body: monthlyTableData,
        theme: 'grid',
        headStyles: { fillColor: [59, 130, 246] },
      });
    }

    // Footer
    const pageCount = doc.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.text(
        `Página ${i} de ${pageCount}`,
        pageWidth / 2,
        doc.internal.pageSize.getHeight() - 10,
        { align: 'center' }
      );
    }

    const dateRange = selectedPeriod.label === 'Personalizado' && customStartDate && customEndDate
      ? `_${customStartDate}_a_${customEndDate}`
      : `_${selectedPeriod.label.toLowerCase().replace(/\s/g, '-')}`;

    const reportTypeLabel = reportType === 'complete' ? 'completo'
      : reportType === 'summary' ? 'resumo'
      : reportType === 'categories' ? 'categorias'
      : 'mensal';

    doc.save(`relatorio_${reportTypeLabel}${dateRange}_${format(new Date(), 'yyyy-MM-dd')}.pdf`);
    toast.success('PDF gerado com sucesso!');
  };

  // Processar dados para gráficos - Otimização: useMemo para evitar recálculos
  const categoryData = useMemo(() => {
    if (!transactions || transactions.length === 0) {
      return [];
    }

    const categoryMap: Record<string, number> = {};

    // Processar todas as despesas (amount negativo OU type DEBIT)
    transactions.forEach(t => {
      // Usar is_expense do backend
      if (t.is_expense) {
        const cat = t.category || 'Sem categoria';
        categoryMap[cat] = (categoryMap[cat] || 0) + Math.abs(t.amount);
      }
    });

    return Object.entries(categoryMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([name, value]) => ({ name, value }));
  }, [transactions]);

  const incomeCategoryData = useMemo(() => {
    if (!transactions || transactions.length === 0) {
      return [];
    }

    const categoryMap: Record<string, number> = {};

    // Processar todas as receitas
    transactions.forEach(t => {
      if (t.is_income) {
        const cat = t.category || 'Sem categoria';
        categoryMap[cat] = (categoryMap[cat] || 0) + Math.abs(t.amount);
      }
    });

    return Object.entries(categoryMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([name, value]) => ({ name, value }));
  }, [transactions]);

  const monthlyData = useMemo(() => {
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

    return Object.entries(monthMap)
      .map(([mes, data]) => ({
        mes,
        receitas: data.receitas,
        despesas: data.despesas
      }))
      .slice(-12);
  }, [transactions]);

  const dailyBalanceData = useMemo(() => {
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

    return Object.entries(dailyMap)
      .map(([dia, saldo]) => ({ dia, saldo }))
      .slice(-30);
  }, [transactions]);

  if (!isAuthenticated || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

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
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
                Exportar PDF
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => generatePDF('complete')}>
                Relatório Completo
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => generatePDF('summary')}>
                Resumo Financeiro
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => generatePDF('categories')}>
                Análise por Categorias
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => generatePDF('monthly')}>
                Análise Mensal
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
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
                onClick={() => {
                  setSelectedPeriod(period);
                  setShowCustomPeriod(false);
                }}
              >
                {period.label}
              </Button>
            ))}
            <Button
              variant={selectedPeriod.label === 'Personalizado' ? 'default' : 'outline'}
              onClick={() => setShowCustomPeriod(!showCustomPeriod)}
            >
              Personalizado
            </Button>
          </div>

          {showCustomPeriod && (
            <div className="mt-4 p-4 bg-white/5 rounded-lg">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label className="text-sm font-medium mb-2 block">Data Inicial</label>
                  <Input
                    type="date"
                    value={customStartDate}
                    onChange={(e) => setCustomStartDate(e.target.value)}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Data Final</label>
                  <Input
                    type="date"
                    value={customEndDate}
                    onChange={(e) => setCustomEndDate(e.target.value)}
                  />
                </div>
                <div className="flex items-end">
                  <Button onClick={applyCustomPeriod} className="w-full">
                    Aplicar Período
                  </Button>
                </div>
              </div>
            </div>
          )}

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
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="flex items-center">
              Receitas vs Despesas
              <ChartHelpTooltip content="Compara o total de receitas (verde) e despesas (vermelho) mês a mês. Use para identificar meses de maior gasto e entender o padrão de entrada e saída de recursos ao longo do tempo." />
            </CardTitle>
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

        {/* Gráfico de Receitas por Categoria */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              Receitas por Categoria
              <ChartHelpTooltip content="Mostra a distribuição das suas receitas por categoria. Cada fatia representa o percentual de uma categoria no total das entradas. Útil para identificar suas principais fontes de renda." />
            </CardTitle>
          </CardHeader>
          <CardContent>
            {incomeCategoryData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={incomeCategoryData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {incomeCategoryData.map((entry, index) => (
                      <Cell key={`cell-income-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
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
                <p>Nenhuma receita categorizada no período</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Gráfico de Despesas por Categoria */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              Despesas por Categoria
              <ChartHelpTooltip content="Exibe a distribuição dos seus gastos por categoria. Cada fatia mostra o percentual de uma categoria no total das despesas. Fundamental para identificar onde você mais gasta e oportunidades de economia." />
            </CardTitle>
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
                      <Cell key={`cell-expense-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
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
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="flex items-center">
              Fluxo de Caixa Acumulado
              <ChartHelpTooltip content="Mostra a evolução do seu saldo ao longo do tempo, somando receitas e subtraindo despesas de forma acumulativa. A linha subindo indica crescimento financeiro, enquanto descendo indica consumo de recursos. Útil para visualizar a tendência geral das suas finanças." />
            </CardTitle>
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

      {/* Tabelas de Categorias Detalhadas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tabela de Receitas por Categoria */}
        <Card>
          <CardHeader>
            <CardTitle>Receitas por Categoria</CardTitle>
          </CardHeader>
          <CardContent>
            {incomeCategoryData.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/10">
                      <th className="text-left py-3 px-4 text-sm font-medium text-white/70">Categoria</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-white/70">Total</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-white/70">%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {incomeCategoryData.map((cat, index) => {
                      const totalIncome = incomeCategoryData.reduce((sum, c) => sum + c.value, 0);
                      const percentage = (cat.value / totalIncome) * 100;

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
                          <td className="text-right py-3 px-4 text-sm font-medium text-green-500">
                            {formatCurrency(cat.value)}
                          </td>
                          <td className="text-right py-3 px-4 text-sm text-white/70">
                            {percentage.toFixed(1)}%
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-8 text-center text-white/60">
                <p>Nenhuma receita categorizada no período</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Tabela de Despesas por Categoria */}
        <Card>
          <CardHeader>
            <CardTitle>Despesas por Categoria</CardTitle>
          </CardHeader>
          <CardContent>
            {categoryData.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/10">
                      <th className="text-left py-3 px-4 text-sm font-medium text-white/70">Categoria</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-white/70">Total</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-white/70">%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {categoryData.map((cat, index) => {
                      const totalExpenses = categoryData.reduce((sum, c) => sum + c.value, 0);
                      const percentage = (cat.value / totalExpenses) * 100;

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
                          <td className="text-right py-3 px-4 text-sm font-medium text-red-500">
                            {formatCurrency(cat.value)}
                          </td>
                          <td className="text-right py-3 px-4 text-sm text-white/70">
                            {percentage.toFixed(1)}%
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-8 text-center text-white/60">
                <p>Nenhuma despesa categorizada no período</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Gráficos de Fluxo de Caixa - Contas a Pagar/Receber */}
      <div className="grid grid-cols-1 gap-6">
        {/* Fluxo de Caixa Projetado (próximos 12 meses) */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              Fluxo de Caixa Projetado (Próximos 12 Meses)
              <ChartHelpTooltip content="Projeção futura baseada nas suas contas a pagar (vermelho) e a receber (verde) já cadastradas. O resultado (azul) mostra o saldo esperado por mês. Use para planejamento financeiro e identificar meses críticos ou oportunidades de investimento." />
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Previsão baseada em contas a pagar e receber
            </p>
          </CardHeader>
          <CardContent>
            {cashFlowProjection.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={cashFlowProjection}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis
                    dataKey="month"
                    stroke="rgba(255,255,255,0.5)"
                    tick={{ fill: 'rgba(255,255,255,0.7)' }}
                  />
                  <YAxis
                    stroke="rgba(255,255,255,0.5)"
                    tick={{ fill: 'rgba(255,255,255,0.7)' }}
                    tickFormatter={(value) => `R$ ${(value / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(0, 0, 0, 0.8)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      borderRadius: '8px'
                    }}
                    formatter={(value: any) => [formatCurrency(value), '']}
                    labelFormatter={(label) => {
                      const item = cashFlowProjection.find(d => d.month === label);
                      return item ? item.month_name : label;
                    }}
                  />
                  <Legend />
                  <Bar dataKey="receivable" name="A Receber" fill="#10b981" />
                  <Bar dataKey="payable" name="A Pagar" fill="#ef4444" />
                  <Bar dataKey="net" name="Resultado" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="py-8 text-center text-white/60">
                <p>Nenhuma projeção disponível</p>
                <p className="text-sm mt-2">Crie contas a pagar/receber para visualizar o fluxo de caixa projetado</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Gráfico Comparativo: Previsto vs Realizado */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              Previsto vs Realizado
              <ChartHelpTooltip content="Compara o que você planejou (linhas tracejadas) com o que realmente aconteceu (linhas sólidas) nas suas finanças. Linhas verdes são receitas, vermelhas são despesas. A diferença entre previsto e realizado ajuda a avaliar a precisão do seu planejamento financeiro." />
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Comparação entre contas previstas e pagas em /bills (não inclui transações bancárias)
            </p>
          </CardHeader>
          <CardContent>
            {actualCashFlow.length > 0 && cashFlowProjection.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart
                  data={actualCashFlow.map((actualItem) => {
                    const projection = cashFlowProjection.find(p => p.month === actualItem.month);
                    return {
                      month: actualItem.month_name,
                      realizado: actualItem.net,
                      previsto: projection ? projection.net : 0,
                      receitas_realizadas: actualItem.receivable_paid || actualItem.receivable,
                      receitas_previstas: projection?.receivable || 0,
                      despesas_realizadas: actualItem.payable_paid || actualItem.payable,
                      despesas_previstas: projection?.payable || 0
                    };
                  })}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis
                    dataKey="month"
                    stroke="rgba(255,255,255,0.5)"
                    tick={{ fill: 'rgba(255,255,255,0.7)' }}
                  />
                  <YAxis
                    stroke="rgba(255,255,255,0.5)"
                    tick={{ fill: 'rgba(255,255,255,0.7)' }}
                    tickFormatter={(value) => `R$ ${(value / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(0, 0, 0, 0.8)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      borderRadius: '8px'
                    }}
                    formatter={(value: any) => [formatCurrency(value), '']}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="realizado"
                    name="Resultado Realizado (Contas)"
                    stroke="#10b981"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="previsto"
                    name="Resultado Previsto (Contas)"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                  />
                  <Line
                    type="monotone"
                    dataKey="receitas_realizadas"
                    name="Receitas Pagas"
                    stroke="#10b981"
                    strokeWidth={1}
                    opacity={0.5}
                  />
                  <Line
                    type="monotone"
                    dataKey="receitas_previstas"
                    name="Receitas Previstas"
                    stroke="#10b981"
                    strokeWidth={1}
                    strokeDasharray="3 3"
                    opacity={0.5}
                  />
                  <Line
                    type="monotone"
                    dataKey="despesas_realizadas"
                    name="Despesas Pagas"
                    stroke="#ef4444"
                    strokeWidth={1}
                    opacity={0.5}
                  />
                  <Line
                    type="monotone"
                    dataKey="despesas_previstas"
                    name="Despesas Previstas"
                    stroke="#ef4444"
                    strokeWidth={1}
                    strokeDasharray="3 3"
                    opacity={0.5}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="py-8 text-center text-white/60">
                <p>Dados insuficientes para comparação</p>
                <p className="text-sm mt-2">Crie contas em /bills para visualizar a comparação entre previsto e realizado</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}