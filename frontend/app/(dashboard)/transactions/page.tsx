'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { EmptyState } from '@/components/ui/empty-state';
import { DataTable } from '@/components/ui/data-table';
import { bankingService } from '@/services/banking.service';
import { categoriesService } from '@/services/categories.service';
import { BankTransaction, TransactionFilter, Category } from '@/types';
import { formatCurrency, formatDate, cn } from '@/lib/utils';
import { HydrationBoundary } from '@/components/hydration-boundary';
import { useClientOnly } from '@/hooks/use-client-only';
import { 
  BanknotesIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  TagIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
  XMarkIcon,
  CheckIcon,
  DocumentArrowDownIcon,
  TableCellsIcon,
  InformationCircleIcon,
  PencilIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CurrencyDollarIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import {
  SparklesIcon as SparklesSolidIcon
} from '@heroicons/react/24/solid';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { DatePicker } from '@/components/ui/date-picker';
import { useDebounce } from '@/hooks/use-debounce';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface TransactionWithTags extends BankTransaction {
  tags?: string[];
  ai_categorized?: boolean;
  ai_confidence?: number;
  notes?: string;
  category_detail?: {
    id: string;
    name: string;
    color?: string;
    icon?: string;
  } | null;
}

// Função corrigida para formatar data
const formatTransactionDate = (dateString: string | null | undefined): string => {
  if (!dateString) return 'Data não disponível';
  
  try {
    // Tenta diferentes formatos de data
    let date: Date;
    
    // Se já for um objeto Date válido
    if (dateString instanceof Date && !isNaN(dateString.getTime())) {
      date = dateString;
    }
    // Formato ISO com timezone
    else if (dateString.includes('T')) {
      date = new Date(dateString);
    }
    // Formato YYYY-MM-DD
    else if (dateString.match(/^\d{4}-\d{2}-\d{2}$/)) {
      date = new Date(dateString + 'T00:00:00');
    }
    // Tenta parse direto
    else {
      date = new Date(dateString);
    }
    
    // Verifica se a data é válida
    if (isNaN(date.getTime())) {
      console.warn('Invalid date:', dateString);
      return 'Data inválida';
    }
    
    // Formata a data
    return new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    }).format(date);
    
  } catch (error) {
    console.error('Error formatting date:', error, dateString);
    return 'Data inválida';
  }
};

export default function TransactionsPage() {
  const queryClient = useQueryClient();
  const isClient = useClientOnly();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filters, setFilters] = useState<TransactionFilter>({});
  const [selectedTransactions, setSelectedTransactions] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [editingNote, setEditingNote] = useState<string | null>(null);
  const [noteText, setNoteText] = useState('');
  
  const debouncedSearch = useDebounce(searchTerm, 500);

  // Queries
  const { data: transactions, isLoading, error, refetch } = useQuery({
    queryKey: ['bank-transactions', { ...filters, search: debouncedSearch, page, page_size: pageSize }],
    queryFn: () => bankingService.getTransactions({ 
      ...filters, 
      search: debouncedSearch,
      page,
      page_size: pageSize 
    }),
  });

  const { data: accounts } = useQuery({
    queryKey: ['bank-accounts'],
    queryFn: () => bankingService.getBankAccounts(),
  });

  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesService.getCategories(),
  });

  // Safe date parsing for hydration
  const startDate = useMemo(() => {
    if (!filters.start_date) return undefined;
    return new Date(filters.start_date + 'T00:00:00.000Z');
  }, [filters.start_date]);

  const endDate = useMemo(() => {
    if (!filters.end_date) return undefined;
    return new Date(filters.end_date + 'T00:00:00.000Z');
  }, [filters.end_date]);

  // Calculate totals
  const totals = useMemo(() => {
    if (!transactions?.results) return { income: 0, expenses: 0, balance: 0 };
    
    return transactions.results.reduce((acc, transaction) => {
      const amount = Math.abs(transaction.amount);
      if (transaction.transaction_type === 'credit') {
        acc.income += amount;
      } else {
        acc.expenses += amount;
      }
      return acc;
    }, { income: 0, expenses: 0, balance: 0 });
  }, [transactions]);

  totals.balance = totals.income - totals.expenses;

  // Mutations
  const updateCategoryMutation = useMutation({
    mutationFn: ({ id, categoryId }: { id: string; categoryId: string }) =>
      bankingService.updateTransaction(id, { 
        category: categoryId === 'uncategorized' ? undefined : categoryId 
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bank-transactions'] });
      toast.success('Categoria atualizada com sucesso');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Falha ao atualizar categoria');
    },
  });

  const updateNoteMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes: string }) =>
      bankingService.updateTransaction(id, { notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bank-transactions'] });
      setEditingNote(null);
      setNoteText('');
      toast.success('Nota atualizada com sucesso');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Falha ao atualizar nota');
    },
  });

  const bulkUpdateCategoryMutation = useMutation({
    mutationFn: ({ transactionIds, categoryId }: { transactionIds: string[]; categoryId: string }) =>
      bankingService.bulkCategorize({ transaction_ids: transactionIds, category_id: categoryId }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['bank-transactions'] });
      setSelectedTransactions([]);
      toast.success(`${data.updated} transações categorizadas com sucesso`);
    },
    onError: (error: any) => {
      toast.error('Falha ao atualizar categorias');
    },
  });

  const exportTransactionsMutation = useMutation({
    mutationFn: (format: 'csv' | 'excel') => bankingService.exportTransactions(filters),
    onSuccess: (data, format) => {
      if (typeof window !== 'undefined') {
        // Generate consistent timestamp
        const timestamp = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
        const url = window.URL.createObjectURL(new Blob([data]));
        const link = document.createElement('a');
        link.href = url;
        const fileExtension = format === 'excel' ? 'xlsx' : 'csv';
        link.setAttribute('download', `transactions_${timestamp}.${fileExtension}`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      }
      toast.success('Transações exportadas com sucesso');
    },
    onError: (error: any) => {
      toast.error('Falha ao exportar transações');
    },
  });

  const handleSelectAll = useCallback(() => {
    if (selectedTransactions.length === transactions?.results?.length) {
      setSelectedTransactions([]);
    } else {
      setSelectedTransactions(transactions?.results?.map(t => t.id) || []);
    }
  }, [selectedTransactions, transactions]);

  const handleSelectTransaction = useCallback((id: string) => {
    setSelectedTransactions(prev => 
      prev.includes(id) 
        ? prev.filter(t => t !== id)
        : [...prev, id]
    );
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage message="Falha ao carregar transações" />;
  }

  const columns = [
    {
      key: 'select',
      header: () => (
        <input
          type="checkbox"
          checked={selectedTransactions.length === transactions?.results?.length && transactions?.results?.length > 0}
          onChange={handleSelectAll}
          className="rounded border-gray-300"
        />
      ),
      cell: (transaction: TransactionWithTags) => (
        <input
          type="checkbox"
          checked={selectedTransactions.includes(transaction.id)}
          onChange={() => handleSelectTransaction(transaction.id)}
          className="rounded border-gray-300"
        />
      ),
    },
    {
      key: 'date',
      header: 'Data',
      cell: (transaction: TransactionWithTags) => (
        <div className="whitespace-nowrap">
          <p className="font-medium text-sm">{formatTransactionDate(transaction.transaction_date)}</p>
          {transaction.posted_date && transaction.posted_date !== transaction.transaction_date && (
            <p className="text-xs text-gray-500">Lançado: {formatTransactionDate(transaction.posted_date)}</p>
          )}
        </div>
      ),
    },
    {
      key: 'description',
      header: 'Descrição',
      cell: (transaction: TransactionWithTags) => (
        <div className="max-w-xs">
          <p className="font-medium text-sm truncate">{transaction.description}</p>
          {transaction.merchant_name && (
            <p className="text-xs text-gray-600 truncate">{transaction.merchant_name}</p>
          )}
          {transaction.notes && (
            <div className="flex items-center mt-1 text-xs text-gray-500">
              <InformationCircleIcon className="h-3 w-3 mr-1" />
              <span className="truncate">{transaction.notes}</span>
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'category',
      header: 'Categoria',
      cell: (transaction: TransactionWithTags) => (
        <div className="min-w-[180px]">
          <Select
            value={transaction.category || 'uncategorized'}
            onValueChange={(value) =>
              updateCategoryMutation.mutate({ 
                id: transaction.id, 
                categoryId: value
              })
            }
          >
            <SelectTrigger className="w-full h-8 text-sm">
              <div className="flex items-center w-full">
                {transaction.ai_categorized && (
                  <SparklesSolidIcon className="h-3 w-3 mr-1 text-purple-500" title="Categorizada por IA" />
                )}
                {transaction.category_detail ? (
                  <>
                    <span
                      className="w-2 h-2 rounded-full mr-2 flex-shrink-0"
                      style={{ backgroundColor: transaction.category_detail.color || '#gray' }}
                    />
                    <span className="truncate">{transaction.category_detail.name}</span>
                  </>
                ) : (
                  <span className="text-gray-400">Sem categoria</span>
                )}
              </div>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="uncategorized">
                <span className="text-gray-400">Sem categoria</span>
              </SelectItem>
              {categories.map((category) => (
                <SelectItem key={category.id} value={category.id}>
                  <div className="flex items-center">
                    <span
                      className="w-3 h-3 rounded-full mr-2"
                      style={{ backgroundColor: category.color || '#gray' }}
                    />
                    {category.name}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {transaction.ai_categorized && transaction.ai_confidence && (
            <div className="flex items-center mt-1 text-xs text-purple-600">
              <SparklesIcon className="h-3 w-3 mr-1" />
              <span>IA: {Math.round(transaction.ai_confidence * 100)}% confiante</span>
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'amount',
      header: 'Valor',
      cell: (transaction: TransactionWithTags) => (
        <div className={cn(
          "font-semibold text-right whitespace-nowrap",
          transaction.transaction_type === 'credit' ? 'text-green-600' : 'text-red-600'
        )}>
          <div className="flex items-center justify-end">
            {transaction.transaction_type === 'credit' ? (
              <ArrowTrendingUpIcon className="h-4 w-4 mr-1" />
            ) : (
              <ArrowTrendingDownIcon className="h-4 w-4 mr-1" />
            )}
            {formatCurrency(Math.abs(transaction.amount))}
          </div>
        </div>
      ),
    },
    {
      key: 'account',
      header: 'Conta',
      cell: (transaction: TransactionWithTags) => {
        const account = accounts?.results?.find(
          (acc) => acc.id === transaction.bank_account
        );
        return (
          <p className="text-sm text-gray-600 truncate max-w-[120px]">
            {account?.account_name || 'Desconhecida'}
          </p>
        );
      },
    },
    {
      key: 'actions',
      header: '',
      cell: (transaction: TransactionWithTags) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            setEditingNote(transaction.id);
            setNoteText(transaction.notes || '');
          }}
          className="h-8 w-8 p-0"
        >
          <PencilIcon className="h-4 w-4" />
        </Button>
      ),
    },
  ];

  const totalPages = Math.ceil((transactions?.count || 0) / pageSize);

  return (
    <div className="space-y-4 md:space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold">Transações</h1>
          <p className="text-sm md:text-base text-gray-600">Visualize e categorize suas transações</p>
        </div>
        
        {/* Mobile Actions */}
        <div className="flex flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className="md:hidden"
          >
            <FunnelIcon className="h-4 w-4 mr-2" />
            Filtros {Object.keys(filters).length > 0 && `(${Object.keys(filters).length})`}
          </Button>
          
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isLoading}
            >
              <ArrowPathIcon className={cn("h-4 w-4", isLoading && "animate-spin")} />
              <span className="hidden sm:inline ml-2">Atualizar</span>
            </Button>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <ArrowDownTrayIcon className="h-4 w-4" />
                  <span className="hidden sm:inline ml-2">Exportar</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => exportTransactionsMutation.mutate('csv')}>
                  <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
                  Exportar como CSV
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => exportTransactionsMutation.mutate('excel')}>
                  <TableCellsIcon className="h-4 w-4 mr-2" />
                  Exportar como Excel
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      {/* Totals Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 md:gap-4">
        <Card>
          <CardContent className="p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs md:text-sm text-gray-600">Receitas</p>
                <p className="text-lg md:text-2xl font-bold text-green-600">
                  {formatCurrency(totals.income)}
                </p>
              </div>
              <ArrowTrendingUpIcon className="h-6 w-6 md:h-8 md:w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs md:text-sm text-gray-600">Despesas</p>
                <p className="text-lg md:text-2xl font-bold text-red-600">
                  {formatCurrency(totals.expenses)}
                </p>
              </div>
              <ArrowTrendingDownIcon className="h-6 w-6 md:h-8 md:w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs md:text-sm text-gray-600">Saldo</p>
                <p className={cn(
                  "text-lg md:text-2xl font-bold",
                  totals.balance >= 0 ? "text-green-600" : "text-red-600"
                )}>
                  {formatCurrency(totals.balance)}
                </p>
              </div>
              <CurrencyDollarIcon className="h-6 w-6 md:h-8 md:w-8 text-gray-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <div className="space-y-3">
        <div className="flex flex-col md:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Buscar transações..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 w-full"
            />
            {searchTerm && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSearchTerm('')}
                className="absolute right-1 top-1/2 transform -translate-y-1/2"
              >
                <XMarkIcon className="h-4 w-4" />
              </Button>
            )}
          </div>

          {/* Desktop Filters */}
          <div className="hidden md:block">
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline">
                  <FunnelIcon className="h-4 w-4 mr-2" />
                  Filtros {Object.keys(filters).length > 0 && `(${Object.keys(filters).length})`}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80">
                <FiltersContent 
                  filters={filters}
                  setFilters={setFilters}
                  accounts={accounts}
                  categories={categories}
                />
              </PopoverContent>
            </Popover>
          </div>
        </div>

        {/* Mobile Filters */}
        {showFilters && (
          <Card className="md:hidden">
            <CardContent className="p-4">
              <FiltersContent 
                filters={filters}
                setFilters={setFilters}
                accounts={accounts}
                categories={categories}
              />
            </CardContent>
          </Card>
        )}
      </div>

      {/* Bulk Actions */}
      {selectedTransactions.length > 0 && (
        <Card>
          <CardContent className="py-3 px-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <p className="text-sm text-gray-600">
                {selectedTransactions.length} transação(ões) selecionada(s)
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <Select
                  onValueChange={(value) => {
                    if (value) {
                      bulkUpdateCategoryMutation.mutate({ 
                        transactionIds: selectedTransactions,
                        categoryId: value 
                      });
                    }
                  }}
                >
                  <SelectTrigger className="w-[180px] h-8">
                    <SelectValue placeholder="Categorizar em lote" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((category) => (
                      <SelectItem key={category.id} value={category.id}>
                        <div className="flex items-center">
                          <span
                            className="w-3 h-3 rounded-full mr-2"
                            style={{ backgroundColor: category.color || '#gray' }}
                          />
                          {category.name}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedTransactions([])}
                >
                  Limpar Seleção
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Transactions Table */}
      {transactions?.results && transactions.results.length > 0 ? (
        <>
          <Card className="overflow-hidden">
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <DataTable
                  columns={columns}
                  data={transactions.results}
                />
              </div>
            </CardContent>
          </Card>

          {/* Pagination */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Label className="text-sm">Linhas por página:</Label>
              <Select
                value={pageSize.toString()}
                onValueChange={(value) => {
                  setPageSize(parseInt(value));
                  setPage(1);
                }}
              >
                <SelectTrigger className="w-[70px] h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="20">20</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                  <SelectItem value="100">100</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <p className="text-sm text-gray-600">
                Página {page} de {totalPages} ({transactions.count} total)
              </p>
              <div className="flex gap-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                >
                  <ChevronLeftIcon className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page + 1)}
                  disabled={page === totalPages}
                >
                  <ChevronRightIcon className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </>
      ) : (
        <EmptyState
          icon={BanknotesIcon}
          title="Nenhuma transação encontrada"
          description={searchTerm || Object.keys(filters).length > 0 
            ? "Tente ajustar sua busca ou filtros" 
            : "Conecte uma conta bancária para começar a ver suas transações"}
          action={
            searchTerm || Object.keys(filters).length > 0 ? (
              <Button onClick={() => {
                setSearchTerm('');
                setFilters({});
              }}>
                Limpar Filtros
              </Button>
            ) : (
              <HydrationBoundary>
                <Button onClick={() => {
                  // Safe navigation only on client
                  if (typeof window !== 'undefined') {
                    window.location.href = '/accounts';
                  }
                }}>
                  Conectar Conta Bancária
                </Button>
              </HydrationBoundary>
            )
          }
        />
      )}

      {/* Note Edit Dialog */}
      {editingNote && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Editar Nota</CardTitle>
            </CardHeader>
            <CardContent>
              <textarea
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                className="w-full h-24 p-2 border rounded-md"
                placeholder="Adicionar uma nota..."
              />
              <div className="flex justify-end gap-2 mt-4">
                <Button
                  variant="outline"
                  onClick={() => {
                    setEditingNote(null);
                    setNoteText('');
                  }}
                >
                  Cancelar
                </Button>
                <Button
                  onClick={() => {
                    updateNoteMutation.mutate({ id: editingNote, notes: noteText });
                  }}
                >
                  Salvar
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

// Filters Component
function FiltersContent({ filters, setFilters, accounts, categories }: any) {
  const [localFilters, setLocalFilters] = useState(filters);

  // Atualiza filtros locais quando os filtros externos mudam
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const applyFilters = () => {
    setFilters(localFilters);
  };

  return (
    <div className="space-y-4">
      <h4 className="font-medium">Filtrar Transações</h4>
      
      <div>
        <Label>Conta</Label>
        <Select
          value={localFilters.account_id || 'all'}
          onValueChange={(value) =>
            setLocalFilters({ ...localFilters, account_id: value === 'all' ? undefined : value })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Todas as contas" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas as contas</SelectItem>
            {accounts?.results?.map((account: any) => (
              <SelectItem key={account.id} value={account.id}>
                {account.account_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label>Categoria</Label>
        <Select
          value={localFilters.category || 'all'}
          onValueChange={(value) =>
            setLocalFilters({ ...localFilters, category: value === 'all' ? undefined : value })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Todas as categorias" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas as categorias</SelectItem>
            <SelectItem value="uncategorized">Sem categoria</SelectItem>
            {categories.map((category: any) => (
              <SelectItem key={category.id} value={category.id}>
                <div className="flex items-center">
                  <span
                    className="w-3 h-3 rounded-full mr-2"
                    style={{ backgroundColor: category.color || '#gray' }}
                  />
                  {category.name}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label>Tipo de Transação</Label>
        <Select
          value={localFilters.transaction_type || 'all'}
          onValueChange={(value) =>
            setLocalFilters({
              ...localFilters,
              transaction_type: value === 'all' ? undefined : (value as 'debit' | 'credit'),
            })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Todos os tipos" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os tipos</SelectItem>
            <SelectItem value="credit">Receita</SelectItem>
            <SelectItem value="debit">Despesa</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <Label>Data Inicial</Label>
          <HydrationBoundary fallback={<div className="h-10 bg-gray-100 rounded animate-pulse" />}>
            <DatePicker
              date={localFilters.start_date ? new Date(localFilters.start_date) : undefined}
              onDateChange={(date) =>
                setLocalFilters({
                  ...localFilters,
                  start_date: date?.toISOString().split('T')[0],
                })
              }
            />
          </HydrationBoundary>
        </div>
        <div>
          <Label>Data Final</Label>
          <HydrationBoundary fallback={<div className="h-10 bg-gray-100 rounded animate-pulse" />}>
            <DatePicker
              date={localFilters.end_date ? new Date(localFilters.end_date) : undefined}
              onDateChange={(date) =>
                setLocalFilters({
                  ...localFilters,
                  end_date: date?.toISOString().split('T')[0],
                })
              }
            />
          </HydrationBoundary>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <Label>Valor Mínimo</Label>
          <Input
            type="number"
            placeholder="0.00"
            value={localFilters.min_amount || ''}
            onChange={(e) =>
              setLocalFilters({
                ...localFilters,
                min_amount: e.target.value ? parseFloat(e.target.value) : undefined,
              })
            }
          />
        </div>
        <div>
          <Label>Valor Máximo</Label>
          <Input
            type="number"
            placeholder="0.00"
            value={localFilters.max_amount || ''}
            onChange={(e) =>
              setLocalFilters({
                ...localFilters,
                max_amount: e.target.value ? parseFloat(e.target.value) : undefined,
              })
            }
          />
        </div>
      </div>

      <div className="flex gap-2">
        <Button
          variant="outline"
          className="flex-1"
          onClick={() => {
            setLocalFilters({});
            setFilters({});
          }}
        >
          Limpar Filtros
        </Button>
        <Button
          className="flex-1"
          onClick={applyFilters}
        >
          Aplicar Filtros
        </Button>
      </div>
    </div>
  );
}