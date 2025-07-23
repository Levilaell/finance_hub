import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  BanknotesIcon, 
  ChartBarIcon, 
  ShieldCheckIcon,
  CpuChipIcon,
  ClockIcon,
  CheckCircleIcon,
  ArrowRightIcon,
  StarIcon
} from "@heroicons/react/24/outline";

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      {/* Navigation */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <BanknotesIcon className="h-8 w-8 text-primary" />
              <h1 className="text-xl sm:text-2xl font-bold text-foreground">CaixaHub</h1>
            </div>
            <div className="flex items-center space-x-2 sm:space-x-4">
              <Link href="/pricing" className="hidden sm:inline text-muted-foreground hover:text-foreground">
                Planos
              </Link>
              <Button variant="ghost" asChild className="text-sm sm:text-base">
                <Link href="/login">
                  Entrar
                </Link>
              </Button>
              <Button asChild className="text-sm sm:text-base">
                <Link href="/pricing">
                  Começar Grátis
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 lg:py-32">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center space-y-8">
            <Badge variant="secondary" className="mb-4">
              ✨ Gestão financeira inteligente para PMEs
            </Badge>
            
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight">
              Transforme a{" "}
              <span className="text-primary">gestão financeira</span>{" "}
              da sua empresa
            </h1>
            
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Conecte suas contas bancárias, automatize a categorização de transações 
              e tome decisões baseadas em dados com nossa plataforma completa.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
              <Button size="lg" asChild className="text-lg px-8">
                <Link href="/pricing">
                  Começar Grátis
                  <ArrowRightIcon className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button variant="outline" size="lg" asChild className="text-lg px-8">
                <Link href="/login">
                  Entrar na Plataforma
                </Link>
              </Button>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-8 pt-8 text-sm text-muted-foreground">
              <div className="flex items-center space-x-2">
                <CheckCircleIcon className="h-5 w-5 text-green-500" />
                <span>Grátis para começar</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircleIcon className="h-5 w-5 text-green-500" />
                <span>Conexão segura com bancos</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircleIcon className="h-5 w-5 text-green-500" />
                <span>Setup em 5 minutos</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Problem & Solution Section */}
      <section className="py-20 bg-gradient-to-b from-red-50/50 to-green-50/50">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="grid lg:grid-cols-2 gap-16 items-start">
              {/* Problem */}
              <div className="space-y-6">
                <div className="inline-flex items-center px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-medium">
                  O Problema
                </div>
                <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
                  Gestão financeira manual está travando seu crescimento
                </h2>
                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p className="text-gray-600">
                      <strong>Horas perdidas</strong> categorizando transações manualmente
                    </p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p className="text-gray-600">
                      <strong>Erros custosos</strong> na reconciliação bancária
                    </p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p className="text-gray-600">
                      <strong>Decisões tardias</strong> por falta de visibilidade financeira
                    </p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p className="text-gray-600">
                      <strong>Oportunidades perdidas</strong> por não ter dados em tempo real
                    </p>
                  </div>
                </div>
              </div>

              {/* Solution */}
              <div className="space-y-6">
                <div className="inline-flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                  A Solução
                </div>
                <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
                  Automatize tudo e foque no que realmente importa
                </h2>
                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <CheckCircleIcon className="w-6 h-6 text-green-500 mt-0.5 flex-shrink-0" />
                    <p className="text-gray-600">
                      <strong>Categorização automática</strong> com 99% de precisão via IA
                    </p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <CheckCircleIcon className="w-6 h-6 text-green-500 mt-0.5 flex-shrink-0" />
                    <p className="text-gray-600">
                      <strong>Sincronização em tempo real</strong> com mais de 20 bancos
                    </p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <CheckCircleIcon className="w-6 h-6 text-green-500 mt-0.5 flex-shrink-0" />
                    <p className="text-gray-600">
                      <strong>Relatórios inteligentes</strong> para decisões rápidas e assertivas
                    </p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <CheckCircleIcon className="w-6 h-6 text-green-500 mt-0.5 flex-shrink-0" />
                    <p className="text-gray-600">
                      <strong>Economize 15h/mês</strong> e reinvista esse tempo no crescimento
                    </p>
                  </div>
                </div>
                <Button size="lg" className="mt-6">
                  Ver Como Funciona
                  <ArrowRightIcon className="ml-2 h-5 w-5" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Como funciona
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Em apenas 3 passos simples, você terá controle total das finanças da sua empresa
            </p>
          </div>

          <div className="max-w-4xl mx-auto">
            <div className="grid md:grid-cols-3 gap-8">
              {/* Step 1 */}
              <div className="text-center space-y-4">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-primary">1</span>
                </div>
                <h3 className="text-xl font-semibold">Conecte seus bancos</h3>
                <p className="text-muted-foreground">
                  Conecte suas contas bancárias de forma segura usando Open Banking. 
                  Processo leva menos de 2 minutos.
                </p>
              </div>

              {/* Step 2 */}
              <div className="text-center space-y-4">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-primary">2</span>
                </div>
                <h3 className="text-xl font-semibold">IA categoriza tudo</h3>
                <p className="text-muted-foreground">
                  Nossa inteligência artificial analisa e categoriza todas as suas 
                  transações automaticamente.
                </p>
              </div>

              {/* Step 3 */}
              <div className="text-center space-y-4">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-primary">3</span>
                </div>
                <h3 className="text-xl font-semibold">Tome decisões inteligentes</h3>
                <p className="text-muted-foreground">
                  Acesse relatórios detalhados, projeções e insights para 
                  tomar decisões financeiras mais assertivas.
                </p>
              </div>
            </div>

            <div className="text-center mt-12">
              <Button size="lg" asChild>
                <Link href="/pricing">
                  Começar Agora - É Grátis
                  <ArrowRightIcon className="ml-2 h-5 w-5" />
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-muted/50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              A plataforma financeira mais completa do Brasil
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Pare de perder tempo com planilhas e processos manuais. Nossa plataforma 
              automatiza toda sua gestão financeira, desde a conexão bancária até relatórios 
              inteligentes que geram insights para o crescimento da sua empresa.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <Card className="border-2 hover:border-primary/50 transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <BanknotesIcon className="w-6 h-6 text-primary" />
                </div>
                <CardTitle>Conexão Bancária em Tempo Real</CardTitle>
                <CardDescription>
                  Conecte com + de 20 bancos brasileiros em segundos. Sincronização automática 
                  24/7 via Open Banking para você nunca perder uma transação.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 hover:border-primary/50 transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <CpuChipIcon className="w-6 h-6 text-primary" />
                </div>
                <CardTitle>IA que Pensa pela Sua Empresa</CardTitle>
                <CardDescription>
                  Nossa IA categoriza 99% das transações automaticamente, aprende com 
                  seu negócio e economiza até 15 horas por mês do seu time financeiro.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 hover:border-primary/50 transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <ChartBarIcon className="w-6 h-6 text-primary" />
                </div>
                <CardTitle>Insights que Geram Resultados</CardTitle>
                <CardDescription>
                  Relatórios que mostram onde sua empresa está ganhando e perdendo dinheiro. 
                  Projeções precisas para você planejar o futuro com confiança.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 hover:border-primary/50 transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <ClockIcon className="w-6 h-6 text-primary" />
                </div>
                <CardTitle>Recupere 15h/Mês da Sua Equipe</CardTitle>
                <CardDescription>
                  Elimine planilhas e reconciliação manual. Sua equipe pode focar 
                  no crescimento enquanto nossa plataforma cuida da operação.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 hover:border-primary/50 transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <ShieldCheckIcon className="w-6 h-6 text-primary" />
                </div>
                <CardTitle>Segurança de Nível Bancário</CardTitle>
                <CardDescription>
                  Mesma segurança dos grandes bancos. Certificada pelo Banco Central, 
                  LGPD compliant e criptografia militar para proteger seus dados.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 hover:border-primary/50 transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <StarIcon className="w-6 h-6 text-primary" />
                </div>
                <CardTitle>Suporte que Entende do Seu Negócio</CardTitle>
                <CardDescription>
                  Consultores financeiros especialistas em PMEs te ajudam a otimizar 
                  processos e encontrar oportunidades de crescimento.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              O impacto real na sua empresa
            </h2>
            <p className="text-xl text-muted-foreground">
              Projeções baseadas no tempo típico gasto com gestão financeira manual
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-8 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="text-4xl font-bold text-primary mb-2">2 min</div>
              <div className="text-muted-foreground">Setup inicial da plataforma</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary mb-2">15h</div>
              <div className="text-muted-foreground">Tempo economizado por mês</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary mb-2">R$ 450</div>
              <div className="text-muted-foreground">Valor/hora economizada*</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary mb-2">24/7</div>
              <div className="text-muted-foreground">Sincronização automática</div>
            </div>
          </div>
          
          <div className="text-center mt-8">
            <p className="text-sm text-muted-foreground">
              *Baseado no custo médio de um analista financeiro (R$ 30/hora)
            </p>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Perguntas frequentes
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Tudo que você precisa saber para começar hoje mesmo
            </p>
          </div>

          <div className="max-w-4xl mx-auto space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-left">
                  É seguro conectar minhas contas bancárias?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Absolutamente. Usamos Open Banking, a tecnologia oficial regulamentada pelo Banco Central. 
                  Seus dados são criptografados com padrão militar e nunca armazenamos senhas bancárias. 
                  Somos certificados e auditados regularmente.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-left">
                  Quanto tempo leva para configurar?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Menos de 5 minutos. Você conecta suas contas, nossa IA começa a categorizar automaticamente 
                  e em poucos minutos você já tem relatórios funcionando. Sem instalação, sem complicação.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-left">
                  Posso experimentar antes de pagar?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Sim! Oferecemos 14 dias grátis com acesso completo a todas as funcionalidades. 
                  Sem cartão de crédito, sem compromisso. Teste tudo e veja como nossa plataforma 
                  pode transformar sua gestão financeira.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-left">
                  Como a IA aprende sobre meu negócio?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Nossa IA analisa padrões nas suas transações e aprende com suas correções. 
                  Quanto mais usar, mais precisa fica. Em poucas semanas ela conhece seu negócio 
                  melhor que uma pessoa nova na empresa.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-left">
                  E se eu precisar de ajuda para começar?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Nosso time de consultores financeiros faz todo o onboarding com você. 
                  Oferecemos treinamento completo, configuração personalizada e suporte 
                  contínuo para garantir que você aproveite 100% da plataforma.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-left">
                  Funciona com meu sistema de contabilidade?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Sim. Exportamos dados em formatos compatíveis com todos os principais sistemas 
                  contábeis (Excel, CSV). Também oferecemos integrações diretas com os 
                  softwares mais usados por contadores.
                </p>
              </CardContent>
            </Card>
          </div>

        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary text-primary-foreground">
        <div className="container mx-auto px-4 text-center">
          <div className="max-w-3xl mx-auto space-y-8">
            <h2 className="text-3xl md:text-4xl font-bold">
              Pronto para revolucionar sua gestão financeira?
            </h2>
            <p className="text-xl opacity-90">
              Junte-se a centenas de empresas brasileiras que já transformaram 
              sua gestão financeira com nossa plataforma.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button 
                size="lg" 
                variant="secondary" 
                asChild 
                className="text-lg px-8"
              >
                <Link href="/pricing">
                  Ver Planos e Preços
                  <ArrowRightIcon className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button 
                size="lg" 
                variant="secondary" 
                asChild 
                className="text-lg px-8"
              >
                <Link href="/register">
                  Começar Grátis Agora
                </Link>
              </Button>
            </div>
            <p className="text-sm opacity-75">
              Grátis para começar • Sem cartão de crédito • Setup em 5 minutos
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="flex items-center space-x-2">
              <BanknotesIcon className="h-6 w-6 text-primary" />
              <span className="font-semibold">CaixaHub</span>
            </div>
            <div className="flex space-x-6 text-sm text-muted-foreground">
              <Link href="/pricing" className="hover:text-foreground">
                Planos
              </Link>
              <Link href="/terms" className="hover:text-foreground">
                Termos de Uso
              </Link>
              <Link href="/privacy" className="hover:text-foreground">
                Privacidade
              </Link>
            </div>
            <div className="text-sm text-muted-foreground">
              © 2025 CaixaHub. Todos os direitos reservados.
            </div>
          </div>
        </div>
      </footer>
    </main>
  )
}