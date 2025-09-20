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
  StarIcon,
  SparklesIcon,
  LinkIcon,
  ArrowPathIcon,
  DocumentTextIcon,
  EyeIcon,
  CogIcon,
  UserGroupIcon,
  PhoneIcon,
  LockClosedIcon,
  CloudArrowDownIcon,
  PresentationChartLineIcon,
  BellAlertIcon,
  CalculatorIcon,
  FolderIcon,
  DocumentCheckIcon,
  ChartPieIcon
} from "@heroicons/react/24/outline";

export default function HowItWorks() {
  return (
    <main className="min-h-screen bg-background">
      {/* Navigation */}
      <header className="border-b glass sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Link href="/" className="flex items-center space-x-2">
                <div className="h-10 w-10 rounded-full bg-white/10 border border-white/20 flex items-center justify-center">
                  <BanknotesIcon className="h-6 w-6 text-white" />
                </div>
                <h1 className="text-xl sm:text-2xl font-bold text-white">CaixaHub</h1>
              </Link>
            </div>
            <div className="flex items-center space-x-2 sm:space-x-4">
              <Link href="/" className="hidden sm:inline text-muted-foreground hover:text-foreground transition-colors">
                Início
              </Link>
              <Link href="/pricing" className="hidden sm:inline text-muted-foreground hover:text-foreground transition-colors">
                Planos
              </Link>
              <Button variant="ghost" asChild className="text-sm sm:text-base hover:bg-muted">
                <Link href="/login">
                  Entrar
                </Link>
              </Button>
              <Button asChild className="text-sm sm:text-base btn-gradient">
                <Link href="/pricing">
                  Começar Grátis
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-16 lg:py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-subtle opacity-50"></div>
        <div className="container mx-auto px-4 relative">
          <div className="max-w-4xl mx-auto text-center space-y-6">
            <Badge variant="secondary" className="mb-4 glass border-white/20">
              <SparklesIcon className="h-4 w-4 mr-1" />
              Guia Completo da Plataforma
            </Badge>
            
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight">
              Como Funciona o{" "}
              <span className="text-white font-semibold">CaixaHub</span>
            </h1>
            
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              Descubra como nossa plataforma transforma a gestão financeira da sua empresa 
              em um processo automatizado, seguro e inteligente. Do setup inicial aos 
              relatórios avançados, entenda cada funcionalidade.
            </p>
          </div>
        </div>
      </section>

      {/* Quick Overview Steps */}
      <section className="py-16 bg-muted/20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Visão Geral em 4 Passos
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              O processo completo para ter controle financeiro automatizado
            </p>
          </div>

          <div className="max-w-6xl mx-auto">
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Step 1 */}
              <Card className="glass hover-lift transition-all duration-300">
                <CardHeader className="text-center">
                  <div className="w-16 h-16 bg-blue-500/20 border border-blue-500/30 rounded-full flex items-center justify-center mx-auto mb-4">
                    <LinkIcon className="w-8 h-8 text-blue-400" />
                  </div>
                  <CardTitle className="text-lg">1. Conecte</CardTitle>
                  <CardDescription>
                    Vincule suas contas bancárias de forma segura via Open Banking
                  </CardDescription>
                </CardHeader>
              </Card>

              {/* Step 2 */}
              <Card className="glass hover-lift transition-all duration-300">
                <CardHeader className="text-center">
                  <div className="w-16 h-16 bg-green-500/20 border border-green-500/30 rounded-full flex items-center justify-center mx-auto mb-4">
                    <ArrowPathIcon className="w-8 h-8 text-green-400" />
                  </div>
                  <CardTitle className="text-lg">2. Sincronize</CardTitle>
                  <CardDescription>
                    Transações são importadas e categorizadas automaticamente
                  </CardDescription>
                </CardHeader>
              </Card>

              {/* Step 3 */}
              <Card className="glass hover-lift transition-all duration-300">
                <CardHeader className="text-center">
                  <div className="w-16 h-16 bg-purple-500/20 border border-purple-500/30 rounded-full flex items-center justify-center mx-auto mb-4">
                    <ChartBarIcon className="w-8 h-8 text-purple-400" />
                  </div>
                  <CardTitle className="text-lg">3. Analise</CardTitle>
                  <CardDescription>
                    Visualize dashboards e relatórios financeiros em tempo real
                  </CardDescription>
                </CardHeader>
              </Card>

              {/* Step 4 */}
              <Card className="glass hover-lift transition-all duration-300">
                <CardHeader className="text-center">
                  <div className="w-16 h-16 bg-orange-500/20 border border-orange-500/30 rounded-full flex items-center justify-center mx-auto mb-4">
                    <PresentationChartLineIcon className="w-8 h-8 text-orange-400" />
                  </div>
                  <CardTitle className="text-lg">4. Decida</CardTitle>
                  <CardDescription>
                    Tome decisões baseadas em insights gerados pela IA
                  </CardDescription>
                </CardHeader>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Detailed Features */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Funcionalidades Detalhadas
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Conheça cada recurso da plataforma e como eles trabalham juntos para 
              automatizar sua gestão financeira
            </p>
          </div>

          <div className="space-y-24 max-w-6xl mx-auto">
            
            {/* Banking Connection */}
            <div className="grid lg:grid-cols-2 gap-16 items-center">
              <div className="space-y-6">
                <div className="inline-flex items-center px-3 py-1 bg-blue-500/10 text-blue-400 rounded-full text-sm font-medium">
                  <LinkIcon className="h-4 w-4 mr-2" />
                  Conexão Bancária
                </div>
                <h3 className="text-3xl md:text-4xl font-bold">
                  Conecte com + de 20 Bancos Brasileiros
                </h3>
                <p className="text-lg text-muted-foreground leading-relaxed">
                  Utilize a tecnologia Open Banking, regulamentada pelo Banco Central, 
                  para conectar suas contas de forma 100% segura. Sem senhas, sem planilhas, 
                  sem trabalho manual.
                </p>
                <div className="grid sm:grid-cols-2 gap-4">
                  <div className="flex items-start space-x-3">
                    <CheckCircleIcon className="w-6 h-6 text-success mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold">Setup em 2 minutos</p>
                      <p className="text-sm text-muted-foreground">Processo guiado e intuitivo</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <CheckCircleIcon className="w-6 h-6 text-success mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold">Múltiplas contas</p>
                      <p className="text-sm text-muted-foreground">Conecte quantas contas precisar</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <CheckCircleIcon className="w-6 h-6 text-success mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold">Renovação automática</p>
                      <p className="text-sm text-muted-foreground">Renova conexão automaticamente</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <CheckCircleIcon className="w-6 h-6 text-success mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold">Histórico completo</p>
                      <p className="text-sm text-muted-foreground">Importa até 24 meses</p>
                    </div>
                  </div>
                </div>
              </div>
              <Card className="glass">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <ShieldCheckIcon className="h-6 w-6 mr-2 text-success" />
                    Segurança Bancária
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <LockClosedIcon className="h-5 w-5 text-blue-400 mt-1" />
                    <div>
                      <p className="font-semibold text-sm">Criptografia Militar</p>
                      <p className="text-xs text-muted-foreground">AES-256 para todos os dados</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <CheckCircleIcon className="h-5 w-5 text-green-400 mt-1" />
                    <div>
                      <p className="font-semibold text-sm">Certificação BACEN</p>
                      <p className="text-xs text-muted-foreground">Regulamentado pelo Banco Central</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <EyeIcon className="h-5 w-5 text-purple-400 mt-1" />
                    <div>
                      <p className="font-semibold text-sm">Acesso Somente Leitura</p>
                      <p className="text-xs text-muted-foreground">Nunca movimentamos seu dinheiro</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Transaction Sync */}
            <div className="grid lg:grid-cols-2 gap-16 items-center">
              <Card className="glass order-2 lg:order-1">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <ArrowPathIcon className="h-6 w-6 mr-2 text-green-400" />
                    Como Funciona a Sincronização
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center text-xs font-bold text-white">1</div>
                      <div>
                        <p className="font-semibold text-sm">Coleta Automática</p>
                        <p className="text-xs text-muted-foreground">Sistema verifica novas transações a cada hora</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center text-xs font-bold text-white">2</div>
                      <div>
                        <p className="font-semibold text-sm">Processamento IA</p>
                        <p className="text-xs text-muted-foreground">IA analisa e categoriza cada transação</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center text-xs font-bold text-white">3</div>
                      <div>
                        <p className="font-semibold text-sm">Atualização em Tempo Real</p>
                        <p className="text-xs text-muted-foreground">Dashboards são atualizados automaticamente</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <div className="space-y-6 order-1 lg:order-2">
                <div className="inline-flex items-center px-3 py-1 bg-green-500/10 text-green-400 rounded-full text-sm font-medium">
                  <ArrowPathIcon className="h-4 w-4 mr-2" />
                  Sincronização de Transações
                </div>
                <h3 className="text-3xl md:text-4xl font-bold">
                  Sempre Atualizado, Sempre Preciso
                </h3>
                <p className="text-lg text-muted-foreground leading-relaxed">
                  Nossa tecnologia de sincronização inteligente mantém seus dados financeiros 
                  sempre atualizados, com categorização automática por IA e alertas em tempo real 
                  para movimentações importantes.
                </p>
                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <ClockIcon className="w-6 h-6 text-blue-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold">Sincronização 24/7</p>
                      <p className="text-sm text-muted-foreground">Sistema monitora suas contas constantemente</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <CpuChipIcon className="w-6 h-6 text-purple-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold">IA Inteligente</p>
                      <p className="text-sm text-muted-foreground">Aprende com seus padrões e melhora com o tempo</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <BellAlertIcon className="w-6 h-6 text-orange-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold">Alertas Inteligentes</p>
                      <p className="text-sm text-muted-foreground">Notificações para movimentações importantes</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* AI Categorization */}
            <div className="grid lg:grid-cols-2 gap-16 items-center">
              <div className="space-y-6">
                <div className="inline-flex items-center px-3 py-1 bg-purple-500/10 text-purple-400 rounded-full text-sm font-medium">
                  <CpuChipIcon className="h-4 w-4 mr-2" />
                  Inteligência Artificial
                </div>
                <h3 className="text-3xl md:text-4xl font-bold">
                  IA que Pensa pela Sua Empresa
                </h3>
                <p className="text-lg text-muted-foreground leading-relaxed">
                  Nossa inteligência artificial analisa cada transação, identifica padrões 
                  e categoriza automaticamente com 99% de precisão. Economize até 15 horas 
                  por mês eliminando trabalho manual.
                </p>
                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <SparklesIcon className="w-6 h-6 text-purple-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold">Categorização Inteligente</p>
                      <p className="text-sm text-muted-foreground">Identifica fornecedores, tipos de gasto e finalidade</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <CogIcon className="w-6 h-6 text-blue-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold">Aprendizado Contínuo</p>
                      <p className="text-sm text-muted-foreground">Melhora a precisão conforme aprende seus padrões</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <FolderIcon className="w-6 h-6 text-green-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold">Categorias Personalizadas</p>
                      <p className="text-sm text-muted-foreground">Crie categorias específicas do seu negócio</p>
                    </div>
                  </div>
                </div>
              </div>
              <Card className="glass">
                <CardHeader>
                  <CardTitle>Categorias Automáticas</CardTitle>
                  <CardDescription>Exemplos de como nossa IA categoriza suas transações</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-muted/20 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                        <div>
                          <p className="font-semibold text-sm">Fornecedores</p>
                          <p className="text-xs text-muted-foreground">Material de escritório, insumos</p>
                        </div>
                      </div>
                      <Badge variant="secondary" className="text-xs">99%</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-muted/20 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                        <div>
                          <p className="font-semibold text-sm">Vendas/Receita</p>
                          <p className="text-xs text-muted-foreground">PIX, TED, boletos recebidos</p>
                        </div>
                      </div>
                      <Badge variant="secondary" className="text-xs">100%</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-muted/20 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                        <div>
                          <p className="font-semibold text-sm">Impostos</p>
                          <p className="text-xs text-muted-foreground">DAS, FGTS, INSS</p>
                        </div>
                      </div>
                      <Badge variant="secondary" className="text-xs">98%</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-muted/20 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                        <div>
                          <p className="font-semibold text-sm">Pessoal</p>
                          <p className="text-xs text-muted-foreground">Salários, benefícios</p>
                        </div>
                      </div>
                      <Badge variant="secondary" className="text-xs">97%</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Reports and Analytics */}
            <div className="grid lg:grid-cols-2 gap-16 items-center">
              <Card className="glass order-2 lg:order-1">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <DocumentTextIcon className="h-6 w-6 mr-2 text-blue-400" />
                    Relatórios Disponíveis
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-3">
                    <div className="flex items-start space-x-3">
                      <ChartBarIcon className="h-5 w-5 text-blue-400 mt-1" />
                      <div>
                        <p className="font-semibold text-sm">Fluxo de Caixa</p>
                        <p className="text-xs text-muted-foreground">Entradas x saídas com projeções</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <ChartPieIcon className="h-5 w-5 text-green-400 mt-1" />
                      <div>
                        <p className="font-semibold text-sm">Análise por Categoria</p>
                        <p className="text-xs text-muted-foreground">Gastos detalhados por área</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <PresentationChartLineIcon className="h-5 w-5 text-purple-400 mt-1" />
                      <div>
                        <p className="font-semibold text-sm">DRE Automatizado</p>
                        <p className="text-xs text-muted-foreground">Demonstrativo de resultados</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <CalculatorIcon className="h-5 w-5 text-orange-400 mt-1" />
                      <div>
                        <p className="font-semibold text-sm">Reconciliação</p>
                        <p className="text-xs text-muted-foreground">Comparativo banco x contábil</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <div className="space-y-6 order-1 lg:order-2">
                <div className="inline-flex items-center px-3 py-1 bg-blue-500/10 text-blue-400 rounded-full text-sm font-medium">
                  <DocumentTextIcon className="h-4 w-4 mr-2" />
                  Relatórios e Análises
                </div>
                <h3 className="text-3xl md:text-4xl font-bold">
                  Insights que Geram Resultados
                </h3>
                <p className="text-lg text-muted-foreground leading-relaxed">
                  Transforme dados financeiros em decisões estratégicas. Relatórios automáticos, 
                  análises preditivas e insights gerados por IA para você se antecipar ao mercado 
                  e otimizar resultados.
                </p>
                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <CloudArrowDownIcon className="w-6 h-6 text-green-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold">Export Flexível</p>
                      <p className="text-sm text-muted-foreground">Excel, PDF, CSV para contabilidade</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <ClockIcon className="w-6 h-6 text-purple-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold">Tempo Real</p>
                      <p className="text-sm text-muted-foreground">Dados sempre atualizados</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <DocumentCheckIcon className="w-6 h-6 text-blue-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold">Relatórios Personalizados</p>
                      <p className="text-sm text-muted-foreground">Crie relatórios específicos do seu negócio</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* Additional Features */}
      <section className="py-16 bg-muted/20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Recursos Adicionais
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Funcionalidades que completam sua gestão financeira
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <Card className="glass hover-lift transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-green-500/20 border border-green-500/30 rounded-lg flex items-center justify-center mb-4">
                  <UserGroupIcon className="w-6 h-6 text-green-400" />
                </div>
                <CardTitle>Gestão de Equipe</CardTitle>
                <CardDescription>
                  Controle de acessos, permissões por usuário e auditoria de ações.
                  Mantenha sua equipe colaborando com segurança.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="glass hover-lift transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-orange-500/20 border border-orange-500/30 rounded-lg flex items-center justify-center mb-4">
                  <BellAlertIcon className="w-6 h-6 text-orange-400" />
                </div>
                <CardTitle>Alertas Inteligentes</CardTitle>
                <CardDescription>
                  Notificações por email, WhatsApp ou SMS para saldo baixo, 
                  gastos anômalos e oportunidades detectadas.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="glass hover-lift transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-purple-500/20 border border-purple-500/30 rounded-lg flex items-center justify-center mb-4">
                  <PhoneIcon className="w-6 h-6 text-purple-400" />
                </div>
                <CardTitle>Suporte Especializado</CardTitle>
                <CardDescription>
                  Chat, email e videochamada com consultores financeiros 
                  especializados em PMEs brasileiras.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="glass hover-lift transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-blue-500/20 border border-blue-500/30 rounded-lg flex items-center justify-center mb-4">
                  <ShieldCheckIcon className="w-6 h-6 text-blue-400" />
                </div>
                <CardTitle>Backup e Segurança</CardTitle>
                <CardDescription>
                  Backup automático em múltiplos servidores, criptografia de ponta 
                  e conformidade com LGPD e regulações bancárias.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="glass hover-lift transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-red-500/20 border border-red-500/30 rounded-lg flex items-center justify-center mb-4">
                  <StarIcon className="w-6 h-6 text-red-400" />
                </div>
                <CardTitle>Integrações</CardTitle>
                <CardDescription>
                  API aberta para integrar com ERP, sistema contábil, 
                  e-commerce e outras ferramentas do seu negócio.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="glass hover-lift transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-indigo-500/20 border border-indigo-500/30 rounded-lg flex items-center justify-center mb-4">
                  <CogIcon className="w-6 h-6 text-indigo-400" />
                </div>
                <CardTitle>Personalização</CardTitle>
                <CardDescription>
                  Dashboards personalizáveis, métricas específicas do seu segmento 
                  e configurações adaptadas ao seu fluxo de trabalho.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* Getting Started */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">
              Pronto para Começar?
            </h2>
            <p className="text-xl text-muted-foreground mb-8">
              Configure sua conta em menos de 5 minutos e transforme 
              a gestão financeira da sua empresa hoje mesmo.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
              <Button size="lg" asChild className="text-lg px-8 btn-gradient hover-lift">
                <Link href="/pricing">
                  Ver Planos e Preços
                  <ArrowRightIcon className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button variant="outline" size="lg" asChild className="text-lg px-8 hover:bg-muted hover-lift">
                <Link href="/register">
                  Começar Teste Grátis
                </Link>
              </Button>
            </div>

            <div className="grid sm:grid-cols-3 gap-4 text-center text-sm text-muted-foreground">
              <div className="flex items-center justify-center space-x-2">
                <CheckCircleIcon className="h-5 w-5 text-success" />
                <span>14 dias grátis</span>
              </div>
              <div className="flex items-center justify-center space-x-2">
                <CheckCircleIcon className="h-5 w-5 text-success" />
                <span>Sem cartão de crédito</span>
              </div>
              <div className="flex items-center justify-center space-x-2">
                <CheckCircleIcon className="h-5 w-5 text-success" />
                <span>Suporte incluído</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12 bg-card">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="flex items-center space-x-2">
              <Link href="/" className="flex items-center space-x-2">
                <div className="h-8 w-8 rounded-full bg-gradient-primary flex items-center justify-center shadow-md">
                  <BanknotesIcon className="h-4 w-4 text-white" />
                </div>
                <span className="font-semibold text-white">CaixaHub</span>
              </Link>
            </div>
            <div className="flex space-x-6 text-sm text-muted-foreground">
              <Link href="/" className="hover:text-foreground transition-colors">
                Início
              </Link>
              <Link href="/pricing" className="hover:text-foreground transition-colors">
                Planos
              </Link>
              <Link href="/terms" className="hover:text-foreground transition-colors">
                Termos de Uso
              </Link>
              <Link href="/privacy" className="hover:text-foreground transition-colors">
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