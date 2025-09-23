'use client';

import { useState } from 'react';
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

  // Mock empty data
  const reports = { results: [] };
  const accounts = { results: [] };
  const categories = { results: [] };

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
              </CardHeader>
              <CardContent>
                <EmptyState
                  icon={BanknotesIcon}
                  title="Nenhum dado disponível"
                  description="Conecte contas bancárias para visualizar o fluxo de caixa"
                />
              </CardContent>
            </Card>

            {/* Category Distribution */}
            <Card className="hover:shadow-lg transition-all duration-300">
              <CardHeader>
                <CardTitle className="flex items-center text-foreground">
                  <ChartPieIcon className="h-5 w-5 mr-2 text-purple-600" />
                  Distribuição por Categoria
                </CardTitle>
              </CardHeader>
              <CardContent>
                <EmptyState
                  icon={ChartPieIcon}
                  title="Nenhum dado disponível"
                  description="Conecte contas bancárias para visualizar categorias"
                />
              </CardContent>
            </Card>

            {/* Income vs Expenses Comparison */}
            <Card className="lg:col-span-2 hover:shadow-lg transition-all duration-300">
              <CardHeader>
                <CardTitle className="flex items-center text-foreground">
                  <ChartBarIcon className="h-5 w-5 mr-2 text-blue-600" />
                  Comparativo: Receitas vs Despesas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <EmptyState
                  icon={ChartBarIcon}
                  title="Nenhum dado disponível"
                  description="Conecte contas bancárias para visualizar receitas e despesas"
                />
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