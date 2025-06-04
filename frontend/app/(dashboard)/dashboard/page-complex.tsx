'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { bankingService } from '@/services/banking.service';
import { reportsService } from '@/services/reports.service';
import { 
  BanknotesIcon, 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon,
  CreditCardIcon,
  ChartBarIcon,
  ClockIcon,
  ChartPieIcon
} from '@heroicons/react/24/outline';
import { formatCurrency } from '@/lib/utils';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => reportsService.getDashboardStats(),
  });

  const { data: recentTransactions } = useQuery({
    queryKey: ['recent-transactions'],
    queryFn: () => bankingService.getTransactions({ limit: 5 }),
  });

  const { data: accounts } = useQuery({
    queryKey: ['bank-accounts'],
    queryFn: () => bankingService.getBankAccounts(),
  });

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (statsError) {
    return <ErrorMessage message="Failed to load dashboard data" />;
  }

  const statCards = [
    {
      title: 'Total Balance',
      value: formatCurrency(stats?.total_balance || 0),
      icon: BanknotesIcon,
      change: null,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Income This Month',
      value: formatCurrency(stats?.income_this_month || 0),
      icon: ArrowTrendingUpIcon,
      change: '+12.5%',
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: 'Expenses This Month',
      value: formatCurrency(stats?.expenses_this_month || 0),
      icon: ArrowTrendingDownIcon,
      change: '-3.2%',
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
    {
      title: 'Net Income',
      value: formatCurrency(stats?.net_income || 0),
      icon: ChartBarIcon,
      change: stats?.net_income > 0 ? '+' : '',
      color: stats?.net_income >= 0 ? 'text-green-600' : 'text-red-600',
      bgColor: stats?.net_income >= 0 ? 'bg-green-100' : 'bg-red-100',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-gray-600">Welcome back! Here's your financial overview.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <Card key={stat.title}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <p className="text-sm text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold">{stat.value}</p>
                  {stat.change && (
                    <p className={`text-sm ${stat.color}`}>{stat.change}</p>
                  )}
                </div>
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Bank Accounts */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Bank Accounts</CardTitle>
            <Link href="/accounts">
              <Button variant="ghost" size="sm">View All</Button>
            </Link>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {accounts?.results?.slice(0, 3).map((account) => (
                <div key={account.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="p-2 bg-gray-100 rounded-lg">
                      <CreditCardIcon className="h-5 w-5 text-gray-600" />
                    </div>
                    <div>
                      <p className="font-medium">{account.account_name}</p>
                      <p className="text-sm text-gray-600">{account.provider.name}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">{formatCurrency(account.current_balance)}</p>
                    <p className="text-sm text-gray-600">{account.account_type}</p>
                  </div>
                </div>
              ))}
              {(!accounts?.results || accounts.results.length === 0) && (
                <div className="text-center py-8 text-gray-500">
                  <CreditCardIcon className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p>No bank accounts connected</p>
                  <Link href="/accounts">
                    <Button variant="link" size="sm">Add Account</Button>
                  </Link>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Transactions */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Transactions</CardTitle>
            <Link href="/transactions">
              <Button variant="ghost" size="sm">View All</Button>
            </Link>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentTransactions?.results?.map((transaction) => (
                <div key={transaction.id} className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className={`p-2 rounded-lg ${
                      transaction.transaction_type === 'credit' 
                        ? 'bg-green-100' 
                        : 'bg-red-100'
                    }`}>
                      {transaction.transaction_type === 'credit' ? (
                        <ArrowTrendingUpIcon className="h-4 w-4 text-green-600" />
                      ) : (
                        <ArrowTrendingDownIcon className="h-4 w-4 text-red-600" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium">{transaction.description}</p>
                      <p className="text-sm text-gray-600">
                        {new Date(transaction.transaction_date).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <p className={`font-semibold ${
                    transaction.transaction_type === 'credit'
                      ? 'text-green-600'
                      : 'text-red-600'
                  }`}>
                    {transaction.transaction_type === 'credit' ? '+' : '-'}
                    {formatCurrency(Math.abs(transaction.amount))}
                  </p>
                </div>
              ))}
              {(!recentTransactions?.results || recentTransactions.results.length === 0) && (
                <div className="text-center py-8 text-gray-500">
                  <ClockIcon className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p>No recent transactions</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <Link href="/accounts">
              <Button variant="outline" className="w-full">
                <CreditCardIcon className="h-4 w-4 mr-2" />
                Add Account
              </Button>
            </Link>
            <Link href="/transactions">
              <Button variant="outline" className="w-full">
                <BanknotesIcon className="h-4 w-4 mr-2" />
                View Transactions
              </Button>
            </Link>
            <Link href="/reports">
              <Button variant="outline" className="w-full">
                <ChartBarIcon className="h-4 w-4 mr-2" />
                Generate Report
              </Button>
            </Link>
            <Link href="/categories">
              <Button variant="outline" className="w-full">
                <ChartPieIcon className="h-4 w-4 mr-2" />
                Manage Categories
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}