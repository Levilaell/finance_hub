'use client';

import { RefreshCw, CheckCircle, AlertCircle, WifiOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

interface SyncStatusIndicatorProps {
  totalAccounts: number;
  syncedAccounts: number;
  errorAccounts: number;
  syncingAccounts: number;
  lastSyncTime?: Date | null;
  onSyncAll?: () => void;
  isSyncingAll?: boolean;
}

export function SyncStatusIndicator({
  totalAccounts,
  syncedAccounts,
  errorAccounts,
  syncingAccounts,
  lastSyncTime,
  onSyncAll,
  isSyncingAll = false,
}: SyncStatusIndicatorProps) {
  // Calculate status
  const allSynced = syncedAccounts === totalAccounts && errorAccounts === 0;
  const hasErrors = errorAccounts > 0;
  const isSyncing = syncingAccounts > 0 || isSyncingAll;

  // Get status icon and color
  const getStatusDisplay = () => {
    if (isSyncing) {
      return {
        icon: <RefreshCw className="w-4 h-4 animate-spin" />,
        color: 'text-blue-600',
        bgColor: 'bg-blue-50',
        label: `Sincronizando ${syncingAccounts} conta${syncingAccounts !== 1 ? 's' : ''}...`,
      };
    }
    
    if (hasErrors) {
      return {
        icon: <AlertCircle className="w-4 h-4" />,
        color: 'text-orange-600',
        bgColor: 'bg-orange-50',
        label: `${errorAccounts} conta${errorAccounts !== 1 ? 's' : ''} com erro`,
      };
    }
    
    if (allSynced) {
      return {
        icon: <CheckCircle className="w-4 h-4" />,
        color: 'text-green-600',
        bgColor: 'bg-green-50',
        label: 'Todas as contas sincronizadas',
      };
    }
    
    return {
      icon: <WifiOff className="w-4 h-4" />,
      color: 'text-gray-500',
      bgColor: 'bg-gray-50',
      label: `${syncedAccounts}/${totalAccounts} contas sincronizadas`,
    };
  };

  const status = getStatusDisplay();

  // Format last sync time
  const getLastSyncDisplay = () => {
    if (!lastSyncTime) return 'Nunca sincronizado';
    
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - lastSyncTime.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Sincronizado agora';
    if (diffInMinutes < 60) return `Última sync há ${diffInMinutes}min`;
    if (diffInMinutes < 1440) return `Última sync há ${Math.floor(diffInMinutes / 60)}h`;
    return `Última sync há ${Math.floor(diffInMinutes / 1440)}d`;
  };

  return (
    <TooltipProvider>
      <div className="flex items-center gap-3">
        {/* Status Badge */}
        <Tooltip>
          <TooltipTrigger asChild>
            <div className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium",
              status.bgColor,
              status.color
            )}>
              {status.icon}
              <span className="hidden sm:inline">{status.label}</span>
              <span className="sm:hidden">{syncedAccounts}/{totalAccounts}</span>
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <div className="space-y-1">
              <p className="font-medium">{status.label}</p>
              <p className="text-xs text-muted-foreground">{getLastSyncDisplay()}</p>
              {hasErrors && (
                <p className="text-xs text-orange-600">
                  Clique em "Sincronizar tudo" para tentar novamente
                </p>
              )}
            </div>
          </TooltipContent>
        </Tooltip>

        {/* Sync All Button */}
        {onSyncAll && totalAccounts > 0 && (
          <Button
            size="sm"
            variant={hasErrors ? "default" : "ghost"}
            onClick={onSyncAll}
            disabled={isSyncingAll}
            className="h-8"
          >
            <RefreshCw className={cn("w-4 h-4", isSyncingAll && "animate-spin")} />
            <span className="ml-2 hidden lg:inline">Sincronizar tudo</span>
          </Button>
        )}
      </div>
    </TooltipProvider>
  );
}