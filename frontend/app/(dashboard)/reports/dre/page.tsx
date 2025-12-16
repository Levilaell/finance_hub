'use client';

import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { reportsService, DREReport, DREGroup } from '@/services/reports.service';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { formatCurrency } from '@/lib/utils';
import {
  DocumentArrowDownIcon,
  CalendarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  ArrowLeftIcon,
} from '@heroicons/react/24/outline';
import { format, startOfMonth, endOfMonth, subMonths, startOfYear, endOfYear, subYears } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import Link from 'next/link';

interface PeriodFilter {
  label: string;
  startDate: Date;
  endDate: Date;
}

export default function DREPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [isLoading, setIsLoading] = useState(true);
  const [dreData, setDreData] = useState<DREReport | null>(null);
  const [compareWithPrevious, setCompareWithPrevious] = useState(true);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['receitas_operacionais', 'despesas_operacionais']));
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

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
      label: 'Mês atual',
      startDate: startOfMonth(new Date()),
      endDate: endOfMonth(new Date())
    },
    {
      label: 'Mês anterior',
      startDate: startOfMonth(subMonths(new Date(), 1)),
      endDate: endOfMonth(subMonths(new Date(), 1))
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

  const fetchDRE = useCallback(async () => {
    if (!isAuthenticated) return;

    setIsLoading(true);
    try {
      const data = await reportsService.getDRE({
        start_date: format(selectedPeriod.startDate, 'yyyy-MM-dd'),
        end_date: format(selectedPeriod.endDate, 'yyyy-MM-dd'),
        compare_with_previous: compareWithPrevious
      });
      setDreData(data);
    } catch (error) {
      console.error('Erro ao carregar DRE:', error);
      toast.error('Erro ao carregar relatório DRE');
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, selectedPeriod, compareWithPrevious]);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    fetchDRE();
  }, [isAuthenticated, router, fetchDRE]);

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

    // Check max 1 year
    const diffDays = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
    if (diffDays > 366) {
      toast.error('Período máximo: 1 ano');
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

  const toggleGroup = (groupId: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev);
      if (next.has(groupId)) {
        next.delete(groupId);
      } else {
        next.add(groupId);
      }
      return next;
    });
  };

  const toggleCategory = (categoryKey: string) => {
    setExpandedCategories(prev => {
      const next = new Set(prev);
      if (next.has(categoryKey)) {
        next.delete(categoryKey);
      } else {
        next.add(categoryKey);
      }
      return next;
    });
  };

  const handleExportPDF = async () => {
    try {
      toast.loading('Gerando PDF...');
      const blob = await reportsService.exportDREPdf({
        start_date: format(selectedPeriod.startDate, 'yyyy-MM-dd'),
        end_date: format(selectedPeriod.endDate, 'yyyy-MM-dd'),
        compare_with_previous: compareWithPrevious
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `DRE_${format(selectedPeriod.startDate, 'yyyy-MM-dd')}_${format(selectedPeriod.endDate, 'yyyy-MM-dd')}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.dismiss();
      toast.success('PDF exportado com sucesso!');
    } catch (error) {
      toast.dismiss();
      toast.error('Erro ao exportar PDF');
    }
  };

  const handleExportExcel = async () => {
    try {
      toast.loading('Gerando Excel...');
      const blob = await reportsService.exportDREExcel({
        start_date: format(selectedPeriod.startDate, 'yyyy-MM-dd'),
        end_date: format(selectedPeriod.endDate, 'yyyy-MM-dd'),
        compare_with_previous: compareWithPrevious
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `DRE_${format(selectedPeriod.startDate, 'yyyy-MM-dd')}_${format(selectedPeriod.endDate, 'yyyy-MM-dd')}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.dismiss();
      toast.success('Excel exportado com sucesso!');
    } catch (error) {
      toast.dismiss();
      toast.error('Erro ao exportar Excel');
    }
  };

  const formatVariation = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(1)}%`;
  };

  const getVariationClass = (value: number, isExpense: boolean = false) => {
    if (isExpense) {
      // For expenses, negative is good (cost reduction)
      return value <= 0 ? 'text-green-500' : 'text-red-500';
    }
    return value >= 0 ? 'text-green-500' : 'text-red-500';
  };

  if (!isAuthenticated || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  const hasComparison = dreData?.comparison != null;
  const summary = dreData?.current?.summary;
  const compSummary = dreData?.comparison?.summary;
  const variations = dreData?.variations;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-4">
          <Link href="/reports">
            <Button variant="ghost" size="sm" className="text-white/60 hover:text-white">
              <ArrowLeftIcon className="h-4 w-4 mr-2" />
              Voltar
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white">DRE - Demonstrativo de Resultado</h1>
            <p className="text-white/60 text-sm mt-1">
              {format(selectedPeriod.startDate, 'dd MMM', { locale: ptBR })} - {format(selectedPeriod.endDate, 'dd MMM yyyy', { locale: ptBR })}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {/* Comparativo toggle */}
          <div className="flex items-center gap-2 px-3 py-2 bg-white/5 rounded-lg">
            <Switch
              id="compare"
              checked={compareWithPrevious}
              onCheckedChange={setCompareWithPrevious}
            />
            <Label htmlFor="compare" className="text-sm text-white/70">
              Comparar com período anterior
            </Label>
          </div>

          {/* Período */}
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
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={handleExportPDF}>
                Exportar PDF
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleExportExcel}>
                Exportar Excel
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

      {/* Cards de Resumo */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Card className="bg-card/50">
            <CardContent className="p-4">
              <p className="text-xs text-white/60 uppercase tracking-wide">Receitas Operacionais</p>
              <p className="text-lg font-bold text-green-500 mt-1">
                {formatCurrency(summary.receitas_operacionais)}
              </p>
              {hasComparison && variations?.receitas_operacionais && (
                <p className={`text-xs mt-2 ${getVariationClass(variations.receitas_operacionais.percentage)}`}>
                  {formatVariation(variations.receitas_operacionais.percentage)} vs anterior
                </p>
              )}
            </CardContent>
          </Card>

          <Card className="bg-card/50">
            <CardContent className="p-4">
              <p className="text-xs text-white/60 uppercase tracking-wide">Despesas Operacionais</p>
              <p className="text-lg font-bold text-red-500 mt-1">
                {formatCurrency(summary.despesas_operacionais)}
              </p>
              {hasComparison && variations?.despesas_operacionais && (
                <p className={`text-xs mt-2 ${getVariationClass(variations.despesas_operacionais.percentage, true)}`}>
                  {formatVariation(variations.despesas_operacionais.percentage)} vs anterior
                </p>
              )}
            </CardContent>
          </Card>

          <Card className="bg-card/50">
            <CardContent className="p-4">
              <p className="text-xs text-white/60 uppercase tracking-wide">Resultado Operacional</p>
              <p className={`text-lg font-bold mt-1 ${summary.resultado_operacional >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {formatCurrency(summary.resultado_operacional)}
              </p>
              {hasComparison && variations?.resultado_operacional && (
                <p className={`text-xs mt-2 ${getVariationClass(variations.resultado_operacional.percentage)}`}>
                  {formatVariation(variations.resultado_operacional.percentage)} vs anterior
                </p>
              )}
            </CardContent>
          </Card>

          <Card className="bg-card/50 border-2 border-primary/30">
            <CardContent className="p-4">
              <p className="text-xs text-white/60 uppercase tracking-wide">Resultado Líquido</p>
              <p className={`text-xl font-bold mt-1 ${summary.resultado_liquido >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {formatCurrency(summary.resultado_liquido)}
              </p>
              {hasComparison && variations?.resultado_liquido && (
                <p className={`text-xs mt-2 ${getVariationClass(variations.resultado_liquido.percentage)}`}>
                  {formatVariation(variations.resultado_liquido.percentage)} vs anterior
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabela DRE */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Demonstrativo de Resultado do Exercício</CardTitle>
        </CardHeader>
        <CardContent>
          {dreData?.current?.groups && dreData.current.groups.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left py-3 px-4 text-white/70 font-medium">Descrição</th>
                    <th className="text-right py-3 px-4 text-white/70 font-medium">Período Atual</th>
                    {hasComparison && (
                      <>
                        <th className="text-right py-3 px-4 text-white/70 font-medium">Período Anterior</th>
                        <th className="text-right py-3 px-4 text-white/70 font-medium">Variação</th>
                      </>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {dreData.current.groups.map((group) => {
                    const compGroup = dreData.comparison?.groups?.find(g => g.id === group.id);
                    const isExpanded = expandedGroups.has(group.id);
                    const isExpense = group.sign === '-';

                    return (
                      <React.Fragment key={group.id}>
                        {/* Group Header */}
                        <tr
                          className="bg-white/5 hover:bg-white/10 cursor-pointer border-b border-white/5"
                          onClick={() => toggleGroup(group.id)}
                        >
                          <td className="py-3 px-4 font-medium">
                            <div className="flex items-center gap-2">
                              {isExpanded ? (
                                <ChevronDownIcon className="h-4 w-4 text-white/50" />
                              ) : (
                                <ChevronRightIcon className="h-4 w-4 text-white/50" />
                              )}
                              <span className={isExpense ? 'text-red-400' : 'text-green-400'}>
                                ({group.sign})
                              </span>
                              {group.name}
                            </div>
                          </td>
                          <td className={`py-3 px-4 text-right font-semibold ${isExpense ? 'text-red-400' : 'text-green-400'}`}>
                            {formatCurrency(group.total)}
                          </td>
                          {hasComparison && (
                            <>
                              <td className="py-3 px-4 text-right text-white/70">
                                {compGroup ? formatCurrency(compGroup.total) : '-'}
                              </td>
                              <td className="py-3 px-4 text-right">
                                {group.variation !== undefined && (
                                  <span className={getVariationClass(group.variation, isExpense)}>
                                    {formatVariation(group.variation)}
                                  </span>
                                )}
                              </td>
                            </>
                          )}
                        </tr>

                        {/* Categories */}
                        {isExpanded && group.categories.map((category) => {
                          const categoryKey = `${group.id}-${category.name}`;
                          const isCatExpanded = expandedCategories.has(categoryKey);
                          const hasSubcategories = category.subcategories.length > 0;

                          return (
                            <React.Fragment key={categoryKey}>
                              <tr
                                className={`border-b border-white/5 ${hasSubcategories ? 'hover:bg-white/5 cursor-pointer' : ''}`}
                                onClick={() => hasSubcategories && toggleCategory(categoryKey)}
                              >
                                <td className="py-2 px-4 pl-10">
                                  <div className="flex items-center gap-2">
                                    {hasSubcategories && (
                                      isCatExpanded ? (
                                        <ChevronDownIcon className="h-3 w-3 text-white/40" />
                                      ) : (
                                        <ChevronRightIcon className="h-3 w-3 text-white/40" />
                                      )
                                    )}
                                    <span className="text-white/80">{category.name}</span>
                                  </div>
                                </td>
                                <td className="py-2 px-4 text-right text-white/80">
                                  {formatCurrency(category.total)}
                                </td>
                                {hasComparison && (
                                  <>
                                    <td className="py-2 px-4 text-right text-white/50">
                                      {category.previous_total !== undefined
                                        ? formatCurrency(category.previous_total)
                                        : '-'}
                                    </td>
                                    <td className={`py-2 px-4 text-right ${
                                      category.variation !== undefined
                                        ? getVariationClass(category.variation, isExpense)
                                        : ''
                                    }`}>
                                      {category.variation !== undefined
                                        ? formatVariation(category.variation)
                                        : '-'}
                                    </td>
                                  </>
                                )}
                              </tr>

                              {/* Subcategories */}
                              {isCatExpanded && category.subcategories.map((sub) => (
                                <tr
                                  key={`${categoryKey}-${sub.name}`}
                                  className="border-b border-white/5"
                                >
                                  <td className="py-2 px-4 pl-16 text-white/60 text-sm">
                                    └ {sub.name}
                                  </td>
                                  <td className="py-2 px-4 text-right text-white/60 text-sm">
                                    {formatCurrency(sub.total)}
                                  </td>
                                  {hasComparison && (
                                    <>
                                      <td className="py-2 px-4 text-right text-white/40 text-sm">
                                        {sub.previous_total !== undefined
                                          ? formatCurrency(sub.previous_total)
                                          : '-'}
                                      </td>
                                      <td className={`py-2 px-4 text-right text-sm ${
                                        sub.variation !== undefined
                                          ? getVariationClass(sub.variation, isExpense)
                                          : ''
                                      }`}>
                                        {sub.variation !== undefined
                                          ? formatVariation(sub.variation)
                                          : '-'}
                                      </td>
                                    </>
                                  )}
                                </tr>
                              ))}
                            </React.Fragment>
                          );
                        })}
                      </React.Fragment>
                    );
                  })}

                  {/* Separator */}
                  <tr>
                    <td colSpan={hasComparison ? 4 : 2} className="py-2"></td>
                  </tr>

                  {/* Summary Rows */}
                  {summary && (
                    <>
                      <tr className="bg-white/5 border-b border-white/10">
                        <td className="py-3 px-4 font-semibold">(=) Resultado Operacional</td>
                        <td className={`py-3 px-4 text-right font-semibold ${summary.resultado_operacional >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {formatCurrency(summary.resultado_operacional)}
                        </td>
                        {hasComparison && compSummary && (
                          <>
                            <td className="py-3 px-4 text-right text-white/70">
                              {formatCurrency(compSummary.resultado_operacional)}
                            </td>
                            <td className={`py-3 px-4 text-right ${getVariationClass(variations?.resultado_operacional?.percentage || 0)}`}>
                              {variations?.resultado_operacional && formatVariation(variations.resultado_operacional.percentage)}
                            </td>
                          </>
                        )}
                      </tr>

                      <tr className="border-b border-white/5">
                        <td className="py-2 px-4 text-white/70">(+) Receitas Financeiras</td>
                        <td className="py-2 px-4 text-right text-green-400">
                          {formatCurrency(summary.receitas_financeiras)}
                        </td>
                        {hasComparison && compSummary && (
                          <>
                            <td className="py-2 px-4 text-right text-white/50">
                              {formatCurrency(compSummary.receitas_financeiras)}
                            </td>
                            <td className={`py-2 px-4 text-right ${getVariationClass(variations?.receitas_financeiras?.percentage || 0)}`}>
                              {variations?.receitas_financeiras && formatVariation(variations.receitas_financeiras.percentage)}
                            </td>
                          </>
                        )}
                      </tr>

                      <tr className="border-b border-white/5">
                        <td className="py-2 px-4 text-white/70">(-) Despesas Financeiras</td>
                        <td className="py-2 px-4 text-right text-red-400">
                          {formatCurrency(summary.despesas_financeiras)}
                        </td>
                        {hasComparison && compSummary && (
                          <>
                            <td className="py-2 px-4 text-right text-white/50">
                              {formatCurrency(compSummary.despesas_financeiras)}
                            </td>
                            <td className={`py-2 px-4 text-right ${getVariationClass(variations?.despesas_financeiras?.percentage || 0, true)}`}>
                              {variations?.despesas_financeiras && formatVariation(variations.despesas_financeiras.percentage)}
                            </td>
                          </>
                        )}
                      </tr>

                      {/* Final Result */}
                      <tr className="bg-primary/20 border-2 border-primary/30">
                        <td className="py-4 px-4 font-bold text-lg">(=) RESULTADO LÍQUIDO</td>
                        <td className={`py-4 px-4 text-right font-bold text-lg ${summary.resultado_liquido >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {formatCurrency(summary.resultado_liquido)}
                        </td>
                        {hasComparison && compSummary && (
                          <>
                            <td className="py-4 px-4 text-right font-semibold text-white/70">
                              {formatCurrency(compSummary.resultado_liquido)}
                            </td>
                            <td className={`py-4 px-4 text-right font-semibold ${getVariationClass(variations?.resultado_liquido?.percentage || 0)}`}>
                              {variations?.resultado_liquido && formatVariation(variations.resultado_liquido.percentage)}
                            </td>
                          </>
                        )}
                      </tr>
                    </>
                  )}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-12 text-center text-white/60">
              <p className="text-lg mb-2">Nenhum dado disponível</p>
              <p className="text-sm">Não há transações para o período selecionado.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info */}
      <Card className="bg-blue-500/10 border-blue-500/20">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <ArrowTrendingUpIcon className="h-5 w-5 text-blue-400" />
            </div>
            <div>
              <h4 className="font-medium text-blue-400">Sobre o DRE</h4>
              <p className="text-sm text-white/60 mt-1">
                O Demonstrativo de Resultado do Exercício (DRE) mostra o resultado financeiro da sua empresa,
                separando receitas e despesas por categoria. Transferências entre contas e investimentos são
                excluídos automaticamente por não representarem receitas ou despesas operacionais.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
