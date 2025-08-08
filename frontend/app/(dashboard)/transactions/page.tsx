'use client';

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { EmptyState } from '@/components/ui/empty-state';
import { bankingService } from '@/services/banking.service';
import { TransactionFilters } from '@/types/banking.types';
import { formatCurrency, formatDate } from '@/lib/utils';
import { testId, TEST_IDS, testIdWithIndex } from '@/utils/test-helpers';
import { 
  BanknotesIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
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

  // Fetch accounts
  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => bankingService.getAccounts(),
  });

  // Fetch transactions
  const { data: transactions, isLoading, error } = useQuery({
    queryKey: ['transactions', filters, page],
    queryFn: () => bankingService.getTransactions({ ...filters, page }),
  });

  // Fetch categories
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => bankingService.getCategories(),
  });

  // Calculate totals
  const totals = useMemo(() => {
    if (!transactions?.results) return { income: 0, expenses: 0, balance: 0 };
    
    return transactions.results.reduce((acc, transaction) => {
      const amount = Math.abs(transaction.amount);
      if (transaction.type === 'CREDIT') {
        acc.income += amount;
      } else {
        acc.expenses += amount;
      }
      return acc;
    }, { income: 0, expenses: 0, balance: 0 });
  }, [transactions]);

  totals.balance = totals.income - totals.expenses;

  // Handle search
  const handleSearch = () => {
    setFilters({ ...filters, search: searchTerm });
    setPage(1);
  };

  // Export transactions
  const handleExport = async () => {
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
    } catch (error) {
      console.error('Export failed:', error);
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
            className="bg-white/10 hover:bg-white/20 border-white/20 transition-all duration-300"
            {...testId(TEST_IDS.banking.exportButton)}
          >
            <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
            Exportar
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="hover:shadow-lg transition-all duration-300 hover:scale-105">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Receitas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-foreground">
              {formatCurrency(totals.income)}
            </p>
            <p className="text-xs text-success-subtle mt-1">Total de entradas</p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-all duration-300 hover:scale-105">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Despesas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-foreground">
              {formatCurrency(totals.expenses)}
            </p>
            <p className="text-xs text-error-subtle mt-1">Total de saídas</p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-all duration-300 hover:scale-105">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Saldo
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className={`text-2xl font-bold ${totals.balance >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {formatCurrency(totals.balance)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card className="shadow-md">
        <CardContent className="pt-6">
          <div className="flex gap-2 mb-4">
            <div className="flex-1">
              <Input
                placeholder="Buscar transações..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <Button 
              onClick={handleSearch}
              className="bg-white text-black hover:bg-white/90 transition-all duration-300"
            >
              Buscar
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className="bg-white/10 hover:bg-white/20 border-white/20 transition-all duration-300"
              {...testId(TEST_IDS.banking.filterCategory)}
            >
              <FunnelIcon className="h-4 w-4 mr-2" />
              Filtros
            </Button>
          </div>

          {showFilters && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 pt-4 border-t">
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
          )}
        </CardContent>
      </Card>

      {/* Transactions List */}
      <Card className="shadow-md">
        <CardContent className="p-0">
          {transactions?.results && transactions.results.length > 0 ? (
            <div className="overflow-x-auto" {...testId(TEST_IDS.banking.transactionList)}>
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
                <tbody className="bg-white divide-y divide-gray-200">
                  {transactions.results.map((transaction, index) => (
                    <tr key={transaction.id} className="hover:bg-white/5 transition-all duration-200" {...testIdWithIndex(TEST_IDS.banking.transactionItem, index)}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                        {formatDate(transaction.date)}
                      </td>
                      <td className="px-6 py-4 text-sm text-foreground">
                        {transaction.description}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                        {transaction.category_detail ? (
                          <span className="inline-flex items-center gap-1">
                            {transaction.category_detail.icon} 
                            {transaction.category_detail.name}
                          </span>
                        ) : (
                          <span className="text-muted-foreground/60">Sem categoria</span>
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