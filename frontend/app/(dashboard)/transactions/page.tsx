'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { bankingService } from '@/services/banking.service';
import { Transaction, BankAccount, Category } from '@/types/banking';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { formatCurrency } from '@/lib/utils';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowPathIcon,
  ArrowDownTrayIcon,
  XMarkIcon,
  ChevronDownIcon,
  CheckIcon,
  LinkIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';
import { Input } from '@/components/ui/input';
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { toast } from 'sonner';
import * as XLSX from 'xlsx';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { LinkBillDialog } from '@/components/banking';

export default function TransactionsPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [filteredTransactions, setFilteredTransactions] = useState<Transaction[]>([]);
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [updatingTransactionId, setUpdatingTransactionId] = useState<string | null>(null);
  const [showLinkBillDialog, setShowLinkBillDialog] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAccount, setSelectedAccount] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 50; // 50 transações por página

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    fetchData();
  }, [isAuthenticated, router]);

  useEffect(() => {
    applyFilters();
    setCurrentPage(1); // Reset to first page when filters change
  }, [transactions, searchTerm, selectedAccount, selectedType, selectedCategory, startDate, endDate]);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [transactionsData, accountsData, categoriesData] = await Promise.all([
        bankingService.getTransactions(), // Carrega todas as transações em batches
        bankingService.getAccounts(),
        bankingService.getCategories(),
      ]);
      setTransactions(transactionsData);
      setAccounts(accountsData);
      setCategories(categoriesData);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchData();
    setIsRefreshing(false);
  };

  const applyFilters = () => {
    let filtered = [...transactions];

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (t) =>
          t.description.toLowerCase().includes(term) ||
          t.category?.toLowerCase().includes(term) ||
          t.merchant_name?.toLowerCase().includes(term)
      );
    }

    // Account filter
    if (selectedAccount !== 'all') {
      filtered = filtered.filter((t) => t.account_name === selectedAccount);
    }

    // Type filter
    if (selectedType !== 'all') {
      filtered = filtered.filter((t) => t.type === selectedType);
    }

    // Category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter((t) => t.category === selectedCategory);
    }

    // Date filters - convert to local date for comparison to match user's timezone
    if (startDate) {
      filtered = filtered.filter((t) => {
        // Convert ISO datetime to local date (YYYY-MM-DD)
        const transactionDate = new Date(t.date);
        const year = transactionDate.getFullYear();
        const month = String(transactionDate.getMonth() + 1).padStart(2, '0');
        const day = String(transactionDate.getDate()).padStart(2, '0');
        const localDateStr = `${year}-${month}-${day}`;
        return localDateStr >= startDate;
      });
    }
    if (endDate) {
      filtered = filtered.filter((t) => {
        // Convert ISO datetime to local date (YYYY-MM-DD)
        const transactionDate = new Date(t.date);
        const year = transactionDate.getFullYear();
        const month = String(transactionDate.getMonth() + 1).padStart(2, '0');
        const day = String(transactionDate.getDate()).padStart(2, '0');
        const localDateStr = `${year}-${month}-${day}`;
        return localDateStr <= endDate;
      });
    }

    // Sort by date (most recent first)
    filtered.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

    setFilteredTransactions(filtered);
  };

  const handleUpdateCategory = async (transactionId: string, categoryId: string | null) => {
    setUpdatingTransactionId(transactionId);
    try {
      await bankingService.updateTransactionCategory(transactionId, categoryId);

      // Update local state
      setTransactions(prev =>
        prev.map(t =>
          t.id === transactionId
            ? {
                ...t,
                user_category_id: categoryId,
                category: categoryId
                  ? categories.find(c => c.id === categoryId)?.name
                  : t.pluggy_category
              }
            : t
        )
      );

      toast.success('Categoria atualizada com sucesso!');
    } catch (error) {
      console.error('Error updating category:', error);
      toast.error('Erro ao atualizar categoria');
    } finally {
      setUpdatingTransactionId(null);
    }
  };

  const clearFilters = () => {
    setSearchTerm('');
    setSelectedAccount('all');
    setSelectedType('all');
    setSelectedCategory('all');
    setStartDate('');
    setEndDate('');
  };

  const openLinkBillDialog = (transaction: Transaction) => {
    setSelectedTransaction(transaction);
    setShowLinkBillDialog(true);
  };

  const exportToCSV = () => {
    if (filteredTransactions.length === 0) {
      toast.error('Nenhuma transação para exportar');
      return;
    }

    const headers = ['Data', 'Hora', 'Descrição', 'Categoria', 'Conta', 'Tipo', 'Valor'];
    const rows = filteredTransactions.map((t) => [
      format(new Date(t.date), 'dd/MM/yyyy', { locale: ptBR }),
      format(new Date(t.date), 'HH:mm', { locale: ptBR }),
      `"${t.description.replace(/"/g, '""')}"`,
      `"${(t.category || 'Sem categoria').replace(/"/g, '""')}"`,
      `"${t.account_name.replace(/"/g, '""')}"`,
      t.type === 'CREDIT' ? 'Receita' : 'Despesa',
      Number(Math.abs(t.amount)).toFixed(2).replace('.', ',')
    ]);

    // Add BOM for Excel UTF-8 compatibility
    const BOM = '\uFEFF';
    const csv = BOM + [headers, ...rows].map((row) => row.join(';')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);

    const dateRange = startDate && endDate
      ? `_${format(new Date(startDate), 'yyyy-MM-dd')}_a_${format(new Date(endDate), 'yyyy-MM-dd')}`
      : startDate
      ? `_desde_${format(new Date(startDate), 'yyyy-MM-dd')}`
      : endDate
      ? `_ate_${format(new Date(endDate), 'yyyy-MM-dd')}`
      : '';

    link.download = `transacoes${dateRange}_${format(new Date(), 'yyyy-MM-dd_HH-mm')}.csv`;
    link.click();
    toast.success(`${filteredTransactions.length} transações exportadas para CSV`);
  };

  const exportToExcel = () => {
    if (filteredTransactions.length === 0) {
      toast.error('Nenhuma transação para exportar');
      return;
    }

    const data = filteredTransactions.map((t) => ({
      Data: format(new Date(t.date), 'dd/MM/yyyy', { locale: ptBR }),
      Hora: format(new Date(t.date), 'HH:mm', { locale: ptBR }),
      Descrição: t.description,
      Categoria: t.category || 'Sem categoria',
      Conta: t.account_name,
      Tipo: t.type === 'CREDIT' ? 'Receita' : 'Despesa',
      Valor: Math.abs(t.amount)
    }));

    const worksheet = XLSX.utils.json_to_sheet(data);

    // Set column widths
    worksheet['!cols'] = [
      { wch: 12 }, // Data
      { wch: 8 },  // Hora
      { wch: 40 }, // Descrição
      { wch: 20 }, // Categoria
      { wch: 25 }, // Conta
      { wch: 10 }, // Tipo
      { wch: 15 }  // Valor
    ];

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Transações');

    const dateRange = startDate && endDate
      ? `_${format(new Date(startDate), 'yyyy-MM-dd')}_a_${format(new Date(endDate), 'yyyy-MM-dd')}`
      : startDate
      ? `_desde_${format(new Date(startDate), 'yyyy-MM-dd')}`
      : endDate
      ? `_ate_${format(new Date(endDate), 'yyyy-MM-dd')}`
      : '';

    XLSX.writeFile(workbook, `transacoes${dateRange}_${format(new Date(), 'yyyy-MM-dd_HH-mm')}.xlsx`);
    toast.success(`${filteredTransactions.length} transações exportadas para Excel`);
  };

  // Get unique categories for filter
  const uniqueCategoryNames = Array.from(
    new Set(transactions.map((t) => t.category).filter(Boolean))
  ).sort();

  // Get unique account names for filter
  const accountNames = Array.from(
    new Set(transactions.map((t) => t.account_name))
  ).sort();

  // Calculate totals
  const totalIncome = filteredTransactions
    .filter((t) => t.type === 'CREDIT')
    .reduce((sum, t) => sum + Math.abs(t.amount), 0);

  const totalExpenses = filteredTransactions
    .filter((t) => t.type === 'DEBIT')
    .reduce((sum, t) => sum + Math.abs(t.amount), 0);

  const balance = totalIncome - totalExpenses;

  // Paginação local (client-side) - performance otimizada
  const totalPages = Math.ceil(filteredTransactions.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedTransactions = filteredTransactions.slice(startIndex, endIndex);

  const goToPage = (page: number) => {
    const newPage = Math.max(1, Math.min(page, totalPages));
    setCurrentPage(newPage);
    // Scroll to top when changing pages
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (!isAuthenticated || !user || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Transações</h1>
          <p className="text-white/70 mt-1">
            Todas as suas transações em um só lugar
          </p>
        </div>
        <div className="flex gap-2 w-full sm:w-auto">
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            className="text-white border-white/20 hover:bg-white/10 flex-1 sm:flex-none"
          >
            <FunnelIcon className="h-4 w-4 sm:mr-2" />
            <span className="hidden sm:inline">Filtros</span>
          </Button>
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="text-white border-white/20 hover:bg-white/10"
          >
            {isRefreshing ? (
              <ArrowPathIcon className="h-4 w-4 animate-spin" />
            ) : (
              <ArrowPathIcon className="h-4 w-4" />
            )}
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="text-white border-white/20 hover:bg-white/10 flex-1 sm:flex-none">
                <ArrowDownTrayIcon className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline">Exportar</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={exportToCSV}>
                Exportar CSV
              </DropdownMenuItem>
              <DropdownMenuItem onClick={exportToExcel}>
                Exportar Excel
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Filtros</CardTitle>
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <XMarkIcon className="h-4 w-4 mr-2" />
              Limpar
            </Button>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Pesquisar</label>
                <div className="relative">
                  <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Descricao, categoria..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Conta</label>
                <Select value={selectedAccount} onValueChange={setSelectedAccount}>
                  <SelectTrigger>
                    <SelectValue placeholder="Todas as contas" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas as contas</SelectItem>
                    {accountNames.map((name) => (
                      <SelectItem key={name} value={name}>
                        {name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Tipo</label>
                <Select value={selectedType} onValueChange={setSelectedType}>
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

              <div>
                <label className="text-sm font-medium mb-2 block">Categoria</label>
                <Select
                  value={selectedCategory}
                  onValueChange={setSelectedCategory}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Todas as categorias">
                      {selectedCategory === 'all' ? (
                        'Todas as categorias'
                      ) : (
                        (() => {
                          const cat = categories.find(c => c.name === selectedCategory);
                          return cat ? (
                            <div className="flex items-center gap-2">
                              <div
                                className="w-4 h-4 rounded flex items-center justify-center text-xs"
                                style={{ backgroundColor: cat.color }}
                              >
                                {cat.icon}
                              </div>
                              <span>{cat.name}</span>
                            </div>
                          ) : selectedCategory;
                        })()
                      )}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas as categorias</SelectItem>
                    {categories
                      .sort((a, b) => a.name.localeCompare(b.name))
                      .map((category) => (
                        <SelectItem key={category.id} value={category.name}>
                          <div className="flex items-center gap-2">
                            <div
                              className="w-4 h-4 rounded flex items-center justify-center text-xs"
                              style={{ backgroundColor: category.color }}
                            >
                              {category.icon}
                            </div>
                            <span>{category.name}</span>
                          </div>
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Data inicial</label>
                <Input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Data final</label>
                <Input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Transactions Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>
            {filteredTransactions.length} {filteredTransactions.length === 1 ? 'Transação' : 'Transações'}
          </CardTitle>
          {totalPages > 1 && (
            <div className="text-sm text-muted-foreground">
              Página {currentPage} de {totalPages}
            </div>
          )}
        </CardHeader>
        <CardContent>
          {filteredTransactions.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/10">
                      <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                        Data
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                        Descricao
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                        Categoria
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                        Conta
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                        Tipo
                      </th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">
                        Valor
                      </th>
                      <th className="text-center py-3 px-4 text-sm font-medium text-muted-foreground">
                        Vínculo
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedTransactions.map((transaction) => (
                      <tr
                        key={transaction.id}
                        className="border-b border-white/5 hover:bg-white/5 transition-colors"
                      >
                        <td className="py-3 px-4">
                          <div className="flex flex-col">
                            <span className="text-sm font-medium text-white">
                              {format(new Date(transaction.date), 'dd/MM/yyyy', {
                                locale: ptBR,
                              })}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {format(new Date(transaction.date), 'HH:mm', {
                                locale: ptBR,
                              })}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex flex-col">
                            <span className="text-sm font-medium text-white">
                              {transaction.description}
                            </span>
                            {transaction.merchant_name && (
                              <span className="text-xs text-muted-foreground">
                                {transaction.merchant_name}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <Popover>
                            <PopoverTrigger asChild>
                              <button
                                className="text-sm px-2 py-1 bg-white/10 rounded hover:bg-white/20 transition-colors flex items-center gap-2 group"
                                disabled={updatingTransactionId === transaction.id}
                              >
                                {updatingTransactionId === transaction.id ? (
                                  <LoadingSpinner className="w-3 h-3" />
                                ) : (
                                  <>
                                    {(() => {
                                      const currentCategory = categories.find(
                                        c => c.id === transaction.user_category_id
                                      );
                                      return currentCategory ? (
                                        <>
                                          <div
                                            className="w-5 h-5 rounded flex items-center justify-center text-xs flex-shrink-0"
                                            style={{ backgroundColor: currentCategory.color }}
                                          >
                                            {currentCategory.icon}
                                          </div>
                                          <span>{currentCategory.name}</span>
                                        </>
                                      ) : (
                                        <span>{transaction.category || 'Sem categoria'}</span>
                                      );
                                    })()}
                                    <ChevronDownIcon className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                                  </>
                                )}
                              </button>
                            </PopoverTrigger>
                            <PopoverContent className="w-64 p-2" align="start">
                              <div className="space-y-1">
                                <div className="text-xs font-medium text-muted-foreground px-2 py-1">
                                  Selecione uma categoria
                                </div>
                                <button
                                  onClick={() => handleUpdateCategory(transaction.id, null)}
                                  className="w-full text-left px-2 py-1.5 text-sm rounded hover:bg-white/10 transition-colors flex items-center justify-between"
                                >
                                  <span>Remover categoria</span>
                                  {!transaction.user_category_id && (
                                    <CheckIcon className="h-4 w-4 text-green-500" />
                                  )}
                                </button>
                                <div className="border-t border-white/10 my-1" />
                                {categories
                                  .filter((c) =>
                                    transaction.type === 'CREDIT'
                                      ? c.type === 'income'
                                      : c.type === 'expense'
                                  )
                                  .map((category) => (
                                    <button
                                      key={category.id}
                                      onClick={() =>
                                        handleUpdateCategory(transaction.id, category.id)
                                      }
                                      className="w-full text-left px-2 py-1.5 text-sm rounded hover:bg-white/10 transition-colors flex items-center justify-between gap-2"
                                    >
                                      <div className="flex items-center gap-2">
                                        <div
                                          className="w-5 h-5 rounded flex items-center justify-center text-xs"
                                          style={{ backgroundColor: category.color }}
                                        >
                                          {category.icon}
                                        </div>
                                        <span>{category.name}</span>
                                      </div>
                                      {transaction.user_category_id === category.id && (
                                        <CheckIcon className="h-4 w-4 text-green-500" />
                                      )}
                                    </button>
                                  ))}
                              </div>
                            </PopoverContent>
                          </Popover>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex flex-col">
                            <span className="text-sm text-white">
                              {transaction.account_name}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {transaction.account_type}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`text-sm font-medium ${
                              transaction.type === 'CREDIT'
                                ? 'text-green-500'
                                : 'text-red-500'
                            }`}
                          >
                            {transaction.type === 'CREDIT' ? 'Receita' : 'Despesa'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <span
                            className={`text-sm font-semibold ${
                              transaction.type === 'CREDIT'
                                ? 'text-green-500'
                                : 'text-red-500'
                            }`}
                          >
                            {transaction.type === 'CREDIT' ? '+' : '-'}
                            {formatCurrency(Math.abs(transaction.amount))}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center">
                          {transaction.has_linked_bill && transaction.linked_bill ? (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger>
                                  <Badge className="bg-blue-100 text-blue-800 flex items-center gap-1">
                                    <DocumentTextIcon className="h-3 w-3" />
                                    Vinculada
                                  </Badge>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p className="font-medium">{transaction.linked_bill.description}</p>
                                  <p className="text-xs">
                                    Venc: {format(new Date(transaction.linked_bill.due_date), 'dd/MM/yyyy', { locale: ptBR })}
                                    {' • '}
                                    {formatCurrency(parseFloat(transaction.linked_bill.amount))}
                                  </p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          ) : (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    className="h-7 w-7 p-0"
                                    onClick={() => openLinkBillDialog(transaction)}
                                  >
                                    <LinkIcon className="h-4 w-4 text-muted-foreground" />
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>Vincular a conta</TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-6 pt-4 border-t border-white/10">
                  <div className="text-sm text-muted-foreground">
                    Mostrando {startIndex + 1} a {Math.min(endIndex, filteredTransactions.length)} de{' '}
                    {filteredTransactions.length} transações
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => goToPage(1)}
                      disabled={currentPage === 1}
                    >
                      Primeira
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => goToPage(currentPage - 1)}
                      disabled={currentPage === 1}
                    >
                      Anterior
                    </Button>
                    <div className="flex items-center gap-1">
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        let pageNumber;
                        if (totalPages <= 5) {
                          pageNumber = i + 1;
                        } else if (currentPage <= 3) {
                          pageNumber = i + 1;
                        } else if (currentPage >= totalPages - 2) {
                          pageNumber = totalPages - 4 + i;
                        } else {
                          pageNumber = currentPage - 2 + i;
                        }
                        return (
                          <Button
                            key={pageNumber}
                            variant={currentPage === pageNumber ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => goToPage(pageNumber)}
                            className="w-10"
                          >
                            {pageNumber}
                          </Button>
                        );
                      })}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => goToPage(currentPage + 1)}
                      disabled={currentPage === totalPages}
                    >
                      Próxima
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => goToPage(totalPages)}
                      disabled={currentPage === totalPages}
                    >
                      Última
                    </Button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12">
              <p className="text-white/60">
                Nenhuma transação encontrada com os filtros aplicados
              </p>
              {(searchTerm ||
                selectedAccount !== 'all' ||
                selectedType !== 'all' ||
                selectedCategory !== 'all' ||
                startDate ||
                endDate) && (
                <Button
                  variant="ghost"
                  onClick={clearFilters}
                  className="mt-4"
                >
                  Limpar filtros
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Link Bill Dialog */}
      <LinkBillDialog
        transaction={selectedTransaction}
        open={showLinkBillDialog}
        onOpenChange={setShowLinkBillDialog}
        onLinked={fetchData}
      />
    </div>
  );
}