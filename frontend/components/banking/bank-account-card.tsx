'use client';

import { useState } from 'react';
import { RefreshCw, AlertCircle, Check, Clock, Wifi, WifiOff } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import type { BankAccount } from '@/types/banking.types';

interface BankAccountCardProps {
  account: BankAccount;
  onSync?: (accountId: string) => void;
  onManageConnection?: (connectionId: string) => void;
  isSyncing?: boolean;
}

export function BankAccountCard({
  account,
  onSync,
  onManageConnection,
  isSyncing = false,
}: BankAccountCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  // Determine sync status
  const getSyncStatus = () => {
    if (isSyncing) return 'syncing';
    
    const item = account.item;
    if (!item) return 'error';
    
    switch (item.status) {
      case 'UPDATED':
        return 'synced';
      case 'UPDATING':
      case 'LOGIN_IN_PROGRESS':
        return 'syncing';
      case 'LOGIN_ERROR':
      case 'ERROR':
        return 'error';
      case 'WAITING_USER_INPUT':
        return 'action_required';
      case 'OUTDATED':
        return 'outdated';
      default:
        return 'unknown';
    }
  };

  const syncStatus = getSyncStatus();

  // Status configurations
  const statusConfig = {
    synced: {
      icon: <Check className="w-4 h-4" />,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      label: 'Sincronizado',
    },
    syncing: {
      icon: <RefreshCw className="w-4 h-4 animate-spin" />,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      label: 'Sincronizando',
    },
    error: {
      icon: <WifiOff className="w-4 h-4" />,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      label: 'Erro de conexão',
    },
    action_required: {
      icon: <AlertCircle className="w-4 h-4" />,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      label: 'Ação necessária',
    },
    outdated: {
      icon: <Clock className="w-4 h-4" />,
      color: 'text-gray-600',
      bgColor: 'bg-gray-50',
      label: 'Desatualizado',
    },
    unknown: {
      icon: <Wifi className="w-4 h-4" />,
      color: 'text-gray-400',
      bgColor: 'bg-gray-50',
      label: 'Status desconhecido',
    },
  };

  const status = statusConfig[syncStatus];
  const needsAction = ['error', 'action_required'].includes(syncStatus);
  const canSync = ['synced', 'outdated', 'error'].includes(syncStatus) && !isSyncing;

  // Format last sync time
  const getLastSyncDisplay = () => {
    if (!account.last_sync_at) return null;
    
    const lastSync = new Date(account.last_sync_at);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - lastSync.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Agora mesmo';
    if (diffInMinutes < 60) return `${diffInMinutes}min atrás`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h atrás`;
    return `${Math.floor(diffInMinutes / 1440)}d atrás`;
  };

  const lastSyncDisplay = getLastSyncDisplay();

  return (
    <Card
      className={cn(
        "relative overflow-hidden transition-all duration-200 cursor-pointer",
        isHovered && "shadow-lg transform -translate-y-0.5",
        needsAction && "ring-2 ring-orange-200"
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onManageConnection?.(account.item?.id || '')}
    >
      <CardContent className="p-4">
        {/* Main Content */}
        <div className="space-y-3">
          {/* Header: Bank and Balance */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              {/* Bank Logo */}
              {account.item?.connector?.image_url ? (
                <img
                  src={account.item.connector.image_url}
                  alt={account.item.connector.name}
                  className="w-10 h-10 rounded-lg object-contain bg-white p-1 border shadow-sm"
                />
              ) : (
                <div 
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold shadow-sm"
                  style={{ backgroundColor: account.item?.connector?.primary_color || '#6366f1' }}
                >
                  {account.item?.connector?.name?.charAt(0) || 'B'}
                </div>
              )}
              
              {/* Account Info */}
              <div>
                <h3 className="font-medium text-gray-900">
                  {account.name || account.marketing_name || 'Conta'}
                </h3>
                <p className="text-sm text-gray-500">
                  {account.type === 'BANK' ? 'Conta corrente' : 
                   account.type === 'CREDIT' ? 'Cartão de crédito' : 
                   account.type}
                </p>
              </div>
            </div>

            {/* Balance */}
            <div className="text-right">
              <p className="text-2xl font-semibold text-gray-900">
                {new Intl.NumberFormat('pt-BR', {
                  style: 'currency',
                  currency: account.currency_code || 'BRL'
                }).format(account.balance)}
              </p>
              {account.type === 'CREDIT' && account.credit_data?.available_credit_limit && (
                <p className="text-xs text-gray-500 mt-1">
                  Limite: {new Intl.NumberFormat('pt-BR', {
                    style: 'currency',
                    currency: account.currency_code || 'BRL'
                  }).format(account.credit_data.available_credit_limit)}
                </p>
              )}
            </div>
          </div>

          {/* Footer: Status and Actions */}
          <div className="flex items-center justify-between pt-2 border-t">
            {/* Status Indicator */}
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className={cn(
                    "flex items-center gap-2 text-sm px-2 py-1 rounded-md",
                    status.bgColor
                  )}>
                    <span className={status.color}>{status.icon}</span>
                    {lastSyncDisplay && syncStatus === 'synced' && (
                      <span className="text-gray-600">{lastSyncDisplay}</span>
                    )}
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{status.label}</p>
                  {account.item?.error_message && (
                    <p className="text-xs mt-1">{account.item.error_message}</p>
                  )}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            {/* Quick Actions */}
            <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
              {canSync && onSync && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onSync(account.id)}
                  disabled={isSyncing}
                  className="h-8 px-3"
                >
                  <RefreshCw className={cn("w-4 h-4", isSyncing && "animate-spin")} />
                  <span className="ml-2 hidden sm:inline">Sincronizar</span>
                </Button>
              )}
              
              {needsAction && (
                <Button
                  size="sm"
                  variant="default"
                  onClick={() => onManageConnection?.(account.item?.id || '')}
                  className="h-8 px-3"
                >
                  {syncStatus === 'action_required' ? 'Resolver' : 'Reconectar'}
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Hover Effect - Subtle gradient */}
        <div className={cn(
          "absolute inset-0 bg-gradient-to-r from-transparent to-gray-50/50 opacity-0 transition-opacity duration-200",
          isHovered && "opacity-100"
        )} />
      </CardContent>
    </Card>
  );
}