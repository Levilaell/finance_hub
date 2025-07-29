'use client';

import { useState, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckIcon, XMarkIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { formatCurrency } from '@/lib/utils';

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
    id: 'starter',
    name: 'Starter',
    slug: 'starter',
    description: 'Desenvolvido para empresas em crescimento que precisam de mais controle financeiro',
    priceMonthly: 49,
    priceYearly: 490,
    features: [
      '🏦 1 conta bancária conectada',
      '📊 500 transações por mês',
      '🤖 Categorização automática',
      '📊 Dashboard completo com gráficos',
      '📝 Relatórios financeiros avançados',
      '💾 Exportação PDF e Excel',
      '🔄 Sincronização em tempo real',
      '📞 Suporte por email',
    ],
    limitations: [
      'Sem análises por IA',
      'Sem insights preditivos',
    ],
  },
  {
    id: 'professional',
    name: 'Profissional',
    slug: 'professional',
    description: 'A solução completa com inteligência artificial para empresas que buscam automação e insights',
    priceMonthly: 149,
    priceYearly: 1490,
    highlighted: true,
    badge: 'Mais Popular',
    features: [
      '🏦 3 contas bancárias conectadas',
      '📊 2.500 transações por mês',
      '🤖 Categorização automática',
      '✨ Análises inteligentes com IA',
      '✨ 10 consultas de IA por mês',
      '✨ Insights e recomendações personalizadas',
      '✨ Previsões de fluxo de caixa',
      '✨ Detecção de anomalias',
      '✨ Otimização de despesas',
      '📝 Relatórios financeiros avançados',
      '📞 Suporte prioritário por WhatsApp',
    ],
    limitations: [
      'Limite de 10 consultas de IA por mês',
      'Limite de 2.500 transações por mês',
      'Limite de 3 contas bancárias conectadas'
    ],
  },
  {
    id: 'enterprise',
    name: 'Empresarial',
    slug: 'enterprise',
    description: 'Solução ilimitada para grandes empresas com necessidades complexas',
    priceMonthly: 349,
    priceYearly: 3490,
    features: [
      '🏦 Contas bancárias ilimitadas',
      '📊 Transações ilimitadas',
      '🤖 Categorização automática',
      '✨ IA sem restrições (consultas ilimitadas)',
      '✨ Análises avançadas ilimitadas',
      '✨ Machine Learning personalizado',
      '✨ Insights preditivos avançados',
      '📝 Relatórios financeiros avançados',
      '🎆 Suporte dedicado',
    ],
    limitations: [],
  },
];

function PricingContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isYearly, setIsYearly] = useState(true); // Default para anual (mais vantajoso)
  const fromRegister = searchParams.get('from') === 'register';

  const handleSelectPlan = (planSlug: string) => {
    // Always redirect to register page with the selected plan
    router.push(`/register?plan=${planSlug}`);
  };

  const formatPrice = (price: number) => {
    // Use shared formatCurrency with minimumFractionDigits: 0
    const formatted = formatCurrency(price);
    // Remove decimal places if they are .00
    return formatted.replace(/,00$/, '');
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
          <p className="text-xl text-gray-600 mb-2">
            Sistema financeiro que funciona sozinho com IA
          </p>
          <p className="text-lg text-gray-500 mb-8">
            <span className="text-green-600 font-semibold">14 dias grátis</span> em todos os planos • Cancele quando quiser
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
              <Badge variant="secondary" className="ml-2 bg-green-100 text-green-700">
                Economize até 17%
              </Badge>
            </Label>
          </div>
        </div>

        {/* Value Props */}
        <div className="flex flex-wrap justify-center gap-4 mb-12">
          <Badge variant="outline" className="px-4 py-2">
            ✅ Categorização automática via Open Banking
          </Badge>
          <Badge variant="outline" className="px-4 py-2">
            🤖 IA que aprende seu negócio
          </Badge>
          <Badge variant="outline" className="px-4 py-2">
            📊 Relatórios prontos em segundos
          </Badge>
          <Badge variant="outline" className="px-4 py-2">
            🎯 14 dias para testar grátis
          </Badge>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16 max-w-6xl mx-auto">
          {plans.map((plan) => {
            const price = isYearly ? plan.priceYearly : plan.priceMonthly;
            const monthlyPrice = isYearly ? plan.priceYearly / 12 : plan.priceMonthly;
            const discount = getDiscountPercentage(plan.priceMonthly, plan.priceYearly);
            
            return (
              <Card
                key={plan.id}
                className={`relative flex flex-col ${
                  plan.highlighted
                    ? 'border-primary shadow-xl scale-105 z-10'
                    : 'border-gray-200'
                }`}
              >
                {plan.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge className="bg-primary text-white px-4">
                      {plan.badge}
                    </Badge>
                  </div>
                )}
                
                <CardHeader className="pb-8">
                  <CardTitle className="text-2xl">{plan.name}</CardTitle>
                  <CardDescription className="mt-2">{plan.description}</CardDescription>
                </CardHeader>
                
                <CardContent className="flex-1">
                  <div className="mb-6">
                    <div className="flex items-baseline">
                      <span className="text-4xl font-bold">
                        {formatPrice(monthlyPrice)}
                      </span>
                      <span className="text-gray-600 ml-2">/mês</span>
                    </div>
                    {isYearly && (
                      <div className="mt-2">
                        <p className="text-sm text-gray-500">
                          Cobrado anualmente: {formatPrice(price)}
                        </p>
                        {discount > 0 && (
                          <p className="text-sm text-green-600 font-medium">
                            Economia de {discount}% no plano anual
                          </p>
                        )}
                      </div>
                    )}
                    <div className="mt-4 p-3 bg-green-50 rounded-lg">
                      <p className="text-sm text-green-700 font-medium">
                        ✓ 14 dias grátis para testar
                      </p>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <p className="font-semibold text-sm text-gray-700">O que está incluído:</p>
                    {plan.features.map((feature, index) => (
                      <div key={index} className="flex items-start gap-2">
                        {feature.startsWith('✨') ? (
                          <>
                            <SparklesIcon className="h-5 w-5 text-purple-500 flex-shrink-0 mt-0.5" />
                            <span className="text-sm text-gray-700 font-medium">
                              {feature.replace('✨ ', '')}
                            </span>
                          </>
                        ) : (
                          <>
                            <CheckIcon className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                            <span className="text-sm text-gray-700">{feature}</span>
                          </>
                        )}
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
                
                <CardFooter className="pt-6">
                  <Button
                    className="w-full"
                    variant={plan.highlighted ? 'default' : 'outline'}
                    size="lg"
                    onClick={() => handleSelectPlan(plan.slug)}
                  >
                    Começar teste grátis
                  </Button>
                </CardFooter>
              </Card>
            );
          })}
        </div>

        {/* Comparison Table */}
        <div className="max-w-4xl mx-auto mb-16">
          <h2 className="text-2xl font-bold text-center mb-8">
            Compare os recursos
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-4">Recurso</th>
                  <th className="text-center p-4">Starter</th>
                  <th className="text-center p-4 bg-primary/5">Professional</th>
                  <th className="text-center p-4">Enterprise</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="p-4">Transações mensais</td>
                  <td className="text-center p-4">500</td>
                  <td className="text-center p-4 bg-primary/5 font-medium">2.500</td>
                  <td className="text-center p-4">Ilimitadas</td>
                </tr>
                <tr className="border-b">
                  <td className="p-4">Insights com IA</td>
                  <td className="text-center p-4">❌</td>
                  <td className="text-center p-4 bg-primary/5">✅ 10/mês</td>
                  <td className="text-center p-4">✅ Ilimitado</td>
                </tr>
                <tr className="border-b">
                  <td className="p-4">Contas bancárias</td>
                  <td className="text-center p-4">1</td>
                  <td className="text-center p-4 bg-primary/5 font-medium">3</td>
                  <td className="text-center p-4">Ilimitadas</td>
                </tr>
                <tr className="border-b">
                  <td className="p-4">Período de teste</td>
                  <td className="text-center p-4 text-green-600 font-medium">14 dias</td>
                  <td className="text-center p-4 bg-primary/5 text-green-600 font-medium">14 dias</td>
                  <td className="text-center p-4 text-green-600 font-medium">14 dias</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-8">
            Perguntas Frequentes
          </h2>
          
          <div className="space-y-6">
            <div>
              <h3 className="font-semibold text-lg mb-2">
                Como funciona o período de teste?
              </h3>
              <p className="text-gray-600">
                Todos os planos incluem 14 dias de teste grátis com acesso completo aos recursos. 
                Não é necessário cartão de crédito para começar. Você só paga se decidir continuar 
                após o período de teste.
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold text-lg mb-2">
                O que são os insights com IA?
              </h3>
              <p className="text-gray-600">
                Nossa IA analisa suas transações e gera recomendações personalizadas para economizar, 
                identifica padrões de gastos, prevê fluxo de caixa e sugere otimizações específicas 
                para o seu negócio. É como ter um consultor financeiro 24/7.
              </p>
            </div>
            
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
                O que acontece após o período de teste?
              </h3>
              <p className="text-gray-600">
                Após os 14 dias de teste, você precisará configurar um método de pagamento para 
                continuar usando o sistema. Você será notificado com antecedência e poderá escolher 
                entre pagamento mensal ou anual (com desconto).
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold text-lg mb-2">
                O que acontece se eu exceder os limites do meu plano?
              </h3>
              <p className="text-gray-600">
                Você será notificado quando atingir 80% do limite. 
                Ao exceder, você pode fazer upgrade instantaneamente ou aguardar o próximo mês 
                para os contadores resetarem.
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold text-lg mb-2">
                A categorização automática funciona com todos os bancos?
              </h3>
              <p className="text-gray-600">
                Sim! Usamos o Open Banking e integrações diretas com os principais bancos brasileiros. 
                A categorização é feita automaticamente pela Pluggy, sem nenhum trabalho manual.
              </p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center mt-16 bg-gray-50 rounded-lg p-8">
          <h3 className="text-2xl font-bold mb-4">
            Pronto para automatizar suas finanças?
          </h3>
          <p className="text-gray-600 mb-6">
            Junte-se a milhares de empresas que economizam 10+ horas por mês com o CaixaHub
          </p>
          <Button asChild size="lg">
            <Link href="/register">
              Começar Teste Grátis de 14 Dias
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function PricingPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando...</p>
        </div>
      </div>
    }>
      <PricingContent />
    </Suspense>
  );
}