'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { bankingService } from '@/services/banking.service';
import { billsService } from '@/services/bills.service';
import {
  FinancialSummary,
  Transaction,
  BankAccount,
  CategorySummary,
  BillsSummary
} from '@/types/banking';
import { format, startOfMonth, endOfMonth } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Progress } from '@/components/ui/progress';
import Link from 'next/link';
import { formatCurrency } from '@/lib/utils';
import {
  BanknotesIcon,
  CreditCardIcon,
  ChartBarIcon,
  DocumentTextIcon,
  ArrowDownIcon,
  ArrowUpIcon,
  ArrowPathIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon
} from '@heroicons/react/24/outline';

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [summary, setSummary] = useState<FinancialSummary | null>(null);
  const [billsSummary, setBillsSummary] = useState<BillsSummary | null>(null);
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [topCategories, setTopCategories] = useState<CategorySummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    fetchDashboardData();
  }, [isAuthenticated, router]);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      // Fetch all data in parallel
      const [summaryData, billsSummaryData, transactionsData, accountsData, categoriesData] = await Promise.all([
        bankingService.getFinancialSummary(),
        billsService.getSummary(),
        bankingService.getTransactions({ limit: 5 }),
        bankingService.getAccounts(),
        bankingService.getCategorySummary()
      ]);

      setSummary(summaryData);
      setBillsSummary(billsSummaryData);
      setRecentTransactions(transactionsData);
      setAccounts(accountsData);
      setTopCategories(categoriesData);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      // Initialize with empty data if error
      setSummary({
        income: 0,
        expenses: 0,
        balance: 0,
        period_start: startOfMonth(new Date()).toISOString(),
        period_end: endOfMonth(new Date()).toISOString(),
        accounts_count: 0,
        transactions_count: 0
      });
      setBillsSummary({
        total_receivable: 0,
        total_receivable_month: 0,
        total_payable: 0,
        total_payable_month: 0,
        total_overdue: 0,
        overdue_count: 0,
        receivable_count: 0,
        payable_count: 0
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchDashboardData();
    setIsRefreshing(false);
  };

  if (!isAuthenticated || !user || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  // Only sum balance from non-credit card accounts (checking, savings, etc.)
  // Credit cards show the invoice balance, not available funds
  const totalBalance = accounts
    .filter(acc => !acc.is_credit_card && acc.type !== 'CREDIT_CARD')
    .reduce((sum, acc) => {
      const balance = typeof acc.balance === 'string' ? parseFloat(acc.balance) : acc.balance;
      return sum + (isNaN(balance) ? 0 : balance);
    }, 0);
  const monthlyIncome = summary?.income || 0;
  const monthlyExpenses = summary?.expenses || 0;
  // Use balance from API (expenses are already negative)
  const monthlyResult = summary?.balance || 0;

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-white">
            Olá, {user?.first_name || user?.email?.split('@')[0]}! 👋
          </h1>
          <p className="text-white/70 mt-1">
            Aqui está o resumo da sua situação financeira
          </p>
        </div>
        <Button
          variant="outline"
          onClick={handleRefresh}
          disabled={isRefreshing}
        >
          {isRefreshing ? (
            <>
              <ArrowPathIcon className="h-4 w-4 mr-2 animate-spin" />
              Atualizando...
            </>
          ) : (
            <>
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Atualizar
            </>
          )}
        </Button>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Saldo Total</CardTitle>
            <BanknotesIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalBalance)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {accounts.length} {accounts.length === 1 ? 'conta conectada' : 'contas conectadas'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Receitas (Mês)</CardTitle>
            <ArrowDownIcon className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(monthlyIncome)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {summary?.period_start && format(new Date(summary.period_start + 'T12:00:00'), 'MMM', { locale: ptBR })}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Despesas (Mês)</CardTitle>
            <ArrowUpIcon className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatCurrency(Math.abs(monthlyExpenses))}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {summary?.period_start && format(new Date(summary.period_start + 'T12:00:00'), 'MMM', { locale: ptBR })}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resultado (Mês)</CardTitle>
            <ChartBarIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${monthlyResult >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {monthlyResult >= 0 && '+'}{formatCurrency(monthlyResult)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {summary?.transactions_count || 0} transações
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Bills Cards - Contas a Pagar/Receber */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">A Receber (Mês)</CardTitle>
            <ArrowTrendingUpIcon className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(billsSummary?.total_receivable_month || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {billsSummary?.receivable_count || 0} conta{billsSummary?.receivable_count !== 1 ? 's' : ''} pendente{billsSummary?.receivable_count !== 1 ? 's' : ''}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">A Pagar (Mês)</CardTitle>
            <ArrowTrendingDownIcon className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatCurrency(billsSummary?.total_payable_month || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {billsSummary?.payable_count || 0} conta{billsSummary?.payable_count !== 1 ? 's' : ''} pendente{billsSummary?.payable_count !== 1 ? 's' : ''}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Atrasadas</CardTitle>
            <DocumentTextIcon className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {formatCurrency(billsSummary?.total_overdue || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {billsSummary?.overdue_count || 0} conta{billsSummary?.overdue_count !== 1 ? 's' : ''} atrasada{billsSummary?.overdue_count !== 1 ? 's' : ''}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Recent Transactions */}
        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Transações Recentes</CardTitle>
            <Link href="/transactions">
              <Button variant="ghost" size="sm">Ver todas</Button>
            </Link>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentTransactions.length > 0 ? (
                recentTransactions
                  .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
                  .slice(0, 7)
                  .map((transaction) => (
                  <div
                    key={transaction.id}
                    className="flex items-center justify-between py-3 border-b border-white/10 last:border-0"
                  >
                    <div className="flex-1">
                      <p className="font-medium text-sm">{transaction.description}</p>
                      <p className="text-xs text-muted-foreground">
                        {transaction.category} • {format(new Date(transaction.date), 'dd MMM HH:mm', { locale: ptBR })}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={`font-semibold ${
                        transaction.type === 'CREDIT' ? 'text-green-500' : 'text-red-500'
                      }`}>
                        {transaction.type === 'CREDIT' ? '+' : '-'}
                        {formatCurrency(Math.abs(transaction.amount))}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center text-white/60 py-8">Nenhuma transação encontrada</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Top Categories */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Principais Categorias (Mês)</CardTitle>
            <Link href="/categories">
              <Button variant="ghost" size="sm">Ver todas</Button>
            </Link>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {topCategories && Object.keys(topCategories).length > 0 ? (
                Object.entries(topCategories)
                  .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                  .slice(0, 5)
                  .map(([category, amount]) => {
                    const totalExpenses = Object.values(topCategories).reduce((sum, val) => sum + Math.abs(val), 0);
                    const percentage = totalExpenses > 0 ? (Math.abs(amount) / totalExpenses) * 100 : 0;

                    return (
                      <div key={category} className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">{category}</span>
                          <span className="font-medium">{formatCurrency(Math.abs(amount))}</span>
                        </div>
                        <Progress value={percentage} className="h-2" />
                      </div>
                    );
                  })
              ) : (
                <p className="text-center text-white/60 py-8">Nenhuma categoria encontrada</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        <Link href="/accounts">
          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <CreditCardIcon className="h-5 w-5" />
                Contas Bancárias
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-white/70">
                {accounts.length} {accounts.length === 1 ? 'conta conectada' : 'contas conectadas'}
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/transactions">
          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <BanknotesIcon className="h-5 w-5" />
                Transações
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-white/70">
                {summary?.transactions_count || 0} este mês
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/reports">
          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <DocumentTextIcon className="h-5 w-5" />
                Relatórios
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-white/70">
                Gerar relatórios financeiros
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}