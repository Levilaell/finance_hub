'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import Link from 'next/link';
import { formatCurrency } from '@/lib/utils';
import { 
  BanknotesIcon,
  CreditCardIcon,
  ChartBarIcon,
  DocumentTextIcon,
  ArrowDownIcon,
  ArrowUpIcon
} from '@heroicons/react/24/outline';

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

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
        <Button variant="outline">
          Atualizar
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
            <div className="text-2xl font-bold">{formatCurrency(0)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              0 contas conectadas
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
              {formatCurrency(0)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Despesas (Mês)</CardTitle>
            <ArrowUpIcon className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatCurrency(0)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resultado (Mês)</CardTitle>
            <ChartBarIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              0 transações
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
              <p className="text-center text-white/60 py-4">Nenhuma transação encontrada</p>
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
              <p className="text-center text-white/60 py-4">Nenhuma categoria encontrada</p>
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
                0 contas conectadas
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
                0 este mês
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