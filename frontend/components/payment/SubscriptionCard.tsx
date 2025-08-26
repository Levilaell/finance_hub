'use client';

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useSubscription } from '@/hooks/useSubscription';
import { useUsageLimits } from '@/hooks/useUsageLimits';
import { Calendar, CreditCard, TrendingUp, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { useRouter } from 'next/navigation';
import { testId, TEST_IDS } from '@/utils/test-helpers';

export function SubscriptionCard() {
  const router = useRouter();
  const { subscription, isLoading, isActive, isTrial, trialDaysRemaining } = useSubscription();
  const { usageLimits } = useUsageLimits();

  if (isLoading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!subscription) {
    return (
      <Card {...testId(TEST_IDS.company.subscriptionCard)}>
        <CardHeader>
          <CardTitle>No Active Subscription</CardTitle>
          <CardDescription>Start your free trial to access all features</CardDescription>
        </CardHeader>
        <CardFooter>
          <Button onClick={() => router.push('/subscription/upgrade')} {...testId(TEST_IDS.company.startTrialButton)}>
            Start Free Trial
          </Button>
        </CardFooter>
      </Card>
    );
  }
  const statusStyles = {
    trial: 'bg-info-subtle text-info-subtle border border-info-subtle',
    active: 'bg-success-subtle text-success-subtle border border-success-subtle',
    cancelled: 'bg-warning-subtle text-warning-subtle border border-warning-subtle',
    expired: 'bg-error-subtle text-error-subtle border border-error-subtle',
    suspended: 'bg-warning-subtle text-warning-subtle border border-warning-subtle',
  };

  return (
    <Card {...testId(TEST_IDS.company.subscriptionCard)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{subscription.plan?.name || 'No Plan'}</CardTitle>
          <Badge variant="outline" className={statusStyles[subscription.subscription_status as keyof typeof statusStyles]} {...testId(TEST_IDS.company.subscriptionStatusBadge)}>
            {subscription.subscription_status.charAt(0).toUpperCase() + subscription.subscription_status.slice(1)}
          </Badge>
        </div>
        <CardDescription>
          {subscription.plan ? 'Subscription Active' : 'No active subscription'}
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {isTrial && (
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            <AlertCircle className="h-4 w-4" />
            <span>{trialDaysRemaining} days remaining in trial</span>
          </div>
        )}

        <div className="space-y-2">
          {subscription.trial_ends_at && (
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center space-x-2">
                <Calendar className="h-4 w-4" />
                <span>Trial Ends</span>
              </span>
              <span className="text-muted-foreground">
                {format(new Date(subscription.trial_ends_at), 'MMM d, yyyy')}
              </span>
            </div>
          )}

          {subscription.plan && !isTrial && (
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center space-x-2">
                <CreditCard className="h-4 w-4" />
                <span>Plan Price</span>
              </span>
              <span className="text-muted-foreground">
                R$ {typeof subscription.plan.price_monthly === 'string' ? parseFloat(subscription.plan.price_monthly).toFixed(2) : (subscription.plan.price_monthly || 0).toFixed(2)}/month
              </span>
            </div>
          )}
        </div>

        {usageLimits && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium">Usage This Period</h4>
            
            {/* Transactions Usage */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span>Transactions</span>
                <span className="text-muted-foreground">
                  {usageLimits.transactions.used} / {usageLimits.transactions.limit}
                </span>
              </div>
              <Progress value={usageLimits.transactions.percentage} {...testId(TEST_IDS.company.transactionsUsageMeter)} />
            </div>

            {/* Bank Accounts Usage */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span>Bank Accounts</span>
                <span className="text-muted-foreground">
                  {usageLimits.bank_accounts.used} / {usageLimits.bank_accounts.limit}
                </span>
              </div>
              <Progress value={usageLimits.bank_accounts.percentage} {...testId(TEST_IDS.company.bankAccountsUsageMeter)} />
            </div>

            {/* AI Requests Usage */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span>AI Requests</span>
                <span className="text-muted-foreground">
                  {usageLimits.ai_requests.used} / {usageLimits.ai_requests.limit}
                </span>
              </div>
              <Progress value={usageLimits.ai_requests.percentage} {...testId(TEST_IDS.company.aiRequestsUsageMeter)} />
            </div>
          </div>
        )}
      </CardContent>

      <CardFooter className="flex justify-between">
        {isActive && subscription.plan?.name !== 'enterprise' && (
          <Button variant="outline" onClick={() => router.push('/subscription/upgrade')} {...testId(TEST_IDS.company.upgradePlanButton)}>
            <TrendingUp className="mr-2 h-4 w-4" />
            Upgrade Plan
          </Button>
        )}
        <Button variant="ghost" onClick={() => router.push('/subscription')} {...testId(TEST_IDS.company.manageSubscriptionButton)}>
          Manage Subscription
        </Button>
      </CardFooter>
    </Card>
  );
}