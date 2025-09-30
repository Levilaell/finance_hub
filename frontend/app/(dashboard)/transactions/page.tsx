'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { bankingService } from '@/services/banking.service';
import { Transaction, BankAccount } from '@/types/banking';
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
  XMarkIcon
} from '@heroicons/react/24/outline';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export default function TransactionsPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [filteredTransactions, setFilteredTransactions] = useState<Transaction[]>([]);
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

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
  const itemsPerPage = 20;

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
      const [transactionsData, accountsData] = await Promise.all([
        bankingService.getTransactions(),
        bankingService.getAccounts()
      ]);
      setTransactions(transactionsData);
      setAccounts(accountsData);
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

  const clearFilters = () => {
    setSearchTerm('');
    setSelectedAccount('all');
    setSelectedType('all');
    setSelectedCategory('all');
    setStartDate('');
    setEndDate('');
  };

  const exportToCSV = () => {
    const headers = ['Data', 'Hora', 'Descricao', 'Categoria', 'Conta', 'Tipo', 'Valor'];
    const rows = filteredTransactions.map((t) => [
      format(new Date(t.date), 'dd/MM/yyyy', { locale: ptBR }),
      format(new Date(t.date), 'HH:mm', { locale: ptBR }),
      t.description,
      t.category || 'Sem categoria',
      t.account_name,
      t.type === 'CREDIT' ? 'Receita' : 'Despesa',
      t.amount.toFixed(2)
    ]);

    const csv = [headers, ...rows].map((row) => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `transacoes_${format(new Date(), 'yyyy-MM-dd')}.csv`;
    link.click();
  };

  // Get unique categories for filter
  const categories = Array.from(
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

  // Pagination calculations
  const totalPages = Math.ceil(filteredTransactions.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedTransactions = filteredTransactions.slice(startIndex, endIndex);

  const goToPage = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
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
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-white">Transações</h1>
          <p className="text-white/70 mt-1">
            Todas as suas transações em um só lugar
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
          >
            <FunnelIcon className="h-4 w-4 mr-2" />
            Filtros
          </Button>
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            {isRefreshing ? (
              <ArrowPathIcon className="h-4 w-4 animate-spin" />
            ) : (
              <ArrowPathIcon className="h-4 w-4" />
            )}
          </Button>
          <Button variant="outline" onClick={exportToCSV}>
            <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
            Exportar
          </Button>
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
                    <SelectValue placeholder="Todas as categorias" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas as categorias</SelectItem>
                    {categories.map((category) => (
                      <SelectItem key={category} value={category!}>
                        {category}
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
            {filteredTransactions.length} Transacao
            {filteredTransactions.length === 1 ? '' : 'es'}
          </CardTitle>
          {totalPages > 1 && (
            <div className="text-sm text-muted-foreground">
              Pagina {currentPage} de {totalPages}
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
                          {transaction.category && (
                            <span className="text-sm px-2 py-1 bg-white/10 rounded">
                              {transaction.category}
                            </span>
                          )}
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
                    {filteredTransactions.length} transacoes
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
                      Proxima
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => goToPage(totalPages)}
                      disabled={currentPage === totalPages}
                    >
                      Ultima
                    </Button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12">
              <p className="text-white/60">
                Nenhuma transacao encontrada com os filtros aplicados
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
    </div>
  );
}