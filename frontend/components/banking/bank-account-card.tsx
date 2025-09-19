'use client';

import Image from 'next/image';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

import {
  ArrowPathIcon,
  BuildingLibraryIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  CreditCardIcon,
  BanknotesIcon,
  ChartBarIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';

import { BankAccount, PluggyItemStatus } from '@/types/banking.types';
import { bankingService } from '@/services/banking.service';

interface BankAccountCardProps {
  account: BankAccount;
  isSyncing: boolean;
  onSync: (accountId: string) => void;
  onReconnect: (account: BankAccount) => void;
  onRemove: (account: BankAccount) => void;
}

export function BankAccountCard({
  account,
  isSyncing,
  onSync,
  onReconnect,
  onRemove,
}: BankAccountCardProps) {
  // Helpers
  const getAccountTypeLabel = (type: string) => {
    const types: Record<string, string> = {
      BANK: 'Conta Bancária',
      CREDIT: 'Cartão de Crédito',
      INVESTMENT: 'Investimento',
      LOAN: 'Empréstimo',
      OTHER: 'Outro',
    };
    return types[type] || types.OTHER;
  };

  const getStatusBadge = (status?: PluggyItemStatus) => {
    const statusMap: Record<string, { 
      label: string; 
      color: string;
    }> = {
      'LOGIN_ERROR': { 
        label: 'Erro de Login', 
        color: 'bg-red-100 text-red-800'
      },
      'ERROR': { 
        label: 'Erro', 
        color: 'bg-red-100 text-red-800'
      },
      'WAITING_USER_INPUT': { 
        label: 'Aguardando', 
        color: 'bg-yellow-100 text-yellow-800'
      },
      'OUTDATED': { 
        label: 'Desatualizado', 
        color: 'bg-yellow-100 text-yellow-800'
      },
      'UPDATING': { 
        label: 'Atualizando', 
        color: 'bg-blue-100 text-blue-800'
      },
      'LOGIN_IN_PROGRESS': { 
        label: 'Conectando', 
        color: 'bg-blue-100 text-blue-800'
      },
    };
    return statusMap[status || ''];
  };

  const formatLastSync = (date?: string) => {
    if (!date) return 'Nunca';
    
    try {
      const syncDate = new Date(date);
      return formatDistanceToNow(syncDate, { addSuffix: true, locale: ptBR });
    } catch {
      return 'Data inválida';
    }
  };

  const needsReconnection = bankingService.needsReconnection(account);
  const statusInfo = getStatusBadge(account.item_status);
  return (
    <Card className="hover:shadow-lg transition-all duration-300">
      <CardContent className="p-6 space-y-4">
        {/* Header Row: Bank Icon, Name, and Actions */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {/* Bank Icon */}
            {account.connector?.image_url ? (
              <Image
                src={account.connector.image_url}
                alt={account.connector.name}
                width={40}
                height={40}
                className="object-contain rounded"
              />
            ) : (
              <div className="w-10 h-10 bg-gray-100 rounded flex items-center justify-center">
                <BuildingLibraryIcon className="h-6 w-6 text-gray-400" />
              </div>
            )}
            
            {/* Bank Name and Account Number */}
            <div>
              <h3 className="font-semibold text-base">
                {account.connector?.name || 'Banco'}
              </h3>
              {account.masked_number && (
                <p className="text-sm text-muted-foreground mt-0.5">
                  {account.masked_number}
                </p>
              )}
            </div>
          </div>

          {/* Delete Button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onRemove(account)}
            className="h-8 w-8 text-red-600 hover:text-red-700"
          >
            <TrashIcon className="h-4 w-4" />
          </Button>
        </div>

        {/* Type and Status Row */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            {getAccountTypeLabel(account.type)}
          </span>
          {statusInfo && (
            <Badge 
              variant="secondary" 
              className={`${statusInfo.color}`}
            >
              {statusInfo.label}
            </Badge>
          )}
        </div>

        {/* Balance */}
        <div className="py-2">
          <p className="text-sm text-muted-foreground mb-1">Saldo</p>
          <p className="text-3xl font-bold">
            {bankingService.formatCurrency(account.balance)}
          </p>
        </div>

        {/* Last Update */}
        <div className="flex items-center justify-between pt-3 border-t">
          <p className="text-sm text-muted-foreground">
            Atualizado {formatLastSync(account.pluggy_updated_at)}
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onSync(account.id)}
            disabled={isSyncing || needsReconnection}
          >
            <ArrowPathIcon className={`h-4 w-4 mr-1.5 ${isSyncing ? 'animate-spin' : ''}`} />
            {isSyncing ? 'Sincronizando' : 'Sincronizar'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}