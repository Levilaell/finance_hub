'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ArrowLeft, AlertCircle, Check } from 'lucide-react';
import { useSubscription } from '@/hooks/useSubscription';
import { subscriptionService, SubscriptionPlan } from '@/services/unified-subscription.service';
import { PlanSelector } from '@/components/payment/PlanSelector';

export default function UpgradePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { subscription, createCheckoutSession } = useSubscription();
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);

  // Get preselected plan from URL params
  useEffect(() => {
    const plan = searchParams.get('plan');
    if (plan) {
      setSelectedPlan(plan);
    }
  }, [searchParams]);

  // Fetch available plans
  const { data: plans, isLoading } = useQuery({
    queryKey: ['subscription-plans'],
    queryFn: subscriptionService.getSubscriptionPlans,
  });

  const handleSelectPlan = (plan: SubscriptionPlan, billingPeriod: 'monthly' | 'yearly') => {
    const successUrl = `${window.location.origin}/subscription/success?session_id={CHECKOUT_SESSION_ID}`;
    const cancelUrl = `${window.location.origin}/subscription/upgrade`;

    createCheckoutSession.mutate({
      plan_id: plan.id,
      billing_period: billingPeriod,
      success_url: successUrl,
      cancel_url: cancelUrl,
    });
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="animate-pulse space-y-8">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="grid gap-6 md:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-96 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const currentPlanId = subscription?.plan?.id;
  const isTrialActive = subscription?.subscription_status === 'trial';
  const trialDaysRemaining = subscription?.trial_days_left || 0;

  return (
    <div className="container mx-auto py-8 space-y-8">
      <div className="flex items-center space-x-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.back()}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Choose Your Plan</h1>
          <p className="text-muted-foreground">
            Select the plan that best fits your needs
          </p>
        </div>
      </div>

      {isTrialActive && trialDaysRemaining <= 7 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Your trial ends in {trialDaysRemaining} days. Choose a plan to continue using Finance Hub.
          </AlertDescription>
        </Alert>
      )}

      {plans && (
        <PlanSelector
          plans={plans}
          currentPlanId={currentPlanId}
          onSelectPlan={handleSelectPlan}
          loading={createCheckoutSession.isPending}
        />
      )}

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>All Plans Include</CardTitle>
          <CardDescription>
            Everything you need to manage your finances
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2">
            <div className="flex items-start space-x-3">
              <div className="rounded-full bg-primary/10 p-1">
                <Check className="h-4 w-4 text-primary" />
              </div>
              <div>
                <p className="font-medium">Bank Account Sync</p>
                <p className="text-sm text-muted-foreground">
                  Connect and sync your bank accounts automatically
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="rounded-full bg-primary/10 p-1">
                <Check className="h-4 w-4 text-primary" />
              </div>
              <div>
                <p className="font-medium">Transaction Categorization</p>
                <p className="text-sm text-muted-foreground">
                  Automatic and manual transaction categorization
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="rounded-full bg-primary/10 p-1">
                <Check className="h-4 w-4 text-primary" />
              </div>
              <div>
                <p className="font-medium">Financial Reports</p>
                <p className="text-sm text-muted-foreground">
                  Detailed insights into your spending and income
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="rounded-full bg-primary/10 p-1">
                <Check className="h-4 w-4 text-primary" />
              </div>
              <div>
                <p className="font-medium">AI-Powered Insights</p>
                <p className="text-sm text-muted-foreground">
                  Get intelligent recommendations and analysis
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="text-center space-y-4">
        <p className="text-sm text-muted-foreground">
          All plans come with a 14-day free trial. No credit card required to start.
        </p>
        <p className="text-sm text-muted-foreground">
          Questions? Contact us at{' '}
          <a href="mailto:support@financehub.com" className="text-primary hover:underline">
            support@financehub.com
          </a>
        </p>
      </div>
    </div>
  );
}