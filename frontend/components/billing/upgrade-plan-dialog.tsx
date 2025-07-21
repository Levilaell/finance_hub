'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { subscriptionService } from '@/services/subscription.service';
import { paymentService } from '@/services/payment.service';
import { formatCurrency } from '@/utils/billing.utils';
import { SubscriptionPlan } from '@/types';
import { CheckIcon } from '@heroicons/react/24/outline';

interface UpgradePlanDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentPlan?: SubscriptionPlan;
}

export function UpgradePlanDialog({
  open,
  onOpenChange,
  currentPlan
}: UpgradePlanDialogProps) {
  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlan | null>(null);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  // Fetch available plans
  const { data: plans, isLoading: plansLoading } = useQuery({
    queryKey: ['available-plans'],
    queryFn: async () => {
      const response = await subscriptionService.getAvailablePlans();
      // Ensure we always return an array
      if (Array.isArray(response)) {
        return response;
      }
      // If response is an object with data property, return the data
      if (response && typeof response === 'object' && 'data' in response && Array.isArray((response as any).data)) {
        return (response as any).data;
      }
      return [];
    },
    enabled: open,
  });

  // Create checkout session mutation
  const checkoutMutation = useMutation({
    mutationFn: (data: { plan_slug: string; billing_cycle: 'monthly' | 'yearly' }) =>
      paymentService.createCheckoutSession(data),
    onSuccess: (response) => {
      // Redirect to Stripe checkout
      if (response.checkout_url) {
        window.location.href = response.checkout_url;
      } else {
        toast.error('Erro ao criar sessão de pagamento');
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Erro ao processar pagamento');
    },
  });

  const handleUpgrade = () => {
    if (!selectedPlan) {
      toast.error('Selecione um plano');
      return;
    }

    // Create checkout session with Stripe
    checkoutMutation.mutate({
      plan_slug: selectedPlan.slug,
      billing_cycle: billingCycle,
    });
  };

  const getPrice = (plan: SubscriptionPlan) => {
    return billingCycle === 'yearly' ? plan.price_yearly : plan.price_monthly;
  };

  const getDiscount = (plan: SubscriptionPlan) => {
    const monthlyTotal = plan.price_monthly * 12;
    const yearlyPrice = plan.price_yearly;
    return Math.round(((monthlyTotal - yearlyPrice) / monthlyTotal) * 100);
  };

  const isPlanUpgrade = (plan: SubscriptionPlan) => {
    if (!currentPlan) return true;
    return plan.price_monthly > currentPlan.price_monthly;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Fazer Upgrade do Plano</DialogTitle>
          <DialogDescription>
            Escolha o plano ideal para suas necessidades e desbloqueie mais recursos.
          </DialogDescription>
        </DialogHeader>

        {plansLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Billing Cycle Toggle */}
            <div className="flex items-center justify-center space-x-4">
              <Button
                variant={billingCycle === 'monthly' ? 'default' : 'outline'}
                onClick={() => setBillingCycle('monthly')}
                size="sm"
              >
                Mensal
              </Button>
              <Button
                variant={billingCycle === 'yearly' ? 'default' : 'outline'}
                onClick={() => setBillingCycle('yearly')}
                size="sm"
              >
                Anual
                <Badge variant="secondary" className="ml-2">
                  Economize até 20%
                </Badge>
              </Button>
            </div>

            {/* Plans Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {plans?.map((plan: SubscriptionPlan) => {
                const isCurrentPlan = currentPlan?.id === plan.id;
                const isUpgrade = isPlanUpgrade(plan);
                const isSelected = selectedPlan?.id === plan.id;
                const discount = billingCycle === 'yearly' ? getDiscount(plan) : 0;

                if (!isUpgrade && !isCurrentPlan) return null;

                return (
                  <Card
                    key={plan.id}
                    className={`relative cursor-pointer transition-all ${
                      isSelected
                        ? 'ring-2 ring-blue-500 shadow-lg'
                        : isCurrentPlan
                        ? 'ring-2 ring-gray-300'
                        : 'hover:shadow-md'
                    }`}
                    onClick={() => !isCurrentPlan && setSelectedPlan(plan)}
                  >
                    {isCurrentPlan && (
                      <Badge className="absolute -top-2 -right-2">
                        Plano Atual
                      </Badge>
                    )}
                    
                    <CardContent className="p-6">
                      <div className="text-center space-y-4">
                        <h3 className="text-lg font-semibold">{plan.name}</h3>
                        
                        <div>
                          <div className="text-3xl font-bold text-blue-600">
                            {formatCurrency(getPrice(plan))}
                          </div>
                          <div className="text-sm text-gray-600">
                            por {billingCycle === 'yearly' ? 'ano' : 'mês'}
                          </div>
                          {billingCycle === 'yearly' && discount > 0 && (
                            <div className="text-sm text-green-600 font-medium">
                              {discount}% de desconto
                            </div>
                          )}
                        </div>

                        <div className="space-y-2 text-left">
                          <div className="flex items-center text-sm">
                            <CheckIcon className="h-4 w-4 text-green-500 mr-2" />
                            {plan.max_transactions} transações/mês
                          </div>
                          <div className="flex items-center text-sm">
                            <CheckIcon className="h-4 w-4 text-green-500 mr-2" />
                            {plan.max_bank_accounts} contas bancárias
                          </div>
                          
                          {plan.has_ai_categorization && (
                            <div className="flex items-center text-sm">
                              <CheckIcon className="h-4 w-4 text-green-500 mr-2" />
                              Categorização com IA
                            </div>
                          )}
                          
                          {plan.has_advanced_reports && (
                            <div className="flex items-center text-sm">
                              <CheckIcon className="h-4 w-4 text-green-500 mr-2" />
                              Relatórios avançados
                            </div>
                          )}
                          
                          {plan.has_api_access && (
                            <div className="flex items-center text-sm">
                              <CheckIcon className="h-4 w-4 text-green-500 mr-2" />
                              Acesso à API
                            </div>
                          )}
                          
                          {plan.has_accountant_access && (
                            <div className="flex items-center text-sm">
                              <CheckIcon className="h-4 w-4 text-green-500 mr-2" />
                              Acesso para contador
                            </div>
                          )}
                        </div>

                        {!isCurrentPlan && (
                          <Button
                            className="w-full"
                            variant={isSelected ? 'default' : 'outline'}
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedPlan(plan);
                            }}
                          >
                            {isSelected ? 'Selecionado' : 'Selecionar'}
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* Selected Plan Summary */}
            {selectedPlan && (
              <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">Resumo do Upgrade</h4>
                <div className="text-sm text-blue-800">
                  <p>Plano selecionado: <strong>{selectedPlan.name}</strong></p>
                  <p>Valor: <strong>{formatCurrency(getPrice(selectedPlan))}/{billingCycle === 'yearly' ? 'ano' : 'mês'}</strong></p>
                  {billingCycle === 'yearly' && (
                    <p className="text-green-700">
                      Você economizará <strong>{formatCurrency(selectedPlan.price_monthly * 12 - selectedPlan.price_yearly)}</strong> por ano!
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={checkoutMutation.isPending}
          >
            Cancelar
          </Button>
          <Button
            onClick={handleUpgrade}
            disabled={!selectedPlan || checkoutMutation.isPending}
          >
            {checkoutMutation.isPending ? (
              <LoadingSpinner />
            ) : (
              'Continuar para Pagamento'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}