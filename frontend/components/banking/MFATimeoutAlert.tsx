/**
 * MFA Timeout Alert Component
 * Shows a prominent warning when MFA is required with countdown timer
 */

import React from 'react';
import { AlertTriangle, Clock, Wifi } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { useMFATimeout } from '@/hooks/use-mfa-timeout';
import { usePluggyConnect } from '@/hooks/use-pluggy-connect';
import { cn } from '@/lib/utils';

interface MFATimeoutAlertProps {
  className?: string;
  onReconnect?: () => void;
}

export function MFATimeoutAlert({ className, onReconnect }: MFATimeoutAlertProps) {
  const { openConnect } = usePluggyConnect();
  
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
      // Use Pluggy Connect to update the item
      await openConnect({ item_id: itemId });
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

  return (
    <Alert 
      variant={getAlertVariant()} 
      className={cn(
        'border-l-4 animate-in slide-in-from-top-2 duration-300',
        isCritical && 'border-l-red-500 bg-red-50 dark:bg-red-950/10',
        isUrgent && !isCritical && 'border-l-orange-500 bg-orange-50 dark:bg-orange-950/10',
        !isUrgent && 'border-l-blue-500 bg-blue-50 dark:bg-blue-950/10',
        className
      )}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className={cn(
          'flex-shrink-0 p-1 rounded-full',
          isCritical && 'bg-red-100 dark:bg-red-900/20',
          isUrgent && !isCritical && 'bg-orange-100 dark:bg-orange-900/20',
          !isUrgent && 'bg-blue-100 dark:bg-blue-900/20'
        )}>
          {isCritical ? (
            <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400" />
          ) : (
            <Clock className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 space-y-3">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h4 className="font-semibold text-sm">
                  {isCritical ? 'MFA Critical - Action Required!' : 'MFA Authentication Required'}
                </h4>
                {institutionName && (
                  <Badge variant="outline" className="text-xs">
                    {institutionName}
                  </Badge>
                )}
              </div>
              
              <AlertDescription className="text-sm">
                {isCritical ? (
                  <>
                    <strong>Urgent:</strong> Your bank is waiting for the verification code. 
                    Time remaining: <strong>{formattedTime}</strong>
                  </>
                ) : isUrgent ? (
                  <>
                    Your bank requires a verification code (SMS/App). 
                    Please enter it within <strong>{formattedTime}</strong>
                  </>
                ) : (
                  <>
                    Authentication required. Please check your phone for the verification code.
                    Time remaining: <strong>{formattedTime}</strong>
                  </>
                )}
              </AlertDescription>
            </div>

            {/* Timer Display */}
            <div className="text-right">
              <div className={cn(
                'text-2xl font-mono font-bold',
                getTimerColor()
              )}>
                {formattedTime}
              </div>
              <div className="text-xs text-muted-foreground">
                remaining
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="space-y-2">
            <Progress 
              value={progress} 
              className={cn(
                'h-2 transition-all duration-300',
                isCritical && '[&>div]:bg-red-500',
                isUrgent && !isCritical && '[&>div]:bg-orange-500',
                !isUrgent && '[&>div]:bg-blue-500'
              )}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Authentication started</span>
              <span>{progress.toFixed(0)}% elapsed</span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 pt-1">
            <Button
              size="sm"
              variant={isCritical ? "destructive" : "default"}
              onClick={handleReconnect}
              className="flex items-center gap-2"
            >
              <Wifi className="h-3 w-3" />
              Reconnect Account
            </Button>
            
            <Button
              size="sm"
              variant="outline"
              onClick={() => mfaTimeout.stopMFATimeout()}
            >
              Cancel
            </Button>
          </div>

          {/* Help Text */}
          <div className="text-xs text-muted-foreground pt-2 border-t">
            💡 <strong>Tip:</strong> Check your phone for SMS or push notification from your bank. 
            If you don&apos;t receive the code, try reconnecting the account.
          </div>
        </div>
      </div>
    </Alert>
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