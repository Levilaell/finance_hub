'use client';

import { Suspense } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { CheckIcon, SparklesIcon, BanknotesIcon, StarIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

function PricingContent() {
  const router = useRouter();

  const handleSelectPlan = () => {
    router.push('/register');
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
                  Começar Trial
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

          </div>
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
            Um único plano com
            <br />
            <span className="text-white">acesso completo</span>
          </h1>
          <p className="text-xl text-white mb-4">
            Tudo que você precisa para automatizar sua gestão financeira
          </p>
          <div className="text-center mb-8">
            <div className="glass rounded-lg p-4 inline-block">
              <p className="text-lg">
                <span className="text-success font-bold">7 dias de trial grátis</span> • <span className="text-white">Cancele quando quiser</span>
              </p>
            </div>
          </div>
        </div>

        {/* Value Props */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-12 max-w-4xl mx-auto">
          <div className="glass rounded-lg p-4 hover-lift transition-all duration-300">
            <div className="text-center">
              <CheckIcon className="h-8 w-8 text-success mx-auto mb-2" />
              <p className="text-sm font-medium">Conexão com +20 bancos</p>
            </div>
          </div>
          <div className="glass rounded-lg p-4 hover-lift transition-all duration-300">
            <div className="text-center">
              <SparklesIcon className="h-8 w-8 text-white mx-auto mb-2" />
              <p className="text-sm font-medium">Categorização por IA</p>
            </div>
          </div>
          <div className="glass rounded-lg p-4 hover-lift transition-all duration-300">
            <div className="text-center">
              <svg className="h-8 w-8 text-white mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <p className="text-sm font-medium">Relatórios ilimitados</p>
            </div>
          </div>
          <div className="glass rounded-lg p-4 hover-lift transition-all duration-300">
            <div className="text-center">
              <ShieldCheckIcon className="h-8 w-8 text-white mx-auto mb-2" />
              <p className="text-sm font-medium">Segurança bancária</p>
            </div>
          </div>
        </div>

        {/* Pricing Card */}
        <div className="max-w-lg mx-auto mb-16">
          <Card className="glass hover-lift transition-all duration-300 border-white/50 shadow-xl">
            <CardHeader className="text-center pb-8">
              <CardTitle className="text-3xl text-white mb-2">Plano Pro</CardTitle>
              <CardDescription className="text-white/80 text-lg">
                Acesso completo a todos os recursos da plataforma
              </CardDescription>
            </CardHeader>

            <CardContent className="text-center">
              <div className="mb-8">
                <div className="flex items-baseline justify-center">
                  <span className="text-5xl font-bold text-white">R$ 97</span>
                  <span className="text-white/70 ml-2 text-xl">/mês</span>
                </div>
                <p className="text-sm text-white/70 mt-2">
                  Cobrado mensalmente
                </p>
              </div>

              <div className="p-4 glass rounded-lg border border-success/30 mb-8">
                <p className="text-success font-medium flex items-center justify-center">
                  <CheckIcon className="h-5 w-5 mr-2" />
                  7 dias de trial grátis para testar
                </p>
                <p className="text-xs text-white/70 mt-2">
                  Cancele a qualquer momento
                </p>
              </div>

              <div className="space-y-3 text-left">
                <p className="font-semibold text-sm text-foreground mb-4">Tudo que está incluído:</p>

                <div className="flex items-start gap-2">
                  <CheckIcon className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-foreground">Conexão ilimitada com bancos via Open Banking</span>
                </div>

                <div className="flex items-start gap-2">
                  <CheckIcon className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-foreground">Sincronização automática</span>
                </div>

                <div className="flex items-start gap-2">
                  <CheckIcon className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-foreground">Transações ilimitadas</span>
                </div>

                <div className="flex items-start gap-2">
                  <CheckIcon className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-foreground font-medium">Categorização automática por IA</span>
                </div>

                <div className="flex items-start gap-2">
                  <CheckIcon className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-foreground">Dashboard financeiro completo</span>
                </div>

                <div className="flex items-start gap-2">
                  <CheckIcon className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-foreground">Relatórios detalhados (PDF e Excel)</span>
                </div>

                <div className="flex items-start gap-2">
                  <CheckIcon className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-foreground">Categorias personalizadas</span>
                </div>

                <div className="flex items-start gap-2">
                  <CheckIcon className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-foreground">Suporte via WhatsApp</span>
                </div>

                <div className="flex items-start gap-2">
                  <CheckIcon className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-foreground">Atualizações e novos recursos incluídos</span>
                </div>

                <div className="flex items-start gap-2">
                  <SparklesIcon className="h-5 w-5 text-white flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-foreground font-medium">Insights inteligentes ilimitados</span>
                </div>
              </div>
              
            </CardContent>

            <CardFooter className="pt-6">
              <Button
                className="w-full btn-gradient hover-glow transition-all duration-300"
                size="lg"
                onClick={handleSelectPlan}
              >
                Começar Trial de 7 Dias
              </Button>
            </CardFooter>
          </Card>
        </div>

        {/* FAQ Section */}
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-8 text-white">
            Perguntas Frequentes
          </h2>

          <div className="space-y-6">
            <div className="glass rounded-lg p-6 hover-lift transition-all duration-300">
              <h3 className="font-semibold text-lg mb-3 text-white">
                Como funciona o trial de 7 dias?
              </h3>
              <p className="text-white/80">
                Ao se cadastrar, você tem 7 dias para testar todos os recursos da plataforma gratuitamente.
                Você só será cobrado após o período de trial.
                Pode cancelar a qualquer momento durante o trial sem nenhum custo.
              </p>
            </div>

            <div className="glass rounded-lg p-6 hover-lift transition-all duration-300">
              <h3 className="font-semibold text-lg mb-3 text-white">
                Preciso cadastrar cartão de crédito no trial?
              </h3>
              <p className="text-white/80">
                Sim. Para garantir uma transição suave após o trial, pedimos o cadastro do cartão no início.
                Você não será cobrado durante os 7 dias de trial e pode cancelar a qualquer momento sem custos.
              </p>
            </div>

            <div className="glass rounded-lg p-6 hover-lift transition-all duration-300">
              <h3 className="font-semibold text-lg mb-3 text-white">
                É seguro conectar minhas contas bancárias?
              </h3>
              <p className="text-white/80">
                Absolutamente. Usamos Open Banking, a tecnologia oficial regulamentada pelo Banco Central.
                Seus dados são criptografados com padrão militar e nunca armazenamos senhas bancárias.
                Temos a mesma segurança dos grandes bancos brasileiros.
              </p>
            </div>

            <div className="glass rounded-lg p-6 hover-lift transition-all duration-300">
              <h3 className="font-semibold text-lg mb-3 text-white">
                Posso cancelar a qualquer momento?
              </h3>
              <p className="text-white/80">
                Sim! Não há fidelidade ou multa por cancelamento. Você pode cancelar sua assinatura
                a qualquer momento diretamente nas configurações da plataforma. Seu acesso continuará
                até o final do período já pago.
              </p>
            </div>

            <div className="glass rounded-lg p-6 hover-lift transition-all duration-300">
              <h3 className="font-semibold text-lg mb-3 text-white">
                O que acontece após o trial?
              </h3>
              <p className="text-white/80">
                Após os 7 dias de trial, seu cartão será cobrado automaticamente no valor de R$ 97,00
                e você continuará tendo acesso completo à plataforma. Você receberá um aviso por email
                antes do término do trial.
              </p>
            </div>

            <div className="glass rounded-lg p-6 hover-lift transition-all duration-300">
              <h3 className="font-semibold text-lg mb-3 text-white">
                Tem limite de transações ou bancos?
              </h3>
              <p className="text-white/80">
                Não! O Plano Pro inclui transações ilimitadas, conexão com quantos bancos você precisar,
                e uso ilimitado de todos os recursos da plataforma, incluindo categorização por IA e relatórios.
              </p>
            </div>

            <div className="glass rounded-lg p-6 hover-lift transition-all duration-300">
              <h3 className="font-semibold text-lg mb-3 text-white">
                Quais formas de pagamento são aceitas?
              </h3>
              <p className="text-white/80">
                Aceitamos todos os principais cartões de crédito (Visa, Mastercard, Amex, Elo).
                O pagamento é processado de forma segura pela Stripe, uma das maiores plataformas
                de pagamento do mundo.
              </p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center mt-16 bg-white/10 border border-white/20 rounded-xl p-8 text-white relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5"></div>
          <div className="relative z-10">
            <h3 className="text-3xl font-bold mb-4">
              Pronto para transformar sua gestão financeira?
            </h3>
            <p className="text-white/90 mb-6 text-lg">
              Comece seu trial de 7 dias e veja como é fácil automatizar suas finanças
            </p>
            <Button asChild size="lg" className="bg-white text-black hover:bg-white/90 hover-lift">
              <Link href="/register">
                Começar Trial Grátis de 7 Dias
              </Link>
            </Button>
            <p className="text-sm text-white/70 mt-4">
              Cancele a qualquer momento • Sem fidelidade
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-white/20 py-12 bg-background/80 backdrop-blur-sm mt-16 relative z-10">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="flex items-center space-x-2">
              <div className="h-8 w-8 rounded-full bg-white/10 border border-white/20 flex items-center justify-center">
                <BanknotesIcon className="h-4 w-4 text-white" />
              </div>
              <span className="font-semibold text-white">CaixaHub</span>
            </div>
            <div className="flex space-x-6 text-sm">
              <Link href="/" className="text-white/80 hover:text-white transition-colors cursor-pointer">
                Início
              </Link>
              <Link href="/terms" className="text-white/80 hover:text-white transition-colors cursor-pointer">
                Termos de Uso
              </Link>
              <Link href="/privacy" className="text-white/80 hover:text-white transition-colors cursor-pointer">
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
