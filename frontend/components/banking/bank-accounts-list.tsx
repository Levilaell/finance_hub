'use client';

import { useState } from 'react';
import { Plus, TrendingUp, TrendingDown, Wallet } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BankAccountCard } from './bank-account-card';
import { BankAccountCardCompact } from './bank-account-card-compact';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import type { BankAccount } from '@/types/banking.types';

interface BankAccountsListProps {
  accounts: BankAccount[];
  onSync?: (accountId: string) => void;
  onManageConnection?: (connectionId: string) => void;
  onAddConnection?: () => void;
  syncingAccountIds?: string[];
  viewMode?: 'cards' | 'compact';
}

export function BankAccountsList({
  accounts,
  onSync,
  onManageConnection,
  onAddConnection,
  syncingAccountIds = [],
  viewMode = 'cards',
}: BankAccountsListProps) {
  const [selectedView, setSelectedView] = useState(viewMode);

  // Calculate totals
  const totals = accounts.reduce(
    (acc, account) => {
      if (account.type === 'BANK') {
        acc.bank += account.balance;
      } else if (account.type === 'CREDIT') {
        acc.credit += Math.abs(account.balance);
        if (account.credit_data?.available_credit_limit) {
          acc.creditLimit += account.credit_data.available_credit_limit;
        }
      }
      acc.total += account.balance;
      return acc;
    },
    { total: 0, bank: 0, credit: 0, creditLimit: 0 }
  );

  // Group accounts by type
  const bankAccounts = accounts.filter(acc => acc.type === 'BANK');
  const creditAccounts = accounts.filter(acc => acc.type === 'CREDIT');

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Saldo Total</p>
                <p className={cn(
                  "text-2xl font-bold",
                  totals.total >= 0 ? "text-green-600" : "text-red-600"
                )}>
                  {new Intl.NumberFormat('pt-BR', {
                    style: 'currency',
                    currency: 'BRL'
                  }).format(totals.total)}
                </p>
              </div>
              <div className={cn(
                "p-2 rounded-lg",
                totals.total >= 0 ? "bg-green-100" : "bg-red-100"
              )}>
                {totals.total >= 0 ? (
                  <TrendingUp className="w-5 h-5 text-green-600" />
                ) : (
                  <TrendingDown className="w-5 h-5 text-red-600" />
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Contas Bancárias</p>
                <p className="text-2xl font-bold">
                  {new Intl.NumberFormat('pt-BR', {
                    style: 'currency',
                    currency: 'BRL'
                  }).format(totals.bank)}
                </p>
              </div>
              <div className="p-2 bg-blue-100 rounded-lg">
                <Wallet className="w-5 h-5 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Cartões de Crédito</p>
                <p className="text-2xl font-bold text-orange-600">
                  {new Intl.NumberFormat('pt-BR', {
                    style: 'currency',
                    currency: 'BRL'
                  }).format(totals.credit)}
                </p>
                {totals.creditLimit > 0 && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Limite: {new Intl.NumberFormat('pt-BR', {
                      style: 'currency',
                      currency: 'BRL'
                    }).format(totals.creditLimit)}
                  </p>
                )}
              </div>
              <div className="p-2 bg-orange-100 rounded-lg">
                <Wallet className="w-5 h-5 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Accounts List */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Minhas Contas</CardTitle>
          <div className="flex items-center gap-2">
            <Tabs value={selectedView} onValueChange={(v) => setSelectedView(v as 'cards' | 'compact')}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="cards">Cards</TabsTrigger>
                <TabsTrigger value="compact">Lista</TabsTrigger>
              </TabsList>
            </Tabs>
            {onAddConnection && (
              <Button onClick={onAddConnection} size="sm">
                <Plus className="w-4 h-4 mr-2" />
                Adicionar Conta
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {accounts.length === 0 ? (
            <div className="text-center py-12">
              <Wallet className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-500 mb-4">Nenhuma conta conectada ainda</p>
              {onAddConnection && (
                <Button onClick={onAddConnection}>
                  <Plus className="w-4 h-4 mr-2" />
                  Conectar Primeira Conta
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              {/* Bank Accounts */}
              {bankAccounts.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-3">
                    Contas Bancárias ({bankAccounts.length})
                  </h3>
                  <div className={cn(
                    selectedView === 'cards' 
                      ? "grid grid-cols-1 md:grid-cols-2 gap-4" 
                      : "space-y-2"
                  )}>
                    {bankAccounts.map(account => (
                      selectedView === 'cards' ? (
                        <BankAccountCard
                          key={account.id}
                          account={account}
                          onSync={onSync}
                          onManageConnection={onManageConnection}
                          isSyncing={syncingAccountIds.includes(account.id)}
                        />
                      ) : (
                        <BankAccountCardCompact
                          key={account.id}
                          account={account}
                          onClick={() => onManageConnection?.(account.item?.id || '')}
                          isSyncing={syncingAccountIds.includes(account.id)}
                        />
                      )
                    ))}
                  </div>
                </div>
              )}

              {/* Credit Cards */}
              {creditAccounts.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-3">
                    Cartões de Crédito ({creditAccounts.length})
                  </h3>
                  <div className={cn(
                    selectedView === 'cards' 
                      ? "grid grid-cols-1 md:grid-cols-2 gap-4" 
                      : "space-y-2"
                  )}>
                    {creditAccounts.map(account => (
                      selectedView === 'cards' ? (
                        <BankAccountCard
                          key={account.id}
                          account={account}
                          onSync={onSync}
                          onManageConnection={onManageConnection}
                          isSyncing={syncingAccountIds.includes(account.id)}
                        />
                      ) : (
                        <BankAccountCardCompact
                          key={account.id}
                          account={account}
                          onClick={() => onManageConnection?.(account.item?.id || '')}
                          isSyncing={syncingAccountIds.includes(account.id)}
                        />
                      )
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}