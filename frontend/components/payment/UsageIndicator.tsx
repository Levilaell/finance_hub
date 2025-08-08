'use client';

import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertCircle, TrendingUp } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import { testId, TEST_IDS } from '@/utils/test-helpers';

interface UsageIndicatorProps {
  type: 'transaction' | 'bank_account' | 'ai_request';
  current: number;
  limit: number;
  percentage: number;
  showAlert?: boolean;
  compact?: boolean;
}

export function UsageIndicator({ 
  type, 
  current, 
  limit, 
  percentage, 
  showAlert = true,
  compact = false 
}: UsageIndicatorProps) {
  const router = useRouter();
  
  const labels = {
    transaction: 'Transactions',
    bank_account: 'Bank Accounts',
    ai_request: 'AI Requests',
  };

  const getProgressColor = (percent: number) => {
    if (percent >= 100) return 'bg-red-500';
    if (percent >= 80) return 'bg-yellow-500';
    return 'bg-primary';
  };

  const isNearLimit = percentage >= 80;
  const isAtLimit = percentage >= 100;

  if (compact) {
    return (
      <div className="space-y-1">
        <div className="flex items-center justify-between text-sm">
          <span>{labels[type]}</span>
          <span className={cn(
            'text-muted-foreground',
            isAtLimit && 'text-red-500 font-medium'
          )}>
            {current} / {limit}
          </span>
        </div>
        <Progress 
          value={Math.min(percentage, 100)} 
          className="h-2"
          indicatorClassName={getProgressColor(percentage)}
          {...testId(`usage-meter-${type}`)}
        />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-medium">{labels[type]}</h4>
          <span className={cn(
            'text-sm',
            isAtLimit && 'text-red-500 font-medium'
          )}>
            {current} / {limit} ({percentage}%)
          </span>
        </div>
        <Progress 
          value={Math.min(percentage, 100)} 
          indicatorClassName={getProgressColor(percentage)}
          {...testId(`usage-meter-${type}`)}
        />
      </div>

      {showAlert && isNearLimit && (
        <Alert variant={isAtLimit ? 'destructive' : 'default'}>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>
              {isAtLimit 
                ? `You've reached your ${labels[type].toLowerCase()} limit.`
                : `You're approaching your ${labels[type].toLowerCase()} limit.`
              }
            </span>
            <Button
              variant="link"
              size="sm"
              className="ml-2"
              onClick={() => router.push('/subscription/upgrade')}
              {...testId(TEST_IDS.company.upgradeFromLimitButton)}
            >
              <TrendingUp className="mr-1 h-3 w-3" />
              Upgrade
            </Button>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}