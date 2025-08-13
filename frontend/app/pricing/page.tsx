'use client';

import { useState, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckIcon, XMarkIcon, SparklesIcon, BanknotesIcon, StarIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { formatCurrency } from '@/lib/utils';
import { ThemeSwitcher } from '@/components/theme-switcher';

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

// Plans synchronized with backend (create_subscription_plans.py) and Stripe dashboard
// IMPORTANT: Keep prices in sync with backend/apps/companies/management/commands/create_subscription_plans.py
const plans: PricingPlan[] = [
  {
    id: 'starter',
    name: 'Starter',
    slug: 'starter',
    description: 'Perfeito para empresas que estão começando a organizar suas finanças',
    priceMonthly: 49,   // R$ 49/mês - Synced with Stripe price_1RkePtPFSVtvOaJKYbiX6TqQ
    priceYearly: 490,   // R$ 490/ano - Synced with Stripe price_1RnPVfPFSVtvOaJKmwzNmUdz
    features: [
      '1 conta bancária',
      '500 transações por mês',
      'Dashboard financeiro',
      'Relatórios básicos',
      'Categorização automática',
      'Exportação PDF/Excel',
      'Suporte por email',
    ],
    limitations: [
      'Não inclui análises por IA',
    ],
  },
  {
    id: 'professional',
    name: 'Profissional',
    slug: 'professional',
    description: 'Ideal para empresas que querem insights inteligentes e automação completa',
    priceMonthly: 149,  // R$ 149/mês - Synced with Stripe price_1RkeQgPFSVtvOaJKgPQzW1SD
    priceYearly: 1490,  // R$ 1490/ano - Synced with Stripe price_1RnPVRPFSVtvOaJKlWxiSHnn
    highlighted: true,
    badge: 'Mais Popular',
    features: [
      '3 contas bancárias',
      '2.500 transações por mês',
      'Tudo do plano Starter, mais:',
      '✨ IA Financeira: 10 interações mensais',
      '✨ Insights automáticos personalizados',
      '✨ Previsões de fluxo de caixa',
      '✨ Alertas de gastos e anomalias',
      '✨ Relatórios inteligentes',
    ],
    limitations: [
      'Limite de 10 análises de IA por mês',
    ],
  },
  {
    id: 'enterprise',
    name: 'Empresarial',
    slug: 'enterprise',
    description: 'Solução completa e ilimitada para empresas com operação complexa',
    priceMonthly: 349,  // R$ 349/mês - Synced with Stripe price_1RkeMJPFSVtvOaJKuIZxvjPa
    priceYearly: 3490,  // R$ 3490/ano - Synced with Stripe price_1RnPV8PFSVtvOaJKuIZxvjPa
    features: [
      'Contas e transações ilimitadas',
      'Tudo dos planos anteriores, mais:',
      '✨ IA Avançada: Interação ilimitada',
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
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 bg-gradient-subtle opacity-30"></div>
      
      {/* Navigation */}
      <header className="border-b glass sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="h-10 w-10 rounded-full bg-white/10 border border-white/20 flex items-center justify-center">
                <BanknotesIcon className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-white">CaixaHub</h1>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" asChild>
                <Link href="/login">
                  Entrar
                </Link>
              </Button>
              <Button asChild className="btn-gradient">
                <Link href="/register">
                  Teste Grátis
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </header>
      
      <div className="container mx-auto px-4 py-16 relative">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-6">
            <Badge className="glass px-6 py-2 text-lg">
              <StarIcon className="h-5 w-5 mr-2" />
              Planos e Preços
            </Badge>
          </div>
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
            Escolha o plano ideal
            <br />
            <span className="text-white">para sua empresa</span>
          </h1>
          <p className="text-xl text-white mb-4">
            Sistema financeiro que funciona sozinho com IA
          </p>
          <div className="text-center mb-8">
            <div className="glass rounded-lg p-4 inline-block">
              <p className="text-lg">
                <span className="text-success font-bold">14 dias grátis</span> em todos os planos • <span className="text-white">Cancele quando quiser</span>
              </p>
            </div>
          </div>
          
          {/* Billing Toggle */}
          <div className="text-center">
            <div className="glass rounded-xl p-6 inline-flex items-center gap-6">
              <Label htmlFor="billing-toggle" className={`transition-colors ${!isYearly ? 'font-semibold text-foreground' : 'text-muted-foreground'}`}>
                Mensal
              </Label>
              <Switch
                id="billing-toggle"
                checked={isYearly}
                onCheckedChange={setIsYearly}
                className="mx-2"
              />
              <div className="flex items-center gap-2">
                <Label htmlFor="billing-toggle" className={`transition-colors ${isYearly ? 'font-semibold text-foreground' : 'text-muted-foreground'}`}>
                  Anual
                </Label>
                <Badge className="bg-success/10 text-success border-success/20 whitespace-nowrap">
                  Economize até 17%
                </Badge>
              </div>
            </div>
          </div>
        </div>

        {/* Value Props */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-12 max-w-4xl mx-auto">
          <div className="glass rounded-lg p-4 hover-lift transition-all duration-300">
            <div className="text-center">
              <CheckIcon className="h-8 w-8 text-success mx-auto mb-2" />
              <p className="text-sm font-medium">Categorização automática via Open Banking</p>
            </div>
          </div>
          <div className="glass rounded-lg p-4 hover-lift transition-all duration-300">
            <div className="text-center">
              <SparklesIcon className="h-8 w-8 text-white mx-auto mb-2" />
              <p className="text-sm font-medium">IA que aprende seu negócio</p>
            </div>
          </div>
          <div className="glass rounded-lg p-4 hover-lift transition-all duration-300">
            <div className="text-center">
              <svg className="h-8 w-8 text-white mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <p className="text-sm font-medium">Relatórios prontos em segundos</p>
            </div>
          </div>
          <div className="glass rounded-lg p-4 hover-lift transition-all duration-300">
            <div className="text-center">
              <svg className="h-8 w-8 text-info mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm font-medium">14 dias para testar grátis</p>
            </div>
          </div>
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
                className={`relative flex flex-col glass hover-lift transition-all duration-300 ${
                  plan.highlighted
                    ? 'border-white/50 shadow-xl hover:shadow-2xl hover:shadow-white/25 scale-105 z-10'
                    : 'hover:shadow-lg'
                }`}
              >
                {plan.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge className="bg-white/10 border border-white/20 text-white px-4 py-1">
                      <StarIcon className="h-4 w-4 mr-1" />
                      {plan.badge}
                    </Badge>
                  </div>
                )}
                
                <CardHeader className="pb-8">
                  <CardTitle className="text-2xl text-white">{plan.name}</CardTitle>
                  <CardDescription className="mt-2 text-white/80">{plan.description}</CardDescription>
                </CardHeader>
                
                <CardContent className="flex-1">
                  <div className="mb-6">
                    <div className="flex items-baseline">
                      <span className="text-4xl font-bold text-white">
                        {formatPrice(monthlyPrice)}
                      </span>
                      <span className="text-white/70 ml-2">/mês</span>
                    </div>
                    {isYearly && (
                      <div className="mt-2">
                        <p className="text-sm text-white/70">
                          Cobrado anualmente: {formatPrice(price)}
                        </p>
                        {discount > 0 && (
                          <p className="text-sm text-success font-medium">
                            Economia de {discount}% no plano anual
                          </p>
                        )}
                      </div>
                    )}
                    <div className="mt-4 p-3 glass rounded-lg border border-success/20">
                      <p className="text-sm text-success font-medium flex items-center">
                        <CheckIcon className="h-4 w-4 mr-2" />
                        14 dias grátis para testar
                      </p>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <p className="font-semibold text-sm text-foreground">O que está incluído:</p>
                    {plan.features.map((feature, index) => {
                      // Handle separator text
                      if (feature.startsWith('Tudo do')) {
                        return (
                          <div key={index} className="pt-3 pb-1">
                            <div className="h-px bg-border mb-3"></div>
                            <span className="text-sm text-white font-semibold italic">
                              {feature}
                            </span>
                          </div>
                        );
                      }
                      
                      return (
                        <div key={index} className="flex items-start gap-2">
                          {feature.startsWith('✨') ? (
                            <>
                              <SparklesIcon className="h-5 w-5 text-white flex-shrink-0 mt-0.5" />
                              <span className="text-sm text-foreground font-medium">
                                {feature.replace('✨ ', '')}
                              </span>
                            </>
                          ) : (
                            <>
                              <CheckIcon className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                              <span className="text-sm text-foreground">{feature}</span>
                            </>
                          )}
                        </div>
                      );
                    })}
                    
                    {plan.limitations.length > 0 && (
                      <>
                        <div className="pt-3 border-t border-border" />
                        {plan.limitations.map((limitation, index) => (
                          <div key={index} className="flex items-start gap-2">
                            <XMarkIcon className="h-5 w-5 text-white/50 flex-shrink-0 mt-0.5" />
                            <span className="text-sm text-white/60">{limitation}</span>
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                </CardContent>
                
                <CardFooter className="pt-6">
                  <Button
                    className={`w-full transition-all duration-300 ${
                      plan.highlighted 
                        ? 'btn-gradient hover-glow' 
                        : 'hover:bg-muted hover-lift'
                    }`}
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
          <h2 className="text-3xl font-bold text-center mb-8 text-white">
            Compare os recursos
          </h2>
          <div className="glass rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-border bg-muted/50">
                    <th className="text-left p-4 text-foreground font-semibold">Recurso</th>
                    <th className="text-center p-4 text-foreground font-semibold">Starter</th>
                    <th className="text-center p-4 bg-white/5 text-white font-semibold">Professional</th>
                    <th className="text-center p-4 text-foreground font-semibold">Enterprise</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-border hover:bg-muted/30 transition-colors">
                    <td className="p-4 text-foreground font-medium">Contas bancárias</td>
                    <td className="text-center p-4 text-white/80">1</td>
                    <td className="text-center p-4 bg-white/5 text-white font-semibold">3</td>
                    <td className="text-center p-4 text-foreground font-medium">Ilimitadas</td>
                  </tr>
                  <tr className="border-b border-border hover:bg-muted/30 transition-colors">
                    <td className="p-4 text-foreground font-medium">Transações mensais</td>
                    <td className="text-center p-4 text-white/80">500</td>
                    <td className="text-center p-4 bg-white/5 text-white font-semibold">2.500</td>
                    <td className="text-center p-4 text-foreground font-medium">Ilimitadas</td>
                  </tr>
                  <tr className="border-b border-border hover:bg-muted/30 transition-colors">
                    <td className="p-4 text-foreground font-medium">Análises de IA</td>
                    <td className="text-center p-4">
                      <XMarkIcon className="h-5 w-5 text-white/60 mx-auto" />
                    </td>
                    <td className="text-center p-4 bg-white/5">
                      <div className="flex items-center justify-center gap-2">
                        <SparklesIcon className="h-5 w-5 text-white" />
                        <span className="text-white font-semibold">10/mês</span>
                      </div>
                    </td>
                    <td className="text-center p-4">
                      <div className="flex items-center justify-center gap-2">
                        <SparklesIcon className="h-5 w-5 text-white" />
                        <span className="text-foreground font-medium">Ilimitado</span>
                      </div>
                    </td>
                  </tr>
                  <tr className="border-b border-border hover:bg-muted/30 transition-colors">
                    <td className="p-4 text-foreground font-medium">Tipo de suporte</td>
                    <td className="text-center p-4 text-white/80">Email</td>
                    <td className="text-center p-4 bg-white/5 text-white font-semibold">WhatsApp</td>
                    <td className="text-center p-4 text-foreground font-medium">Telefone + Email</td>
                  </tr>
                  <tr className="hover:bg-muted/30 transition-colors">
                    <td className="p-4 text-foreground font-medium">Período de teste</td>
                    <td className="text-center p-4 text-success font-semibold">14 dias</td>
                    <td className="text-center p-4 bg-primary/10 text-success font-semibold">14 dias</td>
                    <td className="text-center p-4 text-success font-semibold">14 dias</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-8 text-white">
            Perguntas Frequentes
          </h2>
          
          <div className="space-y-6">
            <div className="glass rounded-lg p-6 hover-lift transition-all duration-300">
              <h3 className="font-semibold text-lg mb-3 text-white">
                Como funciona o período de teste?
              </h3>
              <p className="text-white/80">
                Todos os planos incluem 14 dias de teste grátis com acesso completo aos recursos. 
                Não é necessário cartão de crédito para começar. Você só paga se decidir continuar 
                após o período de teste.
              </p>
            </div>
            
            <div className="glass rounded-lg p-6 hover-lift transition-all duration-300">
              <h3 className="font-semibold text-lg mb-3 text-white">
                O que são as análises de IA?
              </h3>
              <p className="text-white/80">
                Nossa IA analisa seus dados financeiros e gera insights personalizados: identifica padrões de gastos, 
                prevê seu fluxo de caixa, detecta gastos incomuns e sugere oportunidades de economia específicas 
                para o seu negócio. É como ter um consultor financeiro inteligente trabalhando 24/7.
              </p>
            </div>
            
            <div className="glass rounded-lg p-6 hover-lift transition-all duration-300">
              <h3 className="font-semibold text-lg mb-3 text-white">
                Posso mudar de plano depois?
              </h3>
              <p className="text-white/80">
                Sim! Você pode fazer upgrade ou downgrade a qualquer momento. 
                As mudanças são aplicadas imediatamente e os valores são calculados proporcionalmente.
              </p>
            </div>
            
            <div className="glass rounded-lg p-6 hover-lift transition-all duration-300">
              <h3 className="font-semibold text-lg mb-3 text-white">
                O que acontece após o período de teste?
              </h3>
              <p className="text-white/80">
                Após os 14 dias de teste, você precisará configurar um método de pagamento para 
                continuar usando o sistema. Você será notificado com antecedência e poderá escolher 
                entre pagamento mensal ou anual (com desconto).
              </p>
            </div>
            
            <div className="glass rounded-lg p-6 hover-lift transition-all duration-300">
              <h3 className="font-semibold text-lg mb-3 text-white">
                O que acontece se eu precisar de mais do que meu plano oferece?
              </h3>
              <p className="text-white/80">
                Você será notificado quando atingir 80% dos limites de transações ou análises de IA. 
                Pode fazer upgrade instantaneamente para o próximo plano ou aguardar o próximo mês. 
                O plano Empresarial não tem limites.
              </p>
            </div>
            
            <div className="glass rounded-lg p-6 hover-lift transition-all duration-300">
              <h3 className="font-semibold text-lg mb-3 text-white">
                A categorização automática funciona com todos os bancos?
              </h3>
              <p className="text-white/80">
                Sim! Usamos o Open Banking e integrações diretas com os principais bancos brasileiros. 
                A categorização é feita automaticamente pela Pluggy, sem nenhum trabalho manual.
              </p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center mt-16 bg-white/10 border border-white/20 rounded-xl p-8 text-white relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5"></div>
          <div className="relative z-10">
            <h3 className="text-3xl font-bold mb-4">
              Pronto para automatizar suas finanças?
            </h3>
            <p className="text-white/90 mb-6 text-lg">
              Junte-se a milhares de empresas que economizam 10+ horas por mês com o CaixaHub
            </p>
            <Button asChild size="lg" className="bg-white text-black hover:bg-white/90 hover-lift">
              <Link href="/register">
                Começar Teste Grátis de 14 Dias
              </Link>
            </Button>
          </div>
        </div>
      </div>
      
      {/* Footer */}
      <footer className="border-t py-12 bg-card mt-16">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="flex items-center space-x-2">
              <div className="h-8 w-8 rounded-full bg-white/10 border border-white/20 flex items-center justify-center">
                <BanknotesIcon className="h-4 w-4 text-white" />
              </div>
              <span className="font-semibold text-white">CaixaHub</span>
            </div>
            <div className="flex space-x-6 text-sm text-white/70">
              <Link href="/" className="hover:text-foreground transition-colors">
                Início
              </Link>
              <Link href="/terms" className="hover:text-foreground transition-colors">
                Termos de Uso
              </Link>
              <Link href="/privacy" className="hover:text-foreground transition-colors">
                Privacidade
              </Link>
            </div>
            <div className="text-sm text-white/70">
              © 2025 CaixaHub. Todos os direitos reservados.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default function PricingPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 spinner mx-auto mb-4"></div>
          <p className="text-muted-foreground">Carregando...</p>
        </div>
      </div>
    }>
      <PricingContent />
    </Suspense>
  );
}