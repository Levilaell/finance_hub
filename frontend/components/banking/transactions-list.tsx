'use client';

import { useState, useEffect } from 'react';
import { Transaction, TransactionFilter } from '@/types/banking';
import { bankingService } from '@/services/banking.service';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { EmptyState } from '@/components/ui/empty-state';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import {
  ArrowUpIcon,
  ArrowDownIcon,
  FunnelIcon,
  CalendarIcon,
  DocumentArrowDownIcon,
} from '@heroicons/react/24/outline';
import { format, subMonths } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { cn } from '@/lib/utils';

interface TransactionsListProps {
  accountId?: string;
  showFilters?: boolean;
  maxHeight?: string;
}

export function TransactionsList({
  accountId,
  showFilters = true,
  maxHeight = 'max-h-[600px]',
}: TransactionsListProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filters, setFilters] = useState<TransactionFilter>({
    account_id: accountId,
  });
  const [dateRange, setDateRange] = useState({
    from: format(subMonths(new Date(), 3), 'yyyy-MM-dd'), // Last 3 months
    to: format(new Date(), 'yyyy-MM-dd'),
  });

  useEffect(() => {
    fetchTransactions();
  }, [filters]);

  const fetchTransactions = async () => {
    setIsLoading(true);
    try {
      const data = await bankingService.getTransactions({
        ...filters,
        date_from: dateRange.from,
        date_to: dateRange.to,
      });
      setTransactions(data);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFilterChange = (key: keyof TransactionFilter, value: any) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleDateChange = (key: 'from' | 'to', value: string) => {
    setDateRange((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const applyDateFilter = () => {
    setFilters((prev) => ({
      ...prev,
      date_from: dateRange.from,
      date_to: dateRange.to,
    }));
  };

  const exportTransactions = () => {
    const csv = [
      ['Data', 'Descrição', 'Tipo', 'Valor', 'Categoria', 'Conta'].join(','),
      ...transactions.map((tx) =>
        [
          format(new Date(tx.date), 'dd/MM/yyyy'),
          tx.description,
          tx.type === 'CREDIT' ? 'Entrada' : 'Saída',
          tx.amount.toFixed(2),
          tx.category || '',
          tx.account_name,
        ].join(',')
      ),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transacoes_${format(new Date(), 'yyyy-MM-dd')}.csv`;
    a.click();
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <LoadingSpinner />
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <EmptyState
        icon={CalendarIcon}
        title="Nenhuma transação encontrada"
        description="Não há transações para o período selecionado"
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      {showFilters && (
        <div className="flex flex-col md:flex-row gap-3 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="flex gap-2 flex-1">
            <Input
              type="date"
              value={dateRange.from}
              onChange={(e) => handleDateChange('from', e.target.value)}
              className="max-w-[180px]"
            />
            <Input
              type="date"
              value={dateRange.to}
              onChange={(e) => handleDateChange('to', e.target.value)}
              className="max-w-[180px]"
            />
            <Button onClick={applyDateFilter} size="sm">
              <FunnelIcon className="h-4 w-4 mr-2" />
              Filtrar
            </Button>
          </div>

          <div className="flex gap-2">
            <Select
              value={filters.type || 'all'}
              onValueChange={(value) => handleFilterChange('type', value === 'all' ? undefined : value)}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Tipo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos</SelectItem>
                <SelectItem value="CREDIT">Entrada</SelectItem>
                <SelectItem value="DEBIT">Saída</SelectItem>
              </SelectContent>
            </Select>

            <Button onClick={exportTransactions} variant="outline" size="sm">
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              Exportar
            </Button>
          </div>
        </div>
      )}

      {/* Transactions Table */}
      <div className={cn('overflow-auto', maxHeight)}>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Data</TableHead>
              <TableHead>Descrição</TableHead>
              <TableHead>Categoria</TableHead>
              <TableHead>Conta</TableHead>
              <TableHead className="text-right">Valor</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {transactions.map((transaction) => (
              <TableRow key={transaction.id}>
                <TableCell className="font-medium">
                  {format(new Date(transaction.date), 'dd/MM/yyyy', { locale: ptBR })}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {transaction.type === 'CREDIT' ? (
                      <ArrowUpIcon className="h-4 w-4 text-green-600" />
                    ) : (
                      <ArrowDownIcon className="h-4 w-4 text-red-600" />
                    )}
                    <span>{transaction.description}</span>
                  </div>
                </TableCell>
                <TableCell>
                  {transaction.category && (
                    <Badge variant="secondary" className="text-xs">
                      {transaction.category}
                    </Badge>
                  )}
                </TableCell>
                <TableCell className="text-sm text-gray-600">
                  {transaction.account_name}
                </TableCell>
                <TableCell className="text-right">
                  <span
                    className={cn(
                      'font-semibold',
                      transaction.type === 'CREDIT' ? 'text-green-600' : 'text-red-600'
                    )}
                  >
                    {transaction.type === 'CREDIT' ? '+' : '-'}
                    {bankingService.formatCurrency(
                      transaction.amount,
                      transaction.currency_code
                    )}
                  </span>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Summary */}
      <div className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <div className="text-sm text-gray-600">
          Total de {transactions.length} transações
        </div>
        <div className="flex gap-4 text-sm">
          <span className="text-green-600">
            Entradas:{' '}
            {bankingService.formatCurrency(
              transactions
                .filter((tx) => tx.type === 'CREDIT')
                .reduce((sum, tx) => sum + tx.amount, 0),
              'BRL'
            )}
          </span>
          <span className="text-red-600">
            Saídas:{' '}
            {bankingService.formatCurrency(
              transactions
                .filter((tx) => tx.type === 'DEBIT')
                .reduce((sum, tx) => sum + tx.amount, 0),
              'BRL'
            )}
          </span>
        </div>
      </div>
    </div>
  );
}