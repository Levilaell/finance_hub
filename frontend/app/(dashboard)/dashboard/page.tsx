'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { useBankingStore } from '@/store/banking-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { HydrationBoundary } from '@/components/hydration-boundary';
import Link from 'next/link';
import { formatCurrency, formatDate } from '@/lib/utils';
import { 
  ArrowUpIcon, 
  ArrowDownIcon,
  BanknotesIcon,
  CreditCardIcon,
  ChartBarIcon,
  DocumentTextIcon,
  PlusIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon
} from '@heroicons/react/24/outline';

interface DashboardData {
  current_balance: number;
  monthly_income: number;
  monthly_expenses: number;
  monthly_net: number;
  recent_transactions: Transaction[];
  top_categories: CategorySummary[];
  accounts_count: number;
  transactions_count: number;
  active_budgets?: Budget[];
  budgets_summary?: BudgetsSummary;
  active_goals?: FinancialGoal[];
  goals_summary?: GoalsSummary;
  monthly_trends?: MonthlyTrend[];
  expense_trends?: ExpenseTrend[];
  income_comparison?: Comparison;
  expense_comparison?: Comparison;
  financial_insights?: string[];
  alerts?: Alert[];
}

interface Transaction {
  id: number;
  description: string;
  amount: number;
  transaction_date: string;
  transaction_type: string;
  category_name?: string;
  category_icon?: string;
  bank_account_name: string;
}

interface CategorySummary {
  category__name: string;
  category__icon: string;
  total: number;
  count: number;
}

interface Budget {
  id: number;
  name: string;
  amount: number;
  spent_amount: number;
  remaining_amount: number;
  spent_percentage: number;
  is_exceeded: boolean;
}

interface BudgetsSummary {
  total_budgets: number;
  total_budget_amount: number;
  total_spent: number;
  exceeded_count: number;
}

interface FinancialGoal {
  id: number;
  name: string;
  target_amount: number;
  current_amount: number;
  progress_percentage: number;
  days_remaining?: number;
}

interface GoalsSummary {
  total_goals: number;
  completed_goals: number;
  total_target_amount: number;
  total_current_amount: number;
}

interface MonthlyTrend {
  date: string;
  income: number;
  expenses: number;
  balance: number;
  net_flow: number;
}

interface ExpenseTrend {
  period: string;
  category: string;
  amount: number;
  transaction_count: number;
  change_from_previous: number;
  change_percentage: number;
}

interface Comparison {
  current_period: number;
  previous_period: number;
  variance: number;
  variance_percentage: number;
  trend: 'up' | 'down' | 'stable';
}

interface Alert {
  type: string;
  message: string;
  severity: 'high' | 'medium' | 'low';
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const { accounts, fetchAccounts } = useBankingStore();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    fetchDashboardData();
    fetchAccounts();
  }, [isAuthenticated]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const { dashboardService } = await import('@/services/dashboard.service');
      const data = await dashboardService.getDashboardData();
      setDashboardData(data);
    } catch (err) {
      console.error('Dashboard error:', err);
      setError('Erro ao carregar dados do dashboard');
    } finally {
      setLoading(false);
    }
  };

  const getTransactionIcon = (type: string) => {
    switch (type) {
      case 'credit':
      case 'transfer_in':
      case 'pix_in':
        return <ArrowDownIcon className="h-4 w-4 text-green-500" />;
      default:
        return <ArrowUpIcon className="h-4 w-4 text-red-500" />;
    }
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <ArrowTrendingUpIcon className="h-4 w-4 text-green-500" />;
      case 'down':
        return <ArrowTrendingDownIcon className="h-4 w-4 text-red-500" />;
      default:
        return <span className="h-4 w-4 text-gray-500">—</span>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <ErrorMessage message={error} onRetry={fetchDashboardData} />
      </div>
    );
  }

  if (!dashboardData) {
    return null;
  }

  return (
    <HydrationBoundary>
      <div className="space-y-6">
        {/* Welcome Section */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Olá, {user?.first_name || user?.email?.split('@')[0]}! 👋
          </h1>
          <p className="text-gray-600 mt-1">
            Aqui está o resumo da sua situação financeira
          </p>
        </div>

      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Saldo Total</CardTitle>
            <BanknotesIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(dashboardData.current_balance)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {dashboardData.accounts_count} conta{dashboardData.accounts_count !== 1 ? 's' : ''} conectada{dashboardData.accounts_count !== 1 ? 's' : ''}
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
              {formatCurrency(dashboardData.monthly_income)}
            </div>
            {dashboardData.income_comparison && (
              <div className="flex items-center gap-1 mt-1">
                {getTrendIcon(dashboardData.income_comparison.trend)}
                <span className={`text-xs ${
                  dashboardData.income_comparison.variance >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {dashboardData.income_comparison.variance_percentage.toFixed(1)}%
                </span>
                <span className="text-xs text-muted-foreground">vs mês anterior</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Despesas (Mês)</CardTitle>
            <ArrowUpIcon className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatCurrency(dashboardData.monthly_expenses)}
            </div>
            {dashboardData.expense_comparison && (
              <div className="flex items-center gap-1 mt-1">
                {getTrendIcon(dashboardData.expense_comparison.trend)}
                <span className={`text-xs ${
                  dashboardData.expense_comparison.variance <= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {Math.abs(dashboardData.expense_comparison.variance_percentage).toFixed(1)}%
                </span>
                <span className="text-xs text-muted-foreground">vs mês anterior</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resultado (Mês)</CardTitle>
            <ChartBarIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${
              dashboardData.monthly_net >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatCurrency(dashboardData.monthly_net)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {dashboardData.transactions_count} transações
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Alerts */}
      {dashboardData.alerts && dashboardData.alerts.length > 0 && (
        <div className="space-y-2">
          {dashboardData.alerts.map((alert, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border ${
                alert.severity === 'high' 
                  ? 'bg-red-50 border-red-200' 
                  : alert.severity === 'medium'
                  ? 'bg-yellow-50 border-yellow-200'
                  : 'bg-blue-50 border-blue-200'
              }`}
            >
              <p className={`text-sm ${
                alert.severity === 'high' 
                  ? 'text-red-800' 
                  : alert.severity === 'medium'
                  ? 'text-yellow-800'
                  : 'text-blue-800'
              }`}>
                {alert.message}
              </p>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Transactions */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Transações Recentes</CardTitle>
            <Link href="/transactions">
              <Button variant="ghost" size="sm">Ver todas</Button>
            </Link>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {dashboardData.recent_transactions.length > 0 ? (
                dashboardData.recent_transactions.slice(0, 5).map((transaction) => (
                  <div key={transaction.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50">
                    <div className="flex items-center gap-3">
                      {getTransactionIcon(transaction.transaction_type)}
                      <div>
                        <p className="font-medium text-sm">{transaction.description}</p>
                        <p className="text-xs text-gray-500">
                          {transaction.category_name || 'Sem categoria'} • {transaction.bank_account_name}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`font-medium ${
                        ['credit', 'transfer_in', 'pix_in'].includes(transaction.transaction_type)
                          ? 'text-green-600'
                          : 'text-red-600'
                      }`}>
                        {formatCurrency(transaction.amount)}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatDate(transaction.transaction_date)}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center text-gray-500 py-4">Nenhuma transação encontrada</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Top Categories */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Principais Categorias</CardTitle>
            <Link href="/categories">
              <Button variant="ghost" size="sm">Ver todas</Button>
            </Link>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dashboardData.top_categories.length > 0 ? (
                dashboardData.top_categories.slice(0, 5).map((category, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{category.category__icon || '📊'}</span>
                      <span className="text-sm font-medium">{category.category__name}</span>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{formatCurrency(Math.abs(category.total))}</p>
                      <p className="text-xs text-gray-500">{category.count} transações</p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center text-gray-500 py-4">Nenhuma categoria encontrada</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Link href="/accounts">
          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <CreditCardIcon className="h-5 w-5" />
                Contas Bancárias
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                {accounts.length} conta{accounts.length !== 1 ? 's' : ''} conectada{accounts.length !== 1 ? 's' : ''}
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
              <p className="text-sm text-gray-600">
                {dashboardData.transactions_count} este mês
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
              <p className="text-sm text-gray-600">
                Gerar relatórios financeiros
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/transactions/new">
          <Card className="hover:shadow-lg transition-shadow cursor-pointer bg-blue-50 border-blue-200">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2 text-blue-700">
                <PlusIcon className="h-5 w-5" />
                Nova Transação
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-blue-600">
                Adicionar manualmente
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>

        {/* Financial Insights */}
        {dashboardData.financial_insights && dashboardData.financial_insights.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Insights Financeiros</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {dashboardData.financial_insights.map((insight, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <span className="text-blue-500 mt-0.5">💡</span>
                    <p className="text-sm text-gray-600">{insight}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </HydrationBoundary>
  );
}