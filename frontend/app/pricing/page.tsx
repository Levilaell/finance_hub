'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

interface PricingPlan {
  id: string;
  name: string;
  slug: string;
  description: string;
  priceMonthly: number;
  priceYearly: number;
  features: string[];
  limitations: string[];
  highlighted?: boolean;
  badge?: string;
}

const plans: PricingPlan[] = [
  {
    id: 'free',
    name: 'Grátis',
    slug: 'free',
    description: 'Ideal para MEI e autônomos começando',
    priceMonthly: 0,
    priceYearly: 0,
    features: [
      '1 usuário',
      '1 conta bancária',
      '100 transações por mês',
      'Relatórios básicos',
      'Dashboard simples',
      'Suporte por email',
    ],
    limitations: [
      'Sem categorização por IA',
      'Sem relatórios avançados',
      'Sem API',
    ],
  },
  {
    id: 'starter',
    name: 'Starter',
    slug: 'starter',
    description: 'Para pequenos negócios em crescimento',
    priceMonthly: 49,
    priceYearly: 490,
    features: [
      '3 usuários',
      '2 contas bancárias',
      '500 transações por mês',
      'Relatórios completos',
      'Dashboard avançado',
      'Categorização manual',
      'Exportação PDF/Excel',
      'Suporte prioritário',
    ],
    limitations: [
      'Sem categorização por IA',
      'Sem API',
    ],
  },
  {
    id: 'professional',
    name: 'Profissional',
    slug: 'professional',
    description: 'Para empresas estabelecidas',
    priceMonthly: 149,
    priceYearly: 1490,
    highlighted: true,
    badge: 'Mais Popular',
    features: [
      '10 usuários',
      '5 contas bancárias',
      '2.000 transações por mês',
      'Categorização por IA',
      'Relatórios avançados',
      'Análise preditiva',
      'Integração completa Open Banking',
      'Notificações em tempo real',
      'Suporte prioritário 24/7',
      'Backup automático',
    ],
    limitations: [
      'Sem API',
      'Sem personalização',
    ],
  },
  {
    id: 'enterprise',
    name: 'Empresarial',
    slug: 'enterprise',
    description: 'Solução completa para grandes empresas',
    priceMonthly: 449,
    priceYearly: 4490,
    features: [
      'Usuários ilimitados',
      'Contas bancárias ilimitadas',
      'Transações ilimitadas',
      'Categorização por IA avançada',
      'API completa',
      'Relatórios personalizados',
      'Dashboard personalizado',
      'Integração com ERPs',
      'Suporte dedicado',
      'SLA garantido',
      'Treinamento incluído',
      'Consultoria financeira',
    ],
    limitations: [],
  },
];

export default function PricingPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isYearly, setIsYearly] = useState(false);
  const fromRegister = searchParams.get('from') === 'register';

  const handleSelectPlan = (planSlug: string) => {
    if (fromRegister) {
      // If coming from register, pass the selected plan
      router.push(`/register?plan=${planSlug}`);
    } else {
      // If already logged in, go to subscription page
      router.push(`/dashboard/subscription/upgrade?plan=${planSlug}`);
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 0,
    }).format(price);
  };

  const getDiscountPercentage = (monthly: number, yearly: number) => {
    if (monthly === 0) return 0;
    const yearlyMonthly = yearly / 12;
    return Math.round(((monthly - yearlyMonthly) / monthly) * 100);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Escolha o plano ideal para sua empresa
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Comece grátis e escale conforme cresce. Cancele quando quiser.
          </p>
          
          {/* Billing Toggle */}
          <div className="flex items-center justify-center gap-4">
            <Label htmlFor="billing-toggle" className={!isYearly ? 'font-semibold' : ''}>
              Mensal
            </Label>
            <Switch
              id="billing-toggle"
              checked={isYearly}
              onCheckedChange={setIsYearly}
            />
            <Label htmlFor="billing-toggle" className={isYearly ? 'font-semibold' : ''}>
              Anual
              <Badge variant="secondary" className="ml-2">
                Economize até 17%
              </Badge>
            </Label>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
          {plans.map((plan) => {
            const price = isYearly ? plan.priceYearly : plan.priceMonthly;
            const discount = getDiscountPercentage(plan.priceMonthly, plan.priceYearly);
            
            return (
              <Card
                key={plan.id}
                className={`relative ${
                  plan.highlighted
                    ? 'border-primary shadow-lg scale-105'
                    : 'border-gray-200'
                }`}
              >
                {plan.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge variant="default">{plan.badge}</Badge>
                  </div>
                )}
                
                <CardHeader>
                  <CardTitle className="text-2xl">{plan.name}</CardTitle>
                  <CardDescription>{plan.description}</CardDescription>
                </CardHeader>
                
                <CardContent>
                  <div className="mb-6">
                    <div className="flex items-baseline">
                      <span className="text-4xl font-bold">{formatPrice(price)}</span>
                      {price > 0 && (
                        <span className="text-gray-600 ml-2">
                          /{isYearly ? 'ano' : 'mês'}
                        </span>
                      )}
                    </div>
                    {isYearly && discount > 0 && (
                      <p className="text-sm text-green-600 mt-1">
                        Economia de {discount}% no plano anual
                      </p>
                    )}
                  </div>
                  
                  <div className="space-y-3">
                    <p className="font-semibold text-sm text-gray-700">Inclui:</p>
                    {plan.features.map((feature, index) => (
                      <div key={index} className="flex items-start gap-2">
                        <CheckIcon className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                        <span className="text-sm text-gray-700">{feature}</span>
                      </div>
                    ))}
                    
                    {plan.limitations.length > 0 && (
                      <>
                        <div className="pt-3 border-t border-gray-200" />
                        {plan.limitations.map((limitation, index) => (
                          <div key={index} className="flex items-start gap-2">
                            <XMarkIcon className="h-5 w-5 text-gray-400 flex-shrink-0 mt-0.5" />
                            <span className="text-sm text-gray-500">{limitation}</span>
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                </CardContent>
                
                <CardFooter>
                  <Button
                    className="w-full"
                    variant={plan.highlighted ? 'default' : 'outline'}
                    onClick={() => handleSelectPlan(plan.slug)}
                  >
                    {plan.priceMonthly === 0 ? 'Começar Grátis' : 'Escolher Plano'}
                  </Button>
                </CardFooter>
              </Card>
            );
          })}
        </div>

        {/* FAQ Section */}
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-8">
            Perguntas Frequentes
          </h2>
          
          <div className="space-y-6">
            <div>
              <h3 className="font-semibold text-lg mb-2">
                Posso mudar de plano depois?
              </h3>
              <p className="text-gray-600">
                Sim! Você pode fazer upgrade ou downgrade a qualquer momento. 
                As mudanças são aplicadas imediatamente e os valores são calculados proporcionalmente.
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold text-lg mb-2">
                Como funciona o período de teste?
              </h3>
              <p className="text-gray-600">
                Todos os planos pagos incluem 14 dias de teste grátis. 
                Não é necessário cartão de crédito para começar.
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold text-lg mb-2">
                Quais formas de pagamento são aceitas?
              </h3>
              <p className="text-gray-600">
                Aceitamos cartões de crédito (Visa, Mastercard, Elo, American Express), 
                PIX e boleto bancário através do MercadoPago e Stripe.
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold text-lg mb-2">
                O que acontece se eu exceder os limites do meu plano?
              </h3>
              <p className="text-gray-600">
                Você será notificado quando atingir 80% do limite. 
                Ao exceder, sugerimos fazer upgrade para continuar usando normalmente.
              </p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        {!fromRegister && (
          <div className="text-center mt-16">
            <p className="text-gray-600 mb-4">
              Ainda não tem uma conta?
            </p>
            <Button asChild size="lg">
              <Link href="/register">
                Criar Conta Gratuita
              </Link>
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}