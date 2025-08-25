/**
 * MFA Timeout Alert Component
 * Shows a prominent warning when MFA is required with countdown timer
 */

import React from 'react';
import { AlertTriangle, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { CardContent } from '@/components/ui/card';
import { useMFATimeout } from '@/hooks/use-mfa-timeout';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import { 
  ResponsiveBannerContainer, 
  ResponsiveButtonGroup 
} from '@/components/ui/responsive-banner';

interface MFATimeoutAlertProps {
  className?: string;
  onReconnect?: () => void;
}

export function MFATimeoutAlert({ className, onReconnect }: MFATimeoutAlertProps) {
  const router = useRouter();
  
  const mfaTimeout = useMFATimeout({
    timeout: 60, // 60 seconds
    warningThreshold: 20, // Warning at 20s remaining
    onTimeout: (itemId) => {
      console.log(`MFA timeout for item ${itemId}`);
    },
    onWarning: (remainingTime) => {
      console.log(`MFA warning: ${remainingTime}s remaining`);
    }
  });

  const statusInfo = mfaTimeout.getStatusInfo();

  // Don't render if no active MFA timeout
  if (!statusInfo) {
    return null;
  }

  const {
    isUrgent,
    isCritical,
    formattedTime,
    institutionName,
    progress,
    itemId
  } = statusInfo;

  const handleReconnect = async () => {
    if (onReconnect) {
      onReconnect();
    } else if (itemId) {
      // Navigate to MFA input page
      router.push(`/accounts/mfa/${itemId}`);
    }
  };

  const getAlertVariant = () => {
    if (isCritical) return 'destructive';
    if (isUrgent) return 'default';
    return 'default';
  };

  const getTimerColor = () => {
    if (isCritical) return 'text-red-600 dark:text-red-400';
    if (isUrgent) return 'text-orange-600 dark:text-orange-400';
    return 'text-blue-600 dark:text-blue-400';
  };

  const getProgressColor = () => {
    if (isCritical) return 'bg-red-500';
    if (isUrgent) return 'bg-orange-500';
    return 'bg-blue-500';
  };

  const getBannerVariant = (): 'warning' | 'critical' => {
    return isCritical ? 'critical' : 'warning';
  };

  return (
    <ResponsiveBannerContainer 
      variant={getBannerVariant()} 
      className={cn(
        'border-l-4 animate-in slide-in-from-top-2 duration-300',
        isCritical && 'border-l-red-500',
        isUrgent && !isCritical && 'border-l-orange-500',
        !isUrgent && 'border-l-blue-500',
        className
      )}
    >
      <CardContent className="p-0">
        {/* Mobile: Compact header with essential info */}
        <div className={cn(
          'flex flex-col space-y-3',
          'sm:flex-row sm:items-center sm:space-y-0 sm:space-x-4'
        )}>
          {/* Icon + Title + Institution (Mobile: Horizontal, Desktop: Same) */}
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            <div className={cn(
              'flex-shrink-0 p-1 rounded-full',
              isCritical && 'bg-red-100 dark:bg-red-900/20',
              isUrgent && !isCritical && 'bg-orange-100 dark:bg-orange-900/20',
              !isUrgent && 'bg-blue-100 dark:bg-blue-900/20'
            )}>
              {isCritical ? (
                <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400" />
              ) : (
                <Clock className="h-4 w-4 text-orange-600 dark:text-orange-400" />
              )}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <h4 className="font-semibold text-sm truncate">
                  {isCritical ? 'MFA Crítico!' : 'Autenticação MFA'}
                </h4>
                {institutionName && (
                  <Badge variant="outline" className="text-xs px-1 py-0">
                    {institutionName}
                  </Badge>
                )}
              </div>
              
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                {isCritical ? 
                  `Código de verificação necessário. Tempo: ${formattedTime}` :
                  `Verifique seu telefone para o código. Tempo: ${formattedTime}`
                }
              </p>
            </div>
          </div>

          {/* Timer Display - Mobile: Inline, Desktop: Right side */}
          <div className={cn(
            'flex items-center justify-between',
            'sm:flex-col sm:text-right'
          )}>
            <div className={cn(
              // Mobile: Smaller timer, Desktop: Large
              'text-lg sm:text-2xl font-mono font-bold',
              isCritical ? 'text-red-600 dark:text-red-400' : 'text-orange-600 dark:text-orange-400'
            )}>
              {formattedTime}
            </div>
            <div className="text-xs text-muted-foreground sm:hidden">
              restante
            </div>
          </div>
        </div>

        {/* Progress Bar - Simplified for mobile */}
        <div className="mt-3 space-y-2">
          <Progress 
            value={progress} 
            className={cn(
              'h-1 sm:h-2 transition-all duration-300',
              isCritical && '[&>div]:bg-red-500',
              !isCritical && '[&>div]:bg-orange-500'
            )}
          />
          <div className="hidden sm:flex justify-between text-xs text-muted-foreground">
            <span>Autenticação iniciada</span>
            <span>{progress.toFixed(0)}% decorrido</span>
          </div>
        </div>

        {/* Actions - Responsive Button Group */}
        <div className="mt-3">
          <ResponsiveButtonGroup
            primary={{
              label: "Reconectar",
              onClick: handleReconnect,
              variant: isCritical ? 'destructive' : 'default'
            }}
            secondary={{
              label: "Cancelar",
              onClick: () => mfaTimeout.stopMFATimeout(),
              variant: "ghost"
            }}
          />
        </div>

        {/* Help Text - Hide on mobile for height optimization */}
        <div className="hidden sm:block text-xs text-muted-foreground mt-3 pt-2 border-t">
          💡 Verifique seu telefone para SMS ou notificação do banco.
        </div>
      </CardContent>
    </ResponsiveBannerContainer>
  );
}

// Hook-based version for easy integration
export function useMFATimeoutAlert() {
  const mfaTimeout = useMFATimeout();
  
  return {
    shouldShow: mfaTimeout.isActive,
    component: <MFATimeoutAlert />,
    ...mfaTimeout
  };
}