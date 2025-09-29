'use client';

import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { formatDate, cn } from '@/lib/utils';
import {
  DocumentChartBarIcon,
  ArrowDownTrayIcon,
  PlayIcon,
  CalendarIcon,
  ChartBarIcon,
  ChartPieIcon,
  BanknotesIcon,
  ArrowTrendingUpIcon as TrendingUpIcon,
} from '@heroicons/react/24/outline';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { bankingService } from '@/services/banking.service';
import { Transaction } from '@/types/banking';

const REPORT_TYPES = [
  { value: 'profit_loss', label: 'DRE - Demonstração de Resultados', icon: DocumentChartBarIcon },
  { value: 'cash_flow', label: 'Fluxo de Caixa', icon: BanknotesIcon },
  { value: 'monthly_summary', label: 'Resumo Mensal', icon: ChartBarIcon },
  { value: 'category_analysis', label: 'Análise por Categoria', icon: ChartPieIcon },
];

const QUICK_PERIODS = [
  { id: 'current_month', label: 'Mês Atual', icon: CalendarIcon },
  { id: 'last_month', label: 'Mês Anterior', icon: CalendarIcon },
  { id: 'quarterly', label: 'Trimestre', icon: ChartBarIcon },
  { id: 'year_to_date', label: 'Ano Atual', icon: TrendingUpIcon },
];

interface CashFlowData {
  date: string;
  receitas: number;
  despesas: number;
  saldo: number;
}

interface CategoryData {
  name: string;
  value: number;
}

interface ComparisonData {
  periodo: string;
  receitas: number;
  despesas: number;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658', '#FF6B6B', '#4ECDC4', '#45B7D1'];

function ReportsPageContent() {
  // State
  const [reportType, setReportType] = useState<string>('profit_loss');
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [exportFormat, setExportFormat] = useState<'pdf' | 'xlsx'>('pdf');
  const [selectedPeriod, setSelectedPeriod] = useState(() => {
    const today = new Date();
    const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    return {
      start_date: startOfMonth.toISOString().split('T')[0],
      end_date: today.toISOString().split('T')[0]
    };
  });

  // Charts data state
  const [cashFlowData, setCashFlowData] = useState<CashFlowData[]>([]);
  const [categoryData, setCategoryData] = useState<CategoryData[]>([]);
  const [comparisonData, setComparisonData] = useState<ComparisonData[]>([]);
  const [loading, setLoading] = useState(true);

  // Mock empty data
  const reports = { results: [] };
  const accounts = { results: [] };
  const categories = { results: [] };

  // Fetch chart data
  useEffect(() => {
    loadChartData();
  }, [selectedPeriod]);

  const loadChartData = async () => {
    try {
      setLoading(true);

      console.log('Loading chart data for period:', selectedPeriod);

      // Fetch transactions for the selected period
      const transactions = await bankingService.getTransactions({
        date_from: selectedPeriod.start_date,
        date_to: selectedPeriod.end_date,
      });

      console.log('Transactions fetched:', transactions.length);

      // Process cash flow data (daily aggregation)
      const cashFlow = processCashFlowData(transactions);
      console.log('Cash flow data:', cashFlow);
      setCashFlowData(cashFlow);

      // Process category distribution
      const categories = processCategoryData(transactions);
      console.log('Category data:', categories);
      setCategoryData(categories);

      // Process comparison data (current vs previous period)
      const comparison = await processComparisonData();
      console.log('Comparison data:', comparison);
      setComparisonData(comparison);

    } catch (error) {
      console.error('Error loading chart data:', error);
      toast.error('Erro ao carregar dados dos gráficos');
    } finally {
      setLoading(false);
    }
  };

  const processCashFlowData = (transactions: Transaction[]): CashFlowData[] => {
    const dailyData: Record<string, { receitas: number; despesas: number }> = {};

    transactions.forEach(transaction => {
      const date = transaction.date;
      if (!dailyData[date]) {
        dailyData[date] = { receitas: 0, despesas: 0 };
      }

      if (transaction.type === 'CREDIT') {
        dailyData[date].receitas += transaction.amount;
      } else {
        dailyData[date].despesas += Math.abs(transaction.amount);
      }
    });

    // Convert to array and calculate running balance
    let runningBalance = 0;
    return Object.entries(dailyData)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, data]) => {
        runningBalance += data.receitas - data.despesas;
        return {
          date: new Date(date).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }),
          receitas: data.receitas,
          despesas: data.despesas,
          saldo: runningBalance,
        };
      });
  };

  const processCategoryData = (transactions: Transaction[]): CategoryData[] => {
    const categoryTotals: Record<string, number> = {};

    transactions.forEach(transaction => {
      if (transaction.type === 'DEBIT') {
        const category = transaction.category || 'Sem categoria';
        categoryTotals[category] = (categoryTotals[category] || 0) + Math.abs(transaction.amount);
      }
    });

    return Object.entries(categoryTotals)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10); // Top 10 categories
  };

  const processComparisonData = async (): Promise<ComparisonData[]> => {
    // Usar o período selecionado
    const startDate = new Date(selectedPeriod.start_date);
    const endDate = new Date(selectedPeriod.end_date);
    const periodDays = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));

    // Calcular período anterior (mesmo tamanho que o período atual)
    const prevEndDate = new Date(startDate);
    prevEndDate.setDate(prevEndDate.getDate() - 1);
    const prevStartDate = new Date(prevEndDate);
    prevStartDate.setDate(prevStartDate.getDate() - periodDays);

    const currentPeriod = await bankingService.getTransactionsSummary(
      selectedPeriod.start_date,
      selectedPeriod.end_date
    );

    const previousPeriod = await bankingService.getTransactionsSummary(
      prevStartDate.toISOString().split('T')[0],
      prevEndDate.toISOString().split('T')[0]
    );

    // Gerar labels baseados no tamanho do período
    let currentLabel = '';
    let previousLabel = '';

    if (periodDays <= 31) {
      // Período mensal ou menor - mostrar mês/ano
      currentLabel = startDate.toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' }).replace('.', '');
      previousLabel = prevStartDate.toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' }).replace('.', '');
    } else if (periodDays <= 92) {
      // Período trimestral
      currentLabel = `${startDate.toLocaleDateString('pt-BR', { month: 'short' })} - ${endDate.toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' })}`.replace(/\./g, '');
      previousLabel = `${prevStartDate.toLocaleDateString('pt-BR', { month: 'short' })} - ${prevEndDate.toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' })}`.replace(/\./g, '');
    } else {
      // Período anual ou maior
      currentLabel = `Ano ${startDate.getFullYear()}`;
      previousLabel = `Ano ${prevStartDate.getFullYear()}`;
    }

    return [
      {
        periodo: previousLabel,
        receitas: previousPeriod.income || 0,
        despesas: Math.abs(previousPeriod.expenses) || 0,
      },
      {
        periodo: currentLabel,
        receitas: currentPeriod.income || 0,
        despesas: Math.abs(currentPeriod.expenses) || 0,
      },
    ];
  };

  const handleQuickPeriod = (periodId: string) => {
    const today = new Date();
    let startDate = new Date();
    let endDate = new Date();
    
    switch (periodId) {
      case 'current_month':
        startDate = new Date(today.getFullYear(), today.getMonth(), 1);
        endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        break;
      case 'last_month':
        startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        endDate = new Date(today.getFullYear(), today.getMonth(), 0);
        break;
      case 'quarterly':
        startDate = new Date(today.getFullYear(), today.getMonth() - 2, 1);
        endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        break;
      case 'year_to_date':
        startDate = new Date(today.getFullYear(), 0, 1);
        endDate = today;
        break;
      default:
        startDate = new Date(today.getFullYear(), today.getMonth() - 2, 1);
        endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        break;
    }
    
    setSelectedPeriod({
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0]
    });

    toast.success(`Período selecionado: ${QUICK_PERIODS.find(p => p.id === periodId)?.label}`);
  };

  const handleGenerateReport = () => {
    if (!selectedPeriod || !selectedPeriod.start_date || !selectedPeriod.end_date) {
      toast.error('Por favor, selecione um período');
      return;
    }
    
    toast.info('Banking logic removed - report not generated');
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-foreground">
            Relatórios
          </h1>
          <p className="text-muted-foreground">Análises completas e insights sobre suas finanças</p>
        </div>
      </div>

      {/* Quick Reports */}
      <Card className="shadow-md">
        <CardHeader>
          <CardTitle className="text-foreground">
            Relatórios Rápidos
          </CardTitle>
          <CardDescription>Gere relatórios instantâneos para períodos comuns</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            {QUICK_PERIODS.map((period) => {
              const Icon = period.icon;
              return (
                <Button
                  key={period.id}
                  variant="outline"
                  className="justify-start h-auto p-4 hover:bg-muted hover:border-border transition-all duration-300 hover:shadow-md hover:scale-105"
                  onClick={() => handleQuickPeriod(period.id)}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  <div className="text-left">
                    <div className="font-medium">{period.label}</div>
                    <div className="text-xs text-muted-foreground">Clique para visualizar</div>
                  </div>
                </Button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs defaultValue="visualizations" className="space-y-4">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="visualizations">Visualizações</TabsTrigger>
          <TabsTrigger value="custom">Relatórios Personalizados</TabsTrigger>
        </TabsList>

        {/* Visualizations Tab */}
        <TabsContent value="visualizations" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Cash Flow Chart */}
            <Card className="hover:shadow-lg transition-all duration-300">
              <CardHeader>
                <CardTitle className="flex items-center text-foreground">
                  <BanknotesIcon className="h-5 w-5 mr-2 text-blue-600" />
                  Fluxo de Caixa
                </CardTitle>
                <CardDescription>
                  Acompanhamento diário de receitas, despesas e saldo acumulado
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center justify-center h-80">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                ) : cashFlowData.length === 0 ? (
                  <EmptyState
                    icon={BanknotesIcon}
                    title="Nenhum dado disponível"
                    description="Conecte contas bancárias para visualizar o fluxo de caixa"
                  />
                ) : (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={cashFlowData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip
                        formatter={(value: number) =>
                          new Intl.NumberFormat('pt-BR', {
                            style: 'currency',
                            currency: 'BRL',
                          }).format(value)
                        }
                      />
                      <Legend />
                      <Line type="monotone" dataKey="receitas" stroke="#10b981" name="Receitas" strokeWidth={2} />
                      <Line type="monotone" dataKey="despesas" stroke="#ef4444" name="Despesas" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>

            {/* Category Distribution */}
            <Card className="hover:shadow-lg transition-all duration-300">
              <CardHeader>
                <CardTitle className="flex items-center text-foreground">
                  <ChartPieIcon className="h-5 w-5 mr-2 text-purple-600" />
                  Distribuição por Categoria
                </CardTitle>
                <CardDescription>
                  Top 10 categorias de despesas no período
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center justify-center h-80">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                ) : categoryData.length === 0 ? (
                  <EmptyState
                    icon={ChartPieIcon}
                    title="Nenhum dado disponível"
                    description="Conecte contas bancárias para visualizar categorias"
                  />
                ) : (
                  <div className="space-y-4">
                    <ResponsiveContainer width="100%" height={240}>
                      <PieChart>
                        <Pie
                          data={categoryData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {categoryData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip
                          formatter={(value: number) =>
                            new Intl.NumberFormat('pt-BR', {
                              style: 'currency',
                              currency: 'BRL',
                            }).format(value)
                          }
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="space-y-2">
                      {categoryData.map((category, index) => (
                        <div key={category.name} className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <div
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: COLORS[index % COLORS.length] }}
                            />
                            <span className="text-muted-foreground">{category.name}</span>
                          </div>
                          <span className="font-medium">
                            {new Intl.NumberFormat('pt-BR', {
                              style: 'currency',
                              currency: 'BRL',
                            }).format(category.value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Income vs Expenses Comparison */}
            <Card className="lg:col-span-2 hover:shadow-lg transition-all duration-300">
              <CardHeader>
                <CardTitle className="flex items-center text-foreground">
                  <ChartBarIcon className="h-5 w-5 mr-2 text-blue-600" />
                  Comparativo: Receitas vs Despesas
                </CardTitle>
                <CardDescription>
                  Comparação entre período anterior e período selecionado
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center justify-center h-80">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                ) : comparisonData.length === 0 ? (
                  <EmptyState
                    icon={ChartBarIcon}
                    title="Nenhum dado disponível"
                    description="Conecte contas bancárias para visualizar receitas e despesas"
                  />
                ) : (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={comparisonData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="periodo" />
                      <YAxis />
                      <Tooltip
                        formatter={(value: number) =>
                          new Intl.NumberFormat('pt-BR', {
                            style: 'currency',
                            currency: 'BRL',
                          }).format(value)
                        }
                      />
                      <Legend />
                      <Bar dataKey="receitas" fill="#10b981" name="Receitas" />
                      <Bar dataKey="despesas" fill="#ef4444" name="Despesas" />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Custom Reports Tab */}
        <TabsContent value="custom" className="space-y-6">
          <Card className="shadow-md">
            <CardHeader>
              <CardTitle className="text-foreground">
                Gerador de Relatórios Personalizados
              </CardTitle>
              <CardDescription>Configure e gere relatórios detalhados com filtros avançados</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Report Type Selection */}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                  {REPORT_TYPES.map((type) => {
                    const Icon = type.icon;
                    return (
                      <div
                        key={type.value}
                        className={cn(
                          "border rounded-lg p-4 cursor-pointer transition-colors",
                          reportType === type.value
                            ? "border-primary bg-primary/5"
                            : "border-gray-200 hover:border-gray-300"
                        )}
                        onClick={() => setReportType(type.value)}
                      >
                        <Icon className="h-8 w-8 mb-2 text-blue-600" />
                        <h4 className="font-medium">{type.label}</h4>
                      </div>
                    );
                  })}
                </div>

                {/* Filters */}
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <Label>Período Inicial</Label>
                    <input
                      type="date"
                      value={selectedPeriod?.start_date || ''}
                      onChange={(e) =>
                        setSelectedPeriod({ 
                          start_date: e.target.value,
                          end_date: selectedPeriod?.end_date || new Date().toISOString().split('T')[0]
                        })
                      }
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                  </div>
                  <div>
                    <Label>Período Final</Label>
                    <input
                      type="date"
                      value={selectedPeriod?.end_date || ''}
                      onChange={(e) =>
                        setSelectedPeriod({ 
                          start_date: selectedPeriod?.start_date || new Date().toISOString().split('T')[0],
                          end_date: e.target.value
                        })
                      }
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                  </div>
                  <div>
                    <Label>Formato de Exportação</Label>
                    <Select value={exportFormat} onValueChange={(value: 'pdf' | 'xlsx') => setExportFormat(value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pdf">PDF</SelectItem>
                        <SelectItem value="xlsx">Excel</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Account and Category Filters */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <Label>Contas (opcional)</Label>
                    <Select 
                      value={selectedAccounts[0] || "all"}
                      onValueChange={(value) => setSelectedAccounts(value === "all" ? [] : [value])}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Todas as contas" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todas as contas</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Categorias (opcional)</Label>
                    <Select
                      value={selectedCategories[0] || "all"}
                      onValueChange={(value) => setSelectedCategories(value === "all" ? [] : [value])}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Todas as categorias" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todas as categorias</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-4">
                  <Button
                    onClick={handleGenerateReport}
                    className="flex-1 bg-primary hover:bg-primary/90 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
                  >
                    <PlayIcon className="h-4 w-4 mr-2" />
                    Gerar Relatório
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recent Reports */}
          <Card className="shadow-md">
            <CardHeader>
              <CardTitle className="text-foreground">
                Relatórios Recentes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <EmptyState
                icon={DocumentChartBarIcon}
                title="Nenhum relatório gerado"
                description="Gere seu primeiro relatório para obter insights sobre suas finanças"
              />
            </CardContent>
          </Card>
        </TabsContent>
        
      </Tabs>
    </div>
  );
}

export default function ReportsPage() {
  return <ReportsPageContent />;
}