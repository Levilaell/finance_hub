'use client';

import { BankAccount } from '@/types/banking';
import { bankingService } from '@/services/banking.service';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  ArrowPathIcon,
  BuildingLibraryIcon,
  TrashIcon,
  EyeIcon,
  ExclamationTriangleIcon,
  LinkIcon,
} from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface BankAccountCardProps {
  account: BankAccount;
  connectionStatus?: string;  // Status from BankConnection (LOGIN_ERROR, UPDATED, etc)
  onSync?: () => void;
  onReconnect?: () => void;
  onView?: () => void;
  onDelete?: () => void;
}

export function BankAccountCard({ account, connectionStatus, onSync, onReconnect, onView, onDelete }: BankAccountCardProps) {
  const getAccountTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      CHECKING: 'Conta Corrente',
      SAVINGS: 'Poupança',
      CREDIT_CARD: 'Cartão de Crédito',
      LOAN: 'Empréstimo',
      INVESTMENT: 'Investimento',
    };
    return labels[type] || type;
  };

  const getAccountTypeBadgeClass = (type: string) => {
    const classes: Record<string, string> = {
      CHECKING: 'bg-blue-100 text-blue-800',
      SAVINGS: 'bg-green-100 text-green-800',
      CREDIT_CARD: 'bg-purple-100 text-purple-800',
      LOAN: 'bg-orange-100 text-orange-800',
      INVESTMENT: 'bg-indigo-100 text-indigo-800',
    };
    return classes[type] || 'bg-gray-100 text-gray-800';
  };
  return (
    <Card className="hover:shadow-lg transition-all duration-300">
      <CardContent className="p-6 space-y-4">
        {/* Header Row: Bank Icon, Name, and Actions */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {/* Bank Icon */}
            <div className="w-10 h-10 bg-gray-100 rounded flex items-center justify-center">
              <BuildingLibraryIcon className="h-6 w-6 text-gray-400" />
            </div>

            {/* Bank Name and Account Number */}
            <div>
              <h3 className="font-semibold text-base">
                {account.name}
              </h3>
              <p className="text-sm text-muted-foreground mt-0.5">
                {account.institution_name}
                {account.number && ` • ****${account.number.slice(-4)}`}
              </p>
            </div>
          </div>

          {/* Delete Button */}
          {onDelete && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-red-600 hover:text-red-700"
              onClick={onDelete}
            >
              <TrashIcon className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Type and Status Row */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            {getAccountTypeLabel(account.type)}
          </span>
          <Badge
            variant="secondary"
            className={getAccountTypeBadgeClass(account.type)}
          >
            {account.is_active ? 'Conectado' : 'Desconectado'}
          </Badge>
        </div>

        {/* Balance or Credit Limit */}
        <div className="py-2">
          {account.is_credit_card || account.type === 'CREDIT_CARD' ? (
            <>
              <p className="text-sm text-muted-foreground mb-1">Limite Disponível</p>
              <p className="text-3xl font-bold">
                {bankingService.formatCurrency(account.available_credit_limit || 0, account.currency_code)}
              </p>
              {account.credit_limit && (
                <p className="text-xs text-muted-foreground mt-1">
                  Limite total: {bankingService.formatCurrency(account.credit_limit, account.currency_code)}
                </p>
              )}
            </>
          ) : (
            <>
              <p className="text-sm text-muted-foreground mb-1">Saldo Disponível</p>
              <p className="text-3xl font-bold">
                {bankingService.formatCurrency(account.balance, account.currency_code)}
              </p>
            </>
          )}
        </div>

        {/* Connection Error Warning */}
        {(connectionStatus === 'LOGIN_ERROR' || connectionStatus === 'ERROR') && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-2">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-900">
                  Credenciais expiradas
                </p>
                <p className="text-xs text-red-700 mt-1">
                  Reconecte sua conta para continuar sincronizando
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Last Update and Actions */}
        <div className="pt-3 border-t space-y-3">
          <p className="text-sm text-muted-foreground">
            {account.last_synced_at
              ? `Atualizado ${formatDistanceToNow(new Date(account.last_synced_at), {
                  addSuffix: true,
                  locale: ptBR,
                })}`
              : 'Nunca sincronizada'}
          </p>

          <div className="flex gap-2">
            {(connectionStatus === 'LOGIN_ERROR' || connectionStatus === 'ERROR') ? (
              onReconnect && (
                <Button
                  variant="default"
                  size="sm"
                  onClick={onReconnect}
                  className="flex-1 bg-red-600 hover:bg-red-700"
                >
                  <LinkIcon className="h-4 w-4 mr-1.5" />
                  Reconectar
                </Button>
              )
            ) : (
              <>
                {onSync && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={onSync}
                    className="flex-1"
                  >
                    <ArrowPathIcon className="h-4 w-4 mr-1.5" />
                    Sincronizar
                  </Button>
                )}
                {onView && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={onView}
                    className="flex-1"
                  >
                    <EyeIcon className="h-4 w-4 mr-1.5" />
                    Transações
                  </Button>
                )}
              </>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}