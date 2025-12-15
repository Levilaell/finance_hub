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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  ResponsiveContainer,
  ComposedChart,
  Area
} from 'recharts';
import {
  DocumentArrowDownIcon,
  CalendarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  TableCellsIcon,
  ChartPieIcon,
  ArrowsRightLeftIcon,
  ScaleIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import Link from 'next/link';
import { format, startOfMonth, endOfMonth, subMonths, subYears, parseISO, startOfYear, endOfYear } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Input } from '@/components/ui/input';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { toast } from 'sonner';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import { ChartHelpTooltip } from '@/components/ui/chart-help-tooltip';
import * as XLSX from 'xlsx';

interface PeriodFilter {
  label: string;
  startDate: Date | null;
  endDate: Date | null;
}

type ExportFormat = 'pdf' | 'xlsx' | 'csv';
type ExportSection = 'all' | 'overview' | 'categories' | 'cashflow' | 'comparison';

const CHART_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'
];

export default function ReportsPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [isLoading, setIsLoading] = useState(true);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [cashFlowProjection, setCashFlowProjection] = useState<CashFlowProjection[]>([]);
  const [actualCashFlow, setActualCashFlow] = useState<CashFlowProjection[]>([]);
  const [previousPeriodSummary, setPreviousPeriodSummary] = useState<FinancialSummary | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
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
      startDate: null,
      endDate: null
    },
    {
      label: 'Mês atual',
      startDate: startOfMonth(new Date()),
      endDate: endOfMonth(new Date())
    },
    {
      label: 'Últimos 3 meses',
      startDate: startOfMonth(subMonths(new Date(), 2)),
      endDate: endOfMonth(new Date())
    },
    {
      label: 'Últimos 6 meses',
      startDate: startOfMonth(subMonths(new Date(), 5)),
      endDate: endOfMonth(new Date())
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

        // Calcular período anterior para comparação (baseado em meses)
        let previousFilters: any = {};
        if (selectedPeriod.startDate && selectedPeriod.endDate) {
          // Calcular quantos meses o período abrange
          const startMonth = selectedPeriod.startDate.getMonth();
          const startYear = selectedPeriod.startDate.getFullYear();
          const endMonth = selectedPeriod.endDate.getMonth();
          const endYear = selectedPeriod.endDate.getFullYear();
          const monthsInPeriod = (endYear - startYear) * 12 + (endMonth - startMonth) + 1;

          // Período anterior: mesmo número de meses, terminando antes do período atual
          const previousEnd = new Date(selectedPeriod.startDate);
          previousEnd.setDate(previousEnd.getDate() - 1); // Último dia antes do período atual
          const previousStart = startOfMonth(subMonths(selectedPeriod.startDate, monthsInPeriod));

          previousFilters = {
            date_from: previousStart.toISOString().split('T')[0],
            date_to: previousEnd.toISOString().split('T')[0]
          };
        }

        const [transactionsData, cashFlowData, actualFlowData, previousSummaryData] = await Promise.all([
          bankingService.getTransactions(filters),
          billsService.getCashFlowProjection(),
          billsService.getActualCashFlow(),
          previousFilters.date_from
            ? bankingService.getTransactionsSummary(previousFilters.date_from, previousFilters.date_to).catch(() => null)
            : Promise.resolve(null)
        ]);

        if (!cancelled) {
          setTransactions(transactionsData);
          setPreviousPeriodSummary(previousSummaryData);
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

  // Calcular resumo diretamente das transações para consistência com gráficos
  // Filtra transações pelo período selecionado (frontend) para garantir consistência
  const filteredTransactions = useMemo(() => {
    if (!transactions || transactions.length === 0) return [];

    // Se não há período selecionado, retorna todas
    if (!selectedPeriod.startDate && !selectedPeriod.endDate) {
      return transactions;
    }

    return transactions.filter(t => {
      const txDate = t.date.substring(0, 10); // "2025-09-15"

      if (selectedPeriod.startDate) {
        const startStr = selectedPeriod.startDate.toISOString().substring(0, 10);
        if (txDate < startStr) return false;
      }

      if (selectedPeriod.endDate) {
        const endStr = selectedPeriod.endDate.toISOString().substring(0, 10);
        if (txDate > endStr) return false;
      }

      return true;
    });
  }, [transactions, selectedPeriod.startDate, selectedPeriod.endDate]);

  const calculatedSummary = useMemo(() => {
    if (!filteredTransactions || filteredTransactions.length === 0) {
      return { income: 0, expenses: 0, balance: 0, transactions_count: 0 };
    }

    const income = filteredTransactions
      .filter(t => t.is_income)
      .reduce((sum, t) => sum + Math.abs(t.amount), 0);

    const expenses = filteredTransactions
      .filter(t => t.is_expense)
      .reduce((sum, t) => sum + Math.abs(t.amount), 0);


    return {
      income,
      expenses: -expenses,
      balance: income - expenses,
      transactions_count: filteredTransactions.length
    };
  }, [filteredTransactions, selectedPeriod.label]);

  // Dados processados para gráficos (usa filteredTransactions para consistência)
  const categoryData = useMemo(() => {
    if (!filteredTransactions || filteredTransactions.length === 0) return [];

    const categoryMap: Record<string, number> = {};
    filteredTransactions.forEach(t => {
      if (t.is_expense) {
        const cat = t.category || 'Sem categoria';
        categoryMap[cat] = (categoryMap[cat] || 0) + Math.abs(t.amount);
      }
    });

    return Object.entries(categoryMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([name, value]) => ({ name, value }));
  }, [filteredTransactions]);

  const incomeCategoryData = useMemo(() => {
    if (!filteredTransactions || filteredTransactions.length === 0) return [];

    const categoryMap: Record<string, number> = {};
    filteredTransactions.forEach(t => {
      if (t.is_income) {
        const cat = t.category || 'Sem categoria';
        categoryMap[cat] = (categoryMap[cat] || 0) + Math.abs(t.amount);
      }
    });

    return Object.entries(categoryMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([name, value]) => ({ name, value }));
  }, [filteredTransactions]);

  const monthlyData = useMemo(() => {
    if (!filteredTransactions || filteredTransactions.length === 0) return [];

    // Agrupar por mês usando chave YYYY-MM para ordenação correta
    // Usar apenas a parte da data (YYYY-MM-DD) para evitar problemas de timezone
    const monthMap: Record<string, { receitas: number; despesas: number }> = {};
    filteredTransactions.forEach(t => {
      // Extrair YYYY-MM diretamente da string ISO (evita conversão de timezone)
      const sortKey = t.date.substring(0, 7); // "2025-09-15T..." -> "2025-09"

      if (!monthMap[sortKey]) {
        monthMap[sortKey] = { receitas: 0, despesas: 0 };
      }
      if (t.is_income) {
        monthMap[sortKey].receitas += Math.abs(t.amount);
      }
      if (t.is_expense) {
        monthMap[sortKey].despesas += Math.abs(t.amount);
      }
    });

    // Ordenar por chave YYYY-MM (ordem cronológica crescente)
    const result = Object.entries(monthMap)
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([key, data]) => {
        // Converter sortKey de volta para nome do mês
        const [year, month] = key.split('-');
        const date = new Date(parseInt(year), parseInt(month) - 1, 1);
        return {
          mes: format(date, 'MMM/yy', { locale: ptBR }),
          receitas: data.receitas,
          despesas: data.despesas,
          resultado: data.receitas - data.despesas
        };
      })
      .slice(-12);

    return result;
  }, [filteredTransactions]);

  const dailyBalanceData = useMemo(() => {
    if (!filteredTransactions || filteredTransactions.length === 0) return [];

    const dailyMap: Record<string, number> = {};
    let runningBalance = 0;

    filteredTransactions
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .forEach(t => {
        const day = format(parseISO(t.date), 'dd/MM', { locale: ptBR });
        if (t.is_income) runningBalance += Math.abs(t.amount);
        if (t.is_expense) runningBalance -= Math.abs(t.amount);
        dailyMap[day] = runningBalance;
      });

    return Object.entries(dailyMap)
      .map(([dia, saldo]) => ({ dia, saldo }))
      .slice(-30);
  }, [filteredTransactions]);

  // Cálculos de comparação (usa calculatedSummary para consistência)
  const comparisonData = useMemo(() => {
    if (!previousPeriodSummary || calculatedSummary.transactions_count === 0) return null;

    const incomeChange = previousPeriodSummary.income > 0
      ? ((calculatedSummary.income - previousPeriodSummary.income) / previousPeriodSummary.income) * 100
      : 0;

    const expenseChange = Math.abs(previousPeriodSummary.expenses) > 0
      ? ((Math.abs(calculatedSummary.expenses) - Math.abs(previousPeriodSummary.expenses)) / Math.abs(previousPeriodSummary.expenses)) * 100
      : 0;

    return {
      incomeChange,
      expenseChange,
      previousIncome: previousPeriodSummary.income,
      previousExpenses: Math.abs(previousPeriodSummary.expenses)
    };
  }, [calculatedSummary, previousPeriodSummary]);

  // Taxa de poupança (usa calculatedSummary para consistência)
  const savingsRate = useMemo(() => {
    if (calculatedSummary.income === 0) return 0;
    return (calculatedSummary.balance / calculatedSummary.income) * 100;
  }, [calculatedSummary]);

  // Funções de exportação
  const exportToExcel = useCallback((section: ExportSection) => {
    const wb = XLSX.utils.book_new();

    if (section === 'all' || section === 'overview') {
      const overviewData = [
        ['Relatório Financeiro'],
        ['Período', selectedPeriod.startDate && selectedPeriod.endDate
          ? `${format(selectedPeriod.startDate, 'dd/MM/yyyy')} - ${format(selectedPeriod.endDate, 'dd/MM/yyyy')}`
          : 'Todas as transações'],
        [],
        ['Resumo'],
        ['Receitas', calculatedSummary.income],
        ['Despesas', Math.abs(calculatedSummary.expenses)],
        ['Resultado', calculatedSummary.balance],
        ['Taxa de Poupança', `${savingsRate.toFixed(1)}%`],
        ['Transações', calculatedSummary.transactions_count],
      ];
      const wsOverview = XLSX.utils.aoa_to_sheet(overviewData);
      XLSX.utils.book_append_sheet(wb, wsOverview, 'Visão Geral');
    }

    if (section === 'all' || section === 'categories') {
      if (categoryData.length > 0) {
        const expenseHeaders = ['Categoria', 'Valor', '% do Total'];
        const totalExpenses = categoryData.reduce((sum, c) => sum + c.value, 0);
        const expenseRows = categoryData.map(cat => [
          cat.name,
          cat.value,
          `${((cat.value / totalExpenses) * 100).toFixed(1)}%`
        ]);
        const wsExpenses = XLSX.utils.aoa_to_sheet([expenseHeaders, ...expenseRows]);
        XLSX.utils.book_append_sheet(wb, wsExpenses, 'Despesas por Categoria');
      }

      if (incomeCategoryData.length > 0) {
        const incomeHeaders = ['Categoria', 'Valor', '% do Total'];
        const totalIncome = incomeCategoryData.reduce((sum, c) => sum + c.value, 0);
        const incomeRows = incomeCategoryData.map(cat => [
          cat.name,
          cat.value,
          `${((cat.value / totalIncome) * 100).toFixed(1)}%`
        ]);
        const wsIncome = XLSX.utils.aoa_to_sheet([incomeHeaders, ...incomeRows]);
        XLSX.utils.book_append_sheet(wb, wsIncome, 'Receitas por Categoria');
      }
    }

    if (section === 'all' || section === 'cashflow') {
      if (monthlyData.length > 0) {
        const monthlyHeaders = ['Mês', 'Receitas', 'Despesas', 'Resultado'];
        const monthlyRows = monthlyData.map(m => [m.mes, m.receitas, m.despesas, m.resultado]);
        const wsMonthly = XLSX.utils.aoa_to_sheet([monthlyHeaders, ...monthlyRows]);
        XLSX.utils.book_append_sheet(wb, wsMonthly, 'Mensal');
      }
    }

    const fileName = `relatorio_${section}_${format(new Date(), 'yyyy-MM-dd')}.xlsx`;
    XLSX.writeFile(wb, fileName);
    toast.success('Excel exportado com sucesso!');
  }, [calculatedSummary, categoryData, incomeCategoryData, monthlyData, selectedPeriod, savingsRate]);

  const exportToCSV = useCallback((section: ExportSection) => {
    let csvContent = '';

    if (section === 'overview' || section === 'all') {
      csvContent += 'Resumo Financeiro\n';
      csvContent += `Receitas,${calculatedSummary.income}\n`;
      csvContent += `Despesas,${Math.abs(calculatedSummary.expenses)}\n`;
      csvContent += `Resultado,${calculatedSummary.balance}\n`;
      csvContent += `Taxa de Poupança,${savingsRate.toFixed(1)}%\n\n`;
    }

    if (section === 'categories' || section === 'all') {
      if (categoryData.length > 0) {
        csvContent += 'Despesas por Categoria\n';
        csvContent += 'Categoria,Valor,Percentual\n';
        const totalExpenses = categoryData.reduce((sum, c) => sum + c.value, 0);
        categoryData.forEach(cat => {
          csvContent += `${cat.name},${cat.value},${((cat.value / totalExpenses) * 100).toFixed(1)}%\n`;
        });
        csvContent += '\n';
      }
    }

    if (section === 'cashflow' || section === 'all') {
      if (monthlyData.length > 0) {
        csvContent += 'Dados Mensais\n';
        csvContent += 'Mês,Receitas,Despesas,Resultado\n';
        monthlyData.forEach(m => {
          csvContent += `${m.mes},${m.receitas},${m.despesas},${m.resultado}\n`;
        });
      }
    }

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `relatorio_${section}_${format(new Date(), 'yyyy-MM-dd')}.csv`;
    link.click();
    toast.success('CSV exportado com sucesso!');
  }, [calculatedSummary, categoryData, monthlyData, savingsRate]);

  const generatePDF = useCallback((section: ExportSection) => {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();

    doc.setFontSize(20);
    doc.text('Relatório Financeiro', pageWidth / 2, 20, { align: 'center' });

    doc.setFontSize(10);
    const periodText = selectedPeriod.startDate && selectedPeriod.endDate
      ? `${format(selectedPeriod.startDate, 'dd/MM/yyyy')} - ${format(selectedPeriod.endDate, 'dd/MM/yyyy')}`
      : 'Todas as transações';
    doc.text(periodText, pageWidth / 2, 28, { align: 'center' });

    let yPosition = 40;

    if (section === 'all' || section === 'overview') {
      doc.setFontSize(14);
      doc.text('Resumo Financeiro', 14, yPosition);
      yPosition += 10;

      const summaryTableData = [
        ['Receitas', formatCurrency(calculatedSummary.income)],
        ['Despesas', formatCurrency(Math.abs(calculatedSummary.expenses))],
        ['Resultado', formatCurrency(calculatedSummary.balance)],
        ['Taxa de Poupança', `${savingsRate.toFixed(1)}%`],
        ['Transações', calculatedSummary.transactions_count.toString()]
      ];

      autoTable(doc, {
        startY: yPosition,
        head: [['Métrica', 'Valor']],
        body: summaryTableData,
        theme: 'grid',
        headStyles: { fillColor: [59, 130, 246] },
      });

      yPosition = (doc as any).lastAutoTable.finalY + 15;
    }

    if (section === 'all' || section === 'categories') {
      if (categoryData.length > 0) {
        if (yPosition > 230) {
          doc.addPage();
          yPosition = 20;
        }

        doc.setFontSize(14);
        doc.text('Top Despesas por Categoria', 14, yPosition);
        yPosition += 10;

        const totalExpenses = categoryData.reduce((sum, c) => sum + c.value, 0);
        const categoryTableData = categoryData.slice(0, 5).map(cat => [
          cat.name,
          formatCurrency(cat.value),
          `${((cat.value / totalExpenses) * 100).toFixed(1)}%`
        ]);

        autoTable(doc, {
          startY: yPosition,
          head: [['Categoria', 'Total', '% do Total']],
          body: categoryTableData,
          theme: 'grid',
          headStyles: { fillColor: [239, 68, 68] },
        });

        yPosition = (doc as any).lastAutoTable.finalY + 15;
      }
    }

    if (section === 'all' || section === 'cashflow') {
      if (monthlyData.length > 0) {
        if (yPosition > 200) {
          doc.addPage();
          yPosition = 20;
        }

        doc.setFontSize(14);
        doc.text('Evolução Mensal', 14, yPosition);
        yPosition += 10;

        const monthlyTableData = monthlyData.map(month => [
          month.mes,
          formatCurrency(month.receitas),
          formatCurrency(month.despesas),
          formatCurrency(month.resultado)
        ]);

        autoTable(doc, {
          startY: yPosition,
          head: [['Mês', 'Receitas', 'Despesas', 'Resultado']],
          body: monthlyTableData,
          theme: 'grid',
          headStyles: { fillColor: [59, 130, 246] },
        });
      }
    }

    const pageCount = doc.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.text(
        `Página ${i} de ${pageCount} - Gerado em ${format(new Date(), 'dd/MM/yyyy HH:mm')}`,
        pageWidth / 2,
        doc.internal.pageSize.getHeight() - 10,
        { align: 'center' }
      );
    }

    doc.save(`relatorio_${section}_${format(new Date(), 'yyyy-MM-dd')}.pdf`);
    toast.success('PDF gerado com sucesso!');
  }, [calculatedSummary, categoryData, monthlyData, selectedPeriod, savingsRate]);

  if (!isAuthenticated || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  const monthlyResult = calculatedSummary.balance;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Relatórios</h1>
          <p className="text-white/60 text-sm mt-1">
            {selectedPeriod.startDate && selectedPeriod.endDate
              ? `${format(selectedPeriod.startDate, 'dd MMM', { locale: ptBR })} - ${format(selectedPeriod.endDate, 'dd MMM yyyy', { locale: ptBR })}`
              : 'Todas as transações'}
          </p>
        </div>

        <div className="flex gap-2">
          {/* Link DRE */}
          <Link href="/reports/dre">
            <Button variant="outline" size="sm" className="text-white border-white/20 hover:bg-white/10">
              <DocumentTextIcon className="h-4 w-4 mr-2" />
              DRE
            </Button>
          </Link>

          {/* Filtro de período */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="text-white border-white/20 hover:bg-white/10">
                <CalendarIcon className="h-4 w-4 mr-2" />
                {selectedPeriod.label}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Período</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {periods.map((period) => (
                <DropdownMenuItem
                  key={period.label}
                  onClick={() => {
                    setSelectedPeriod(period);
                    setShowCustomPeriod(false);
                  }}
                  className={selectedPeriod.label === period.label ? 'bg-white/10' : ''}
                >
                  {period.label}
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setShowCustomPeriod(!showCustomPeriod)}>
                Personalizado...
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Exportação */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="text-white border-white/20 hover:bg-white/10">
                <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
                Exportar
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>PDF</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => generatePDF('all')}>
                Relatório Completo
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => generatePDF('overview')}>
                Apenas Resumo
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => generatePDF('categories')}>
                Apenas Categorias
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuLabel>Excel</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => exportToExcel('all')}>
                Relatório Completo (.xlsx)
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => exportToExcel('categories')}>
                Categorias (.xlsx)
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuLabel>CSV</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => exportToCSV('all')}>
                Dados Completos (.csv)
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Período personalizado */}
      {showCustomPeriod && (
        <Card>
          <CardContent className="pt-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="text-sm font-medium mb-2 block text-white/70">Data Inicial</label>
                <Input
                  type="date"
                  value={customStartDate}
                  onChange={(e) => setCustomStartDate(e.target.value)}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block text-white/70">Data Final</label>
                <Input
                  type="date"
                  value={customEndDate}
                  onChange={(e) => setCustomEndDate(e.target.value)}
                />
              </div>
              <div className="flex items-end">
                <Button onClick={applyCustomPeriod} className="w-full">
                  Aplicar
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Cards de Resumo Compactos */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Card className="bg-card/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-white/60 uppercase tracking-wide">Receitas</p>
                <p className="text-lg font-bold text-green-500 mt-1">
                  {formatCurrency(calculatedSummary.income)}
                </p>
              </div>
              <ArrowTrendingUpIcon className="h-8 w-8 text-green-500/30" />
            </div>
            {comparisonData && (
              <p className={`text-xs mt-2 ${comparisonData.incomeChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {comparisonData.incomeChange >= 0 ? '+' : ''}{comparisonData.incomeChange.toFixed(1)}% vs período anterior
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="bg-card/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-white/60 uppercase tracking-wide">Despesas</p>
                <p className="text-lg font-bold text-red-500 mt-1">
                  {formatCurrency(Math.abs(calculatedSummary.expenses))}
                </p>
              </div>
              <ArrowTrendingDownIcon className="h-8 w-8 text-red-500/30" />
            </div>
            {comparisonData && (
              <p className={`text-xs mt-2 ${comparisonData.expenseChange <= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {comparisonData.expenseChange >= 0 ? '+' : ''}{comparisonData.expenseChange.toFixed(1)}% vs período anterior
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="bg-card/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-white/60 uppercase tracking-wide">Resultado</p>
                <p className={`text-lg font-bold mt-1 ${monthlyResult >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {monthlyResult >= 0 && '+'}{formatCurrency(monthlyResult)}
                </p>
              </div>
              <ScaleIcon className={`h-8 w-8 ${monthlyResult >= 0 ? 'text-green-500/30' : 'text-red-500/30'}`} />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-white/60 uppercase tracking-wide">Taxa Poupança</p>
                <p className={`text-lg font-bold mt-1 ${savingsRate >= 0 ? 'text-blue-500' : 'text-red-500'}`}>
                  {savingsRate.toFixed(1)}%
                </p>
              </div>
              <ChartPieIcon className="h-8 w-8 text-blue-500/30" />
            </div>
            <p className="text-xs text-white/40 mt-2">
              do total de receitas
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Abas de Conteúdo */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4 lg:w-auto lg:inline-grid">
          <TabsTrigger value="overview" className="text-xs sm:text-sm">
            <ChartPieIcon className="h-4 w-4 mr-1 sm:mr-2 hidden sm:block" />
            Visão Geral
          </TabsTrigger>
          <TabsTrigger value="categories" className="text-xs sm:text-sm">
            <TableCellsIcon className="h-4 w-4 mr-1 sm:mr-2 hidden sm:block" />
            Categorias
          </TabsTrigger>
          <TabsTrigger value="cashflow" className="text-xs sm:text-sm">
            <ArrowsRightLeftIcon className="h-4 w-4 mr-1 sm:mr-2 hidden sm:block" />
            Fluxo de Caixa
          </TabsTrigger>
          <TabsTrigger value="comparison" className="text-xs sm:text-sm">
            <ScaleIcon className="h-4 w-4 mr-1 sm:mr-2 hidden sm:block" />
            Comparativo
          </TabsTrigger>
        </TabsList>

        {/* Tab: Visão Geral */}
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center">
                Receitas vs Despesas
                <ChartHelpTooltip content="Compara receitas e despesas por mês. Verde = receitas, Vermelho = despesas." />
              </CardTitle>
            </CardHeader>
            <CardContent>
              {monthlyData.length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                  <ComposedChart data={monthlyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="mes" stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 12 }} />
                    <YAxis stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 12 }} tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                      formatter={(value: number) => formatCurrency(value)}
                    />
                    <Legend />
                    <Bar dataKey="receitas" fill="#10b981" name="Receitas" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="despesas" fill="#ef4444" name="Despesas" radius={[4, 4, 0, 0]} />
                    <Line type="monotone" dataKey="resultado" stroke="#3b82f6" strokeWidth={2} name="Resultado" dot={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[350px] flex items-center justify-center text-white/60">
                  Nenhum dado disponível para o período
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center">
                Evolução do Saldo
                <ChartHelpTooltip content="Mostra como seu saldo evoluiu ao longo do tempo (acumulado)." />
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dailyBalanceData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={dailyBalanceData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="dia" stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 11 }} />
                    <YAxis stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                      formatter={(value: number) => formatCurrency(value)}
                    />
                    <defs>
                      <linearGradient id="colorSaldo" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <Area type="monotone" dataKey="saldo" stroke="#3b82f6" fill="url(#colorSaldo)" />
                    <Line type="monotone" dataKey="saldo" stroke="#3b82f6" strokeWidth={2} dot={false} name="Saldo" />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[250px] flex items-center justify-center text-white/60">
                  Nenhum dado disponível
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Categorias */}
        <TabsContent value="categories" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Top Despesas */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base text-red-400">Top Despesas</CardTitle>
              </CardHeader>
              <CardContent>
                {categoryData.length > 0 ? (
                  <div className="space-y-3">
                    {categoryData.slice(0, 5).map((cat, index) => {
                      const total = categoryData.reduce((sum, c) => sum + c.value, 0);
                      const percentage = (cat.value / total) * 100;
                      return (
                        <div key={cat.name} className="flex items-center gap-3">
                          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: CHART_COLORS[index] }} />
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-sm truncate">{cat.name}</span>
                              <span className="text-sm font-medium text-red-400">{formatCurrency(cat.value)}</span>
                            </div>
                            <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                              <div
                                className="h-full rounded-full transition-all"
                                style={{ width: `${percentage}%`, backgroundColor: CHART_COLORS[index] }}
                              />
                            </div>
                          </div>
                          <span className="text-xs text-white/50 w-12 text-right">{percentage.toFixed(0)}%</span>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="py-8 text-center text-white/60">Nenhuma despesa no período</div>
                )}
              </CardContent>
            </Card>

            {/* Top Receitas */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base text-green-400">Top Receitas</CardTitle>
              </CardHeader>
              <CardContent>
                {incomeCategoryData.length > 0 ? (
                  <div className="space-y-3">
                    {incomeCategoryData.slice(0, 5).map((cat, index) => {
                      const total = incomeCategoryData.reduce((sum, c) => sum + c.value, 0);
                      const percentage = (cat.value / total) * 100;
                      return (
                        <div key={cat.name} className="flex items-center gap-3">
                          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: CHART_COLORS[index] }} />
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-sm truncate">{cat.name}</span>
                              <span className="text-sm font-medium text-green-400">{formatCurrency(cat.value)}</span>
                            </div>
                            <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                              <div
                                className="h-full rounded-full transition-all"
                                style={{ width: `${percentage}%`, backgroundColor: CHART_COLORS[index] }}
                              />
                            </div>
                          </div>
                          <span className="text-xs text-white/50 w-12 text-right">{percentage.toFixed(0)}%</span>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="py-8 text-center text-white/60">Nenhuma receita no período</div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Gráficos de Pizza lado a lado */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Distribuição de Despesas</CardTitle>
              </CardHeader>
              <CardContent>
                {categoryData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <PieChart>
                      <Pie
                        data={categoryData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={90}
                        dataKey="value"
                        label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                        labelLine={false}
                      >
                        {categoryData.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                        formatter={(value: number) => formatCurrency(value)}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[280px] flex items-center justify-center text-white/60">Sem dados</div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Distribuição de Receitas</CardTitle>
              </CardHeader>
              <CardContent>
                {incomeCategoryData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <PieChart>
                      <Pie
                        data={incomeCategoryData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={90}
                        dataKey="value"
                        label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                        labelLine={false}
                      >
                        {incomeCategoryData.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                        formatter={(value: number) => formatCurrency(value)}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[280px] flex items-center justify-center text-white/60">Sem dados</div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab: Fluxo de Caixa */}
        <TabsContent value="cashflow" className="space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center">
                Projeção de Fluxo de Caixa
                <ChartHelpTooltip content="Baseado nas contas a pagar e receber cadastradas em /bills." />
              </CardTitle>
              <p className="text-xs text-white/50">Próximos 12 meses - baseado em contas a pagar/receber</p>
            </CardHeader>
            <CardContent>
              {cashFlowProjection.length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart data={cashFlowProjection}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="month" stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 11 }} />
                    <YAxis stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                      formatter={(value: number) => formatCurrency(value)}
                      labelFormatter={(label) => {
                        const item = cashFlowProjection.find(d => d.month === label);
                        return item?.month_name || label;
                      }}
                    />
                    <Legend />
                    <Bar dataKey="receivable" name="A Receber" fill="#10b981" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="payable" name="A Pagar" fill="#ef4444" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="net" name="Resultado" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[350px] flex flex-col items-center justify-center text-white/60">
                  <p>Nenhuma projeção disponível</p>
                  <p className="text-sm mt-2">Cadastre contas em /bills para ver a projeção</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center">
                Previsto vs Realizado
                <ChartHelpTooltip content="Compara o planejado (tracejado) com o realizado (sólido) das contas em /bills para os próximos meses." />
              </CardTitle>
              <p className="text-xs text-white/50">Próximos 12 meses - contas previstas vs já pagas</p>
            </CardHeader>
            <CardContent>
              {cashFlowProjection.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart
                    data={cashFlowProjection.map((proj) => {
                      const actual = actualCashFlow.find(a => a.month === proj.month);
                      return {
                        month: proj.month_name,
                        previsto: proj.net,
                        realizado: actual?.net || 0,
                      };
                    })}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="month" stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 11 }} />
                    <YAxis stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                      formatter={(value: number) => formatCurrency(value)}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="previsto" name="Previsto" stroke="#3b82f6" strokeWidth={2} strokeDasharray="5 5" />
                    <Line type="monotone" dataKey="realizado" name="Realizado" stroke="#10b981" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-white/60">
                  Dados insuficientes para comparação
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Comparativo */}
        <TabsContent value="comparison" className="space-y-4">
          {comparisonData ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">Receitas - Comparativo</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <p className="text-xs text-white/50 mb-1">Período Atual</p>
                        <p className="text-2xl font-bold text-green-500">{formatCurrency(calculatedSummary.income)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-white/50 mb-1">Período Anterior</p>
                        <p className="text-lg text-white/70">{formatCurrency(comparisonData.previousIncome)}</p>
                      </div>
                      <div className={`flex items-center gap-2 ${comparisonData.incomeChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {comparisonData.incomeChange >= 0 ? (
                          <ArrowTrendingUpIcon className="h-5 w-5" />
                        ) : (
                          <ArrowTrendingDownIcon className="h-5 w-5" />
                        )}
                        <span className="text-lg font-medium">
                          {comparisonData.incomeChange >= 0 ? '+' : ''}{comparisonData.incomeChange.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">Despesas - Comparativo</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <p className="text-xs text-white/50 mb-1">Período Atual</p>
                        <p className="text-2xl font-bold text-red-500">{formatCurrency(Math.abs(calculatedSummary.expenses))}</p>
                      </div>
                      <div>
                        <p className="text-xs text-white/50 mb-1">Período Anterior</p>
                        <p className="text-lg text-white/70">{formatCurrency(comparisonData.previousExpenses)}</p>
                      </div>
                      <div className={`flex items-center gap-2 ${comparisonData.expenseChange <= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {comparisonData.expenseChange <= 0 ? (
                          <ArrowTrendingDownIcon className="h-5 w-5" />
                        ) : (
                          <ArrowTrendingUpIcon className="h-5 w-5" />
                        )}
                        <span className="text-lg font-medium">
                          {comparisonData.expenseChange >= 0 ? '+' : ''}{comparisonData.expenseChange.toFixed(1)}%
                        </span>
                        <span className="text-xs text-white/50">
                          ({comparisonData.expenseChange <= 0 ? 'economizou' : 'gastou mais'})
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Evolução Mensal Comparativa</CardTitle>
                </CardHeader>
                <CardContent>
                  {monthlyData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <ComposedChart data={monthlyData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="mes" stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 11 }} />
                        <YAxis stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                          formatter={(value: number) => formatCurrency(value)}
                        />
                        <Legend />
                        <Area type="monotone" dataKey="resultado" fill="rgba(59, 130, 246, 0.2)" stroke="transparent" name="Área Resultado" />
                        <Line type="monotone" dataKey="resultado" stroke="#3b82f6" strokeWidth={3} name="Resultado Mensal" dot={{ fill: '#3b82f6', r: 4 }} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[300px] flex items-center justify-center text-white/60">
                      Sem dados para comparação
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="py-12">
                <div className="text-center text-white/60">
                  <ScaleIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg mb-2">Dados insuficientes para comparação</p>
                  <p className="text-sm">Selecione um período com dados no período anterior para ver o comparativo.</p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
