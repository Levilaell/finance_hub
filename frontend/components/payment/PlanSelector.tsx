'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Check, X } from 'lucide-react';
import { SubscriptionPlan } from '@/services/unified-subscription.service';
import { cn } from '@/lib/utils';
import { testId, TEST_IDS, testIdWithIndex } from '@/utils/test-helpers';

interface PlanSelectorProps {
  plans: SubscriptionPlan[];
  currentPlanId?: number;
  onSelectPlan: (plan: SubscriptionPlan, billingPeriod: 'monthly' | 'yearly') => void;
  loading?: boolean;
}

export function PlanSelector({ plans, currentPlanId, onSelectPlan, loading }: PlanSelectorProps) {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly');

  const planFeatures = {
    starter: [
      { name: 'Up to 1,000 transactions/month', included: true },
      { name: 'Connect 2 bank accounts', included: true },
      { name: '10 AI insights/month', included: true },
      { name: 'Basic reports', included: true },
      { name: 'Email support', included: true },
      { name: 'Advanced analytics', included: false },
      { name: 'Priority support', included: false },
      { name: 'API access', included: false },
    ],
    professional: [
      { name: 'Up to 10,000 transactions/month', included: true },
      { name: 'Connect 10 bank accounts', included: true },
      { name: '100 AI insights/month', included: true },
      { name: 'Advanced reports', included: true },
      { name: 'Priority email support', included: true },
      { name: 'Advanced analytics', included: true },
      { name: 'API access', included: true },
      { name: 'Dedicated account manager', included: false },
    ],
    enterprise: [
      { name: 'Unlimited transactions', included: true },
      { name: 'Unlimited bank accounts', included: true },
      { name: 'Unlimited AI insights', included: true },
      { name: 'Custom reports', included: true },
      { name: '24/7 phone & email support', included: true },
      { name: 'Advanced analytics', included: true },
      { name: 'Full API access', included: true },
      { name: 'Dedicated account manager', included: true },
    ],
  };

  const recommendedPlan = 'professional';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-center space-x-4">
        <Label htmlFor="billing-toggle" className="text-sm font-medium">
          Monthly
        </Label>
        <Switch
          id="billing-toggle"
          checked={billingPeriod === 'yearly'}
          onCheckedChange={(checked) => setBillingPeriod(checked ? 'yearly' : 'monthly')}
          {...testId(TEST_IDS.company.billingPeriodToggle)}
        />
        <Label htmlFor="billing-toggle" className="text-sm font-medium">
          Yearly
          <Badge variant="secondary" className="ml-2">
            Save up to 20%
          </Badge>
        </Label>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {plans.map((plan, index) => {
          const features = planFeatures[plan.name as keyof typeof planFeatures] || [];
          const price = billingPeriod === 'yearly' ? plan.price_yearly : plan.price_monthly;
          const monthlyEquivalent = billingPeriod === 'yearly' ? plan.price_yearly / 12 : plan.price_monthly;
          const isCurrentPlan = plan.id === currentPlanId;
          const isRecommended = plan.name === recommendedPlan;

          return (
            <Card
              key={plan.id}
              className={cn(
                'relative',
                isRecommended && 'border-primary shadow-lg'
              )}
              {...testIdWithIndex(TEST_IDS.company.subscriptionPlanCard, index)}
            >
              {isRecommended && (
                <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">
                  Recommended
                </Badge>
              )}
              
              <CardHeader>
                <CardTitle>{plan.name.charAt(0).toUpperCase() + plan.name.slice(1)}</CardTitle>
                <CardDescription>
                  {plan.name === 'starter' && 'Perfect for individuals'}
                  {plan.name === 'professional' && 'Great for growing businesses'}
                  {plan.name === 'enterprise' && 'For large organizations'}
                </CardDescription>
              </CardHeader>
              
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-baseline">
                    <span className="text-3xl font-bold">R$ {monthlyEquivalent.toFixed(2)}</span>
                    <span className="ml-1 text-muted-foreground">/month</span>
                  </div>
                  {billingPeriod === 'yearly' && (
                    <p className="text-sm text-muted-foreground">
                      R$ {price.toFixed(2)} billed annually
                    </p>
                  )}
                  {billingPeriod === 'yearly' && plan.yearly_discount && plan.yearly_discount > 0 && (
                    <Badge variant="secondary" className="mt-1">
                      Save {plan.yearly_discount}% annually
                    </Badge>
                  )}
                </div>

                <ul className="space-y-2">
                  {features.map((feature, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      {feature.included ? (
                        <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                      ) : (
                        <X className="h-5 w-5 text-gray-300 flex-shrink-0" />
                      )}
                      <span className={cn(
                        'text-sm',
                        !feature.included && 'text-muted-foreground'
                      )}>
                        {feature.name}
                      </span>
                    </li>
                  ))}
                </ul>
              </CardContent>
              
              <CardFooter>
                <Button
                  className="w-full"
                  variant={isRecommended ? 'default' : 'outline'}
                  disabled={isCurrentPlan || loading}
                  onClick={() => onSelectPlan(plan, billingPeriod)}
                  {...testIdWithIndex(TEST_IDS.company.selectPlanButton, index)}
                >
                  {isCurrentPlan ? 'Current Plan' : 'Select Plan'}
                </Button>
              </CardFooter>
            </Card>
          );
        })}
      </div>
    </div>
  );
}