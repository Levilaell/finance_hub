'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { EmptyState } from '@/components/ui/empty-state';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { bankingService } from '@/services/banking.service';
import { TransactionFilters } from '@/types/banking.types';
import { formatCurrency, formatDate } from '@/lib/utils';
import { 
  BanknotesIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  MagnifyingGlassIcon,
  XMarkIcon,
  PencilIcon,
} from '@heroicons/react/24/outline';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';
import debounce from 'lodash/debounce';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export default function TransactionsPage() {
  const [filters, setFilters] = useState<TransactionFilters>({});
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [page, setPage] = useState(1);
  const [isExporting, setIsExporting] = useState(false);
  const [editingCategoryId, setEditingCategoryId] = useState<string | null>(null);
  const [savingCategoryId, setSavingCategoryId] = useState<string | null>(null);

  // Fetch accounts
  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => bankingService.getAccounts(),
  });

  // Fetch transactions
  const { data: transactions, isLoading, error, refetch: refetchTransactions } = useQuery({
    queryKey: ['transactions', filters, page],
    queryFn: () => bankingService.getTransactions({ ...filters, page }),
  });

  // Fetch categories
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => bankingService.getCategories(),
  });

  // Use totals from backend (includes all filtered transactions, not just current page)
  const totals = useMemo(() => {
    // Use backend totals if available, fallback to zeros
    if (transactions?.totals) {
      return transactions.totals;
    }
    return { income: 0, expenses: 0, balance: 0, filtered_count: 0 };
  }, [transactions]);

  // Debounced search function
  const debouncedSearch = useMemo(
    () => debounce((term: string) => {
      setFilters(prev => ({ ...prev, search: term || undefined }));
      setPage(1);
    }, 500),
    []
  );

  // Handle search input change
  const handleSearchChange = useCallback((value: string) => {
    setSearchTerm(value);
    debouncedSearch(value);
  }, [debouncedSearch]);

  // Handle immediate search (Enter key or button click)
  const handleSearch = () => {
    debouncedSearch.cancel();
    setFilters({ ...filters, search: searchTerm || undefined });
    setPage(1);
  };

  // Export transactions with feedback
  const handleExport = async () => {
    setIsExporting(true);
    try {
      const blob = await bankingService.exportTransactions(filters);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `transactions_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success('Transações exportadas com sucesso!', {
        description: `${transactions?.totals?.filtered_count || transactions?.count || 0} transações exportadas para CSV`
      });
    } catch (error) {
      console.error('Export failed:', error);
      toast.error('Erro ao exportar transações', {
        description: 'Por favor, tente novamente'
      });
    } finally {
      setIsExporting(false);
    }
  };

  // Calculate active filters count
  const activeFiltersCount = useMemo(() => {
    return Object.keys(filters).filter(
      key => filters[key as keyof TransactionFilters] !== undefined
    ).length;
  }, [filters]);

  // Handle click outside or ESC to cancel editing
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setEditingCategoryId(null);
      }
    };

    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      // Check if click is outside of the select dropdown
      if (!target.closest('[role="combobox"]') && !target.closest('[role="listbox"]')) {
        setEditingCategoryId(null);
      }
    };

    if (editingCategoryId) {
      document.addEventListener('keydown', handleEscape);
      document.addEventListener('mousedown', handleClickOutside);
      
      return () => {
        document.removeEventListener('keydown', handleEscape);
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [editingCategoryId]);

  // Clear all filters
  const clearFilters = () => {
    setFilters({});
    setSearchTerm('');
    setPage(1);
    toast.success('Filtros limpos');
  };

  // Update transaction category
  const handleCategoryChange = async (transactionId: string, newCategoryId: string | null) => {
    setSavingCategoryId(transactionId);
    try {
      await bankingService.updateTransaction(transactionId, {
        category: newCategoryId || undefined
      });
      
      // Refetch transactions to get updated data
      await refetchTransactions();
      
      toast.success('Categoria atualizada com sucesso', {
        duration: 2000
      });
    } catch (error) {
      console.error('Failed to update category:', error);
      toast.error('Erro ao atualizar categoria', {
        description: 'Por favor, tente novamente'
      });
    } finally {
      setSavingCategoryId(null);
      setEditingCategoryId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <ErrorMessage message="Erro ao carregar transações" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">
            Transações
          </h1>
          <p className="text-muted-foreground mt-1">
            Gerencie e categorize suas transações
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={handleExport}
            disabled={isExporting || !transactions?.results?.length}
            className="bg-white/10 hover:bg-white/20 border-white/20 transition-all duration-300"
          >
            {isExporting ? (
              <>
                <LoadingSpinner className="h-4 w-4 mr-2" />
                Exportando...
              </>
            ) : (
              <>
                <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                Exportar
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <Card className="shadow-md">
        <CardContent className="pt-6">
          <div className="flex gap-2 mb-4">
            <div className="flex-1">
              <Input
                placeholder="Buscar transações..."
                value={searchTerm}
                onChange={(e) => handleSearchChange(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="pr-10"
              />
              {searchTerm && (
                <button
                  onClick={() => handleSearchChange('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
                >
                  <XMarkIcon className="h-4 w-4 text-gray-400" />
                </button>
              )}
            </div>
            <Button 
              onClick={handleSearch}
              className="bg-white text-black hover:bg-white/90 transition-all duration-300"
            >
              <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
              Buscar
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className="bg-white/10 hover:bg-white/20 border-white/20 transition-all duration-300"
            >
              <FunnelIcon className="h-4 w-4 mr-2" />
              Filtros
              {activeFiltersCount > 0 && (
                <Badge className="ml-2 bg-blue-500 text-white">
                  {activeFiltersCount}
                </Badge>
              )}
            </Button>
            {activeFiltersCount > 0 && (
              <Button
                variant="ghost"
                onClick={clearFilters}
                className="text-red-500 hover:text-red-600 hover:bg-red-50"
              >
                <XMarkIcon className="h-4 w-4 mr-1" />
                Limpar
              </Button>
            )}
          </div>

          {showFilters && (
            <div className="space-y-4 mt-4 pt-4 border-t">
              {activeFiltersCount > 0 && (
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-muted-foreground">
                    {activeFiltersCount} {activeFiltersCount === 1 ? 'filtro ativo' : 'filtros ativos'}
                  </span>
                  <Button
                    variant="link"
                    size="sm"
                    onClick={clearFilters}
                    className="text-red-500 hover:text-red-600"
                  >
                    Limpar todos
                  </Button>
                </div>
              )}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label>Conta</Label>
                <Select
                  value={filters.account_id || 'all'}
                  onValueChange={(value) =>
                    setFilters({
                      ...filters,
                      account_id: value === 'all' ? undefined : value,
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Todas as contas" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas as contas</SelectItem>
                    {accounts?.map((account) => (
                      <SelectItem key={account.id} value={account.id}>
                        {account.display_name || account.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Categoria</Label>
                <Select
                  value={filters.category_id || 'all'}
                  onValueChange={(value) =>
                    setFilters({
                      ...filters,
                      category_id: value === 'all' ? undefined : value,
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Todas as categorias" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas as categorias</SelectItem>
                    {categories?.map((category) => (
                      <SelectItem key={category.id} value={category.id}>
                        {category.icon} {category.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Tipo</Label>
                <Select
                  value={filters.type || 'all'}
                  onValueChange={(value) =>
                    setFilters({
                      ...filters,
                      type: value === 'all' ? undefined : (value as 'DEBIT' | 'CREDIT'),
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Todos os tipos" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos os tipos</SelectItem>
                    <SelectItem value="CREDIT">Receita</SelectItem>
                    <SelectItem value="DEBIT">Despesa</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Transactions List */}
      <Card className="shadow-md">
        <CardContent className="p-0">
          {transactions?.results && transactions.results.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-white/10 border-b border-white/20">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Data
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Descrição
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Categoria
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Conta
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Valor
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {transactions.results.map((transaction, index) => (
                    <tr key={transaction.id} className="hover:bg-white/5 transition-all duration-200">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                        {formatDate(transaction.date)}
                      </td>
                      <td className="px-6 py-4 text-sm text-foreground">
                        {transaction.description}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                        {editingCategoryId === transaction.id ? (
                          <Select
                            value={transaction.category || 'none'}
                            onValueChange={(value) => {
                              handleCategoryChange(transaction.id, value === 'none' ? null : value);
                            }}
                            disabled={savingCategoryId === transaction.id}
                            defaultOpen={true}
                          >
                            <SelectTrigger className="w-[180px] h-8 bg-white dark:bg-gray-800 border-blue-500">
                              <SelectValue placeholder="Selecione categoria" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">
                                <span className="text-muted-foreground italic">Sem categoria</span>
                              </SelectItem>
                              {(() => {
                                const filtered = categories?.filter(cat => {
                                  // Allow 'both' type for any transaction
                                  if (cat.type === 'both') return true;
                                  // Match income categories with CREDIT transactions
                                  if (transaction.type === 'CREDIT' && cat.type === 'income') return true;
                                  // Match expense categories with DEBIT transactions
                                  if (transaction.type === 'DEBIT' && cat.type === 'expense') return true;
                                  return false;
                                });
                                
                                if (!filtered || filtered.length === 0) {
                                  return (
                                    <SelectItem value="none" disabled>
                                      <span className="text-muted-foreground italic">
                                        {transaction.type === 'CREDIT' 
                                          ? 'Nenhuma categoria de receita disponível'
                                          : 'Nenhuma categoria de despesa disponível'}
                                      </span>
                                    </SelectItem>
                                  );
                                }
                                
                                return filtered.map((category) => (
                                  <SelectItem key={category.id} value={category.id}>
                                    <span className="inline-flex items-center gap-1">
                                      <span className="text-lg">{category.icon}</span>
                                      <span>{category.name}</span>
                                    </span>
                                  </SelectItem>
                                ));
                              })()}
                            </SelectContent>
                          </Select>
                        ) : (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  onClick={() => setEditingCategoryId(transaction.id)}
                                  className="inline-flex items-center gap-1 px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer group"
                                  disabled={savingCategoryId === transaction.id}
                                >
                                  {savingCategoryId === transaction.id ? (
                                    <LoadingSpinner className="h-4 w-4" />
                                  ) : transaction.category_detail ? (
                                    <>
                                      <span className="text-lg">{transaction.category_detail.icon}</span>
                                      <span>{transaction.category_detail.name}</span>
                                      <PencilIcon className="h-3 w-3 ml-1 opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </>
                                  ) : (
                                    <>
                                      <span className="text-muted-foreground/60 italic">Sem categoria</span>
                                      <PencilIcon className="h-3 w-3 ml-1 opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </>
                                  )}
                                </button>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>Clique para editar categoria</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                        {transaction.account_info?.name || '-'}
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm text-right font-medium ${
                        transaction.type === 'CREDIT' ? 'text-success-subtle' : 'text-error-subtle'
                      }`}>
                        {transaction.type === 'CREDIT' ? '+' : '-'}
                        {formatCurrency(Math.abs(transaction.amount))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState
              icon={BanknotesIcon}
              title="Nenhuma transação encontrada"
              description="Conecte uma conta bancária para ver suas transações"
            />
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {transactions && transactions.count > 0 && (
        <div className="flex justify-between items-center">
          <p className="text-sm text-muted-foreground">
            Mostrando {transactions.results.length} de {transactions.count} transações
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => setPage(page - 1)}
              disabled={!transactions.previous}
              className="hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 hover:border-blue-300 transition-all duration-200"
            >
              Anterior
            </Button>
            <Button
              variant="outline"
              onClick={() => setPage(page + 1)}
              disabled={!transactions.next}
              className="hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 hover:border-blue-300 transition-all duration-200"
            >
              Próxima
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}