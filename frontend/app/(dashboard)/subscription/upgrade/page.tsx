'use client';

import { useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { subscriptionService } from '@/services/subscription.service';
import { paymentService } from '@/services/payment.service';
import { formatCurrency } from '@/utils/billing.utils';
import { SubscriptionPlan } from '@/types';
import { CheckIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';

export default function UpgradePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedPlan = searchParams.get('plan');
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
      if (response && typeof response === 'object' && Array.isArray(response.data)) {
        return response.data;
      }
      return [];
    },
  });

  // Set preselected plan when plans are loaded
  useQuery({
    queryKey: ['preselect-plan', preselectedPlan, plans],
    queryFn: () => {
      if (preselectedPlan && plans && plans.length > 0) {
        const plan = plans.find((p: SubscriptionPlan) => 
          p.name.toLowerCase() === preselectedPlan.toLowerCase()
        );
        if (plan) {
          setSelectedPlan(plan);
        }
      }
      return null;
    },
    enabled: !!preselectedPlan && !!plans && plans.length > 0,
  });

  // Create checkout session mutation
  const createCheckoutMutation = useMutation({
    mutationFn: (data: { plan_id: string; billing_cycle: string }) =>
      paymentService.createCheckoutSession(data),
    onSuccess: (data) => {
      if (data.redirect_url) {
        window.location.href = data.redirect_url;
      } else {
        toast.error('Erro ao criar sessão de pagamento');
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Erro ao processar pagamento');
    },
  });

  const handleSubscribe = () => {
    if (!selectedPlan) {
      toast.error('Selecione um plano');
      return;
    }

    createCheckoutMutation.mutate({
      plan_id: selectedPlan.id,
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

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <Button
          variant="ghost"
          onClick={() => router.push('/dashboard')}
          className="mb-4"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Voltar ao Dashboard
        </Button>
        
        <h1 className="text-3xl font-bold">Escolha seu Plano</h1>
        <p className="text-gray-600 mt-2">
          Selecione o plano ideal para suas necessidades e comece a gerenciar suas finanças de forma inteligente.
        </p>
      </div>

      {plansLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner />
        </div>
      ) : (
        <div className="space-y-8">
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {plans?.map((plan: SubscriptionPlan) => {
              const isSelected = selectedPlan?.id === plan.id;
              const discount = billingCycle === 'yearly' ? getDiscount(plan) : 0;

              return (
                <Card
                  key={plan.id}
                  className={`relative cursor-pointer transition-all ${
                    isSelected
                      ? 'ring-2 ring-blue-500 shadow-lg'
                      : 'hover:shadow-md'
                  }`}
                  onClick={() => setSelectedPlan(plan)}
                >
                  {plan.name === 'Professional' && (
                    <Badge className="absolute -top-2 -right-2 bg-blue-500">
                      Mais Popular
                    </Badge>
                  )}
                  
                  <CardContent className="p-6">
                    <div className="text-center space-y-4">
                      <h3 className="text-xl font-semibold">{plan.name}</h3>
                      
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

                      <div className="space-y-3 text-left">
                        <div className="flex items-center text-sm">
                          <CheckIcon className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                          <span>{plan.max_transactions === -1 ? 'Transações ilimitadas' : `${plan.max_transactions} transações/mês`}</span>
                        </div>
                        <div className="flex items-center text-sm">
                          <CheckIcon className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                          <span>{plan.max_bank_accounts === -1 ? 'Contas bancárias ilimitadas' : `${plan.max_bank_accounts} contas bancárias`}</span>
                        </div>
                        <div className="flex items-center text-sm">
                          <CheckIcon className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                          <span>{plan.max_users === -1 ? 'Usuários ilimitados' : `${plan.max_users} usuários`}</span>
                        </div>
                        
                        {plan.has_ai_categorization && (
                          <div className="flex items-center text-sm">
                            <CheckIcon className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                            <span>Categorização com IA</span>
                          </div>
                        )}
                        
                        {plan.has_advanced_reports && (
                          <div className="flex items-center text-sm">
                            <CheckIcon className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                            <span>Relatórios avançados</span>
                          </div>
                        )}
                        
                        {plan.has_api_access && (
                          <div className="flex items-center text-sm">
                            <CheckIcon className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                            <span>Acesso à API</span>
                          </div>
                        )}
                        
                        {plan.has_accountant_access && (
                          <div className="flex items-center text-sm">
                            <CheckIcon className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                            <span>Acesso para contador</span>
                          </div>
                        )}
                      </div>

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
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Selected Plan Summary */}
          {selectedPlan && (
            <div className="bg-blue-50 border border-blue-200 p-6 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-3 text-lg">Resumo da Assinatura</h4>
              <div className="text-sm text-blue-800 space-y-2">
                <p>Plano selecionado: <strong>{selectedPlan.name}</strong></p>
                <p>Valor: <strong>{formatCurrency(getPrice(selectedPlan))}/{billingCycle === 'yearly' ? 'ano' : 'mês'}</strong></p>
                {billingCycle === 'yearly' && (
                  <p className="text-green-700">
                    Você economizará <strong>{formatCurrency(selectedPlan.price_monthly * 12 - selectedPlan.price_yearly)}</strong> por ano!
                  </p>
                )}
              </div>
              
              <div className="mt-6 flex justify-center">
                <Button
                  size="lg"
                  onClick={handleSubscribe}
                  disabled={createCheckoutMutation.isPending}
                  className="min-w-[200px]"
                >
                  {createCheckoutMutation.isPending ? (
                    <LoadingSpinner />
                  ) : (
                    'Assinar Agora'
                  )}
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}