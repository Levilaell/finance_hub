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
              <h1 className="text-2xl font-bold text-foreground">CaixaHub</h1>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/pricing" className="text-muted-foreground hover:text-foreground">
                Planos
              </Link>
              <Button variant="ghost" asChild>
                <Link href="/login">
                  Entrar
                </Link>
              </Button>
              <Button asChild>
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

            <div className="flex items-center justify-center space-x-8 pt-8 text-sm text-muted-foreground">
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

      {/* Features Section */}
      <section className="py-20 bg-muted/50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Tudo que sua empresa precisa
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Uma solução completa para gestão financeira, desde conexão bancária 
              até relatórios avançados com inteligência artificial.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <Card className="border-2 hover:border-primary/50 transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <BanknotesIcon className="w-6 h-6 text-primary" />
                </div>
                <CardTitle>Conexão Bancária Automática</CardTitle>
                <CardDescription>
                  Integração segura com mais de 100 bancos brasileiros via Open Banking. 
                  Sincronização automática de transações em tempo real.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 hover:border-primary/50 transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <CpuChipIcon className="w-6 h-6 text-primary" />
                </div>
                <CardTitle>Categorização Inteligente</CardTitle>
                <CardDescription>
                  IA avançada categoriza suas transações automaticamente, economizando 
                  horas de trabalho manual e garantindo precisão na organização.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 hover:border-primary/50 transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <ChartBarIcon className="w-6 h-6 text-primary" />
                </div>
                <CardTitle>Relatórios Avançados</CardTitle>
                <CardDescription>
                  Dashboards interativos com análises profundas de fluxo de caixa, 
                  categorias de gastos e projeções financeiras.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 hover:border-primary/50 transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <ClockIcon className="w-6 h-6 text-primary" />
                </div>
                <CardTitle>Economia de Tempo</CardTitle>
                <CardDescription>
                  Automatize tarefas repetitivas e reduza o tempo gasto com 
                  reconciliação bancária de dias para minutos.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 hover:border-primary/50 transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <ShieldCheckIcon className="w-6 h-6 text-primary" />
                </div>
                <CardTitle>Segurança Bancária</CardTitle>
                <CardDescription>
                  Criptografia de nível bancário, conformidade com LGPD e certificações 
                  de segurança internacionais para proteger seus dados.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 hover:border-primary/50 transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <StarIcon className="w-6 h-6 text-primary" />
                </div>
                <CardTitle>Suporte Especializado</CardTitle>
                <CardDescription>
                  Equipe de especialistas em gestão financeira disponível para 
                  ajudar sua empresa a crescer de forma sustentável.
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
              Resultados que falam por si
            </h2>
            <p className="text-xl text-muted-foreground">
              Empresas que usam nossa plataforma economizam tempo e aumentam a eficiência
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-8 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="text-4xl font-bold text-primary mb-2">90%</div>
              <div className="text-muted-foreground">Redução no tempo de reconciliação</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary mb-2">15h</div>
              <div className="text-muted-foreground">Horas economizadas por mês</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary mb-2">99%</div>
              <div className="text-muted-foreground">Precisão na categorização</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary mb-2">100+</div>
              <div className="text-muted-foreground">Bancos conectados</div>
            </div>
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
                variant="outline" 
                asChild 
                className="text-lg px-8 border-primary-foreground text-primary-foreground hover:bg-primary-foreground hover:text-primary"
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
              <Link href="#" className="hover:text-foreground">
                Suporte
              </Link>
            </div>
            <div className="text-sm text-muted-foreground">
              © 2024 CaixaHub. Todos os direitos reservados.
            </div>
          </div>
        </div>
      </footer>
    </main>
  )
}