'use client';

import { RefreshCw, AlertCircle, Check, WifiOff } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { BankAccount } from '@/types/banking.types';

interface BankAccountCardCompactProps {
  account: BankAccount;
  onClick?: () => void;
  isSyncing?: boolean;
  showBalance?: boolean;
}

export function BankAccountCardCompact({
  account,
  onClick,
  isSyncing = false,
  showBalance = true,
}: BankAccountCardCompactProps) {
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
      default:
        return 'synced';
    }
  };

  const syncStatus = getSyncStatus();

  // Status icon
  const getStatusIcon = () => {
    switch (syncStatus) {
      case 'synced':
        return <Check className="w-3 h-3 text-green-600" />;
      case 'syncing':
        return <RefreshCw className="w-3 h-3 text-blue-600 animate-spin" />;
      case 'error':
        return <WifiOff className="w-3 h-3 text-red-600" />;
      case 'action_required':
        return <AlertCircle className="w-3 h-3 text-orange-600" />;
      default:
        return null;
    }
  };

  const needsAttention = ['error', 'action_required'].includes(syncStatus);

  return (
    <div
      className={cn(
        "flex items-center justify-between p-3 rounded-lg border bg-card transition-colors cursor-pointer hover:bg-gray-50",
        needsAttention && "border-orange-200 bg-orange-50/50"
      )}
      onClick={onClick}
    >
      {/* Left side: Bank info */}
      <div className="flex items-center gap-3 min-w-0">
        {/* Bank Logo */}
        {account.item?.connector?.image_url ? (
          <img
            src={account.item.connector.image_url}
            alt={account.item.connector.name}
            className="w-8 h-8 rounded object-contain bg-white p-0.5 border flex-shrink-0"
          />
        ) : (
          <div 
            className="w-8 h-8 rounded flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
            style={{ backgroundColor: account.item?.connector?.primary_color || '#6366f1' }}
          >
            {account.item?.connector?.name?.charAt(0) || 'B'}
          </div>
        )}
        
        {/* Account Info */}
        <div className="min-w-0">
          <p className="font-medium text-sm truncate">
            {account.name || account.marketing_name || 'Conta'}
          </p>
          <p className="text-xs text-muted-foreground">
            {account.item?.connector?.name || 'Banco'} • {account.type === 'BANK' ? 'Conta' : 'Cartão'}
          </p>
        </div>
      </div>

      {/* Right side: Balance and status */}
      <div className="flex items-center gap-3">
        {showBalance && (
          <p className={cn(
            "font-semibold text-right",
            account.balance < 0 ? "text-red-600" : "text-gray-900"
          )}>
            {new Intl.NumberFormat('pt-BR', {
              style: 'currency',
              currency: account.currency_code || 'BRL',
              minimumFractionDigits: 0,
              maximumFractionDigits: 0,
            }).format(account.balance)}
          </p>
        )}
        
        <div className="flex-shrink-0">
          {getStatusIcon()}
        </div>
      </div>
    </div>
  );
}