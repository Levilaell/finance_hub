'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { useTransactions, useBankAccounts } from '@/hooks/use-banking';

import { TransactionsList } from '@/components/banking/transactions-list';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

import {
  ArrowLeftIcon,
  DocumentChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  BanknotesIcon,
} from '@heroicons/react/24/outline';
import { format, subMonths } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { bankingService } from '@/services/banking.service';

export default function TransactionsPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuthStore();
  const { accounts, isLoading: isLoadingAccounts } = useBankAccounts();

  const [dateRange] = useState({
    from: format(subMonths(new Date(), 3), 'yyyy-MM-dd'), // Last 3 months
    to: format(new Date(), 'yyyy-MM-dd'),
  });

  const { transactions, isLoading: isLoadingTransactions } = useTransactions({
    date_from: dateRange.from,
    date_to: dateRange.to,
  });

  if (authLoading || isLoadingAccounts || isLoadingTransactions) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (!isAuthenticated) {
    router.push('/login');
    return null;
  }

  // Calculate summary
  const totalIncome = transactions
    .filter((tx) => tx.type === 'CREDIT')
    .reduce((sum, tx) => sum + tx.amount, 0);

  const totalExpenses = transactions
    .filter((tx) => tx.type === 'DEBIT')
    .reduce((sum, tx) => sum + tx.amount, 0);

  const balance = totalIncome - totalExpenses;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push('/accounts')}
            className="text-white hover:bg-white/10"
          >
            <ArrowLeftIcon className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-white">Transações</h1>
            <p className="text-muted-foreground mt-1">
              {format(new Date(dateRange.from), 'dd MMM', { locale: ptBR })} -{' '}
              {format(new Date(dateRange.to), 'dd MMM yyyy', { locale: ptBR })}
            </p>
          </div>
        </div>
        <Button
          onClick={() => router.push('/reports')}
          variant="outline"
          className="border-white/20 text-white hover:bg-white/10"
        >
          <DocumentChartBarIcon className="h-4 w-4 mr-2" />
          Gerar Relatório
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gray-800/50 border-gray-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">
              Saldo do Período
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {bankingService.formatCurrency(balance, 'BRL')}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-800/50 border-gray-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">
              Entradas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">
              {bankingService.formatCurrency(totalIncome, 'BRL')}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-800/50 border-gray-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">
              Saídas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">
              {bankingService.formatCurrency(totalExpenses, 'BRL')}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-800/50 border-gray-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">
              Total de Transações
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {transactions.length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Transactions List */}
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle>Todas as Transações</CardTitle>
        </CardHeader>
        <CardContent>
          <TransactionsList showFilters={true} />
        </CardContent>
      </Card>
    </div>
  );
}