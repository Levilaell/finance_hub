'use client';

import { CreditCard, Wallet, TrendingUp, PiggyBank } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { AccountSummary } from '@/types/banking.types';

interface AccountSummaryCardsProps {
  summary: AccountSummary | undefined;
  isLoading: boolean;
}

export function AccountSummaryCards({ summary, isLoading }: AccountSummaryCardsProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const cards = [
    {
      title: 'Saldo em Contas',
      value: summary?.bank_accounts.total_balance || 0,
      icon: Wallet,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      description: `${summary?.bank_accounts.count || 0} conta${(summary?.bank_accounts.count || 0) !== 1 ? 's' : ''}`
    },
    {
      title: 'Cartões de Crédito',
      value: summary?.credit_cards.total_balance || 0,
      icon: CreditCard,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      description: `Limite: ${formatCurrency(summary?.credit_cards.total_limit || 0)}`,
      isNegative: true
    },
    {
      title: 'Patrimônio Líquido',
      value: summary?.net_worth || 0,
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      description: 'Total de ativos'
    },
    {
      title: 'Reserva de Emergência',
      value: 0, // This would come from a calculation or user settings
      icon: PiggyBank,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      description: 'Meta: 6 meses',
      hidden: true // Hidden for now
    }
  ];

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-8 w-8 rounded-full" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-7 w-32 mb-1" />
              <Skeleton className="h-3 w-20" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {cards.filter(card => !card.hidden).map((card) => {
        const Icon = card.icon;
        return (
          <Card key={card.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {card.title}
              </CardTitle>
              <div className={`${card.bgColor} p-2 rounded-full`}>
                <Icon className={`h-4 w-4 ${card.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {card.isNegative && card.value > 0 && '-'}
                {formatCurrency(Math.abs(card.value))}
              </div>
              <p className="text-xs text-muted-foreground">
                {card.description}
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}