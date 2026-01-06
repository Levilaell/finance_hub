"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { X, Check, CheckCircle2, Building2, Bot, FileSpreadsheet, Sparkles, Zap, Clock, Users, Landmark, TrendingUp, Calculator, BarChart3, Shield } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Footer } from "@/components/landing-v2/Footer";
import Image from "next/image";
import Link from "next/link";
import { BanknotesIcon } from "@heroicons/react/24/outline";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

// Price ID para o plano de R$197
const PRICE_ID_197 = process.env.NEXT_PUBLIC_PRICE_197 || "price_1SXwA6AhSWJIUR4PV1BYoKLt";

// DTR (Dynamic Text Replacement) por ângulo de criativo - CONTADORES
const DTR_CONFIG = {
  pain: {
    headline: "Contador, você gasta horas categorizando extrato dos seus clientes?",
    subheadline: "O CaixaHub faz isso automaticamente por você. Conecta no banco, categoriza e entrega relatórios prontos para todos os seus clientes."
  },
  escala: {
    headline: "Atenda mais clientes sem aumentar sua equipe",
    subheadline: "O CaixaHub automatiza a categorização e conciliação bancária. Você foca em análise estratégica, não em trabalho operacional."
  },
  diferenciacao: {
    headline: "Ofereça visão financeira em tempo real para seus clientes",
    subheadline: "Enquanto outros contadores entregam relatórios só no fim do mês, você entrega atualização diária automatizada pelo CaixaHub."
  },
  default: {
    headline: "Automatize o financeiro dos seus clientes",
    subheadline: "Conecte os bancos dos seus clientes uma vez. Categorização, conciliação e relatórios — tudo automático."
  }
};

// Bancos suportados via Pluggy CDN
const SUPPORTED_BANKS = [
  { id: 201, name: "Itaú", color: "#EC7000" },
  { id: 202, name: "Bradesco", color: "#CC092F" },
  { id: 204, name: "Santander", color: "#EC0000" },
  { id: 1, name: "Nubank", color: "#820AD1" },
  { id: 208, name: "Inter", color: "#FF7A00" },
  { id: 212, name: "C6 Bank", color: "#242424" },
  { id: 206, name: "Banco do Brasil", color: "#FFEF00" },
  { id: 203, name: "Caixa", color: "#005CA9" },
  { id: 213, name: "Sicoob", color: "#003641" },
  { id: 214, name: "Sicredi", color: "#00A651" },
  { id: 215, name: "BTG Pactual", color: "#001E50" },
  { id: 211, name: "Safra", color: "#00205B" },
  { id: 209, name: "Original", color: "#00A650" },
  { id: 210, name: "PagBank", color: "#00A650" },
];

// Métricas de social proof - CONTADORES
const METRICS = [
  { icon: Users, value: "500+", label: "empresas atendidas" },
  { icon: Landmark, value: "100+", label: "bancos conectados" },
  { icon: Clock, value: "2 min", label: "setup por cliente" },
  { icon: TrendingUp, value: "95%", label: "precisão na categorização" }
];

// Benefícios do Hero - CONTADORES
const HERO_BENEFITS = [
  "Categorização automática com IA para todos os clientes",
  "Relatórios prontos em tempo real, não só no fim do mês",
  "Cada cliente configurado em 2 minutos"
];

function LandingContent() {
  const searchParams = useSearchParams();
  const angle = searchParams.get("a") as keyof typeof DTR_CONFIG | null;

  // Salva o parâmetro de aquisição no localStorage para usar no registro
  useEffect(() => {
    if (angle) {
      localStorage.setItem('acquisition_angle', `contador_${angle}`);
    } else {
      localStorage.setItem('acquisition_angle', 'contador_default');
    }
  }, [angle]);

  // Usa configuração baseada no parâmetro ?a=, fallback para default
  const dtr = DTR_CONFIG[angle || "default"] || DTR_CONFIG.default;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-lg border-b border-border/50"
      >
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-20">
            <Link href="/" className="flex items-center space-x-2">
              <div className="h-10 w-10 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center">
                <BanknotesIcon className="h-6 w-6 text-primary" />
              </div>
              <span className="text-xl font-bold">
                CaixaHub
              </span>
            </Link>

            <div className="flex items-center gap-2 sm:gap-4">
              <Button variant="ghost" size="sm" className="sm:size-default" asChild>
                <a href="/login">Entrar</a>
              </Button>
              <Button
                className="bg-primary hover:bg-primary/90 text-primary-foreground text-sm sm:text-base"
                size="sm"
                asChild
              >
                <a href={`/register?price_id=${PRICE_ID_197}`}>
                  <span className="hidden sm:inline">Ver como funciona</span>
                  <span className="sm:hidden">Ver demo</span>
                </a>
              </Button>
            </div>
          </div>
        </div>
      </motion.header>

      <main className="pt-20">
        {/* Hero Section */}
        <section className="relative min-h-screen flex items-center bg-background overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-muted/20" />

          <div className="container mx-auto px-4 py-20 relative z-10">
            <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="space-y-8"
              >
                {/* Badge de público */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.4 }}
                >
                  <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium border border-primary/20">
                    <Calculator className="w-4 h-4" />
                    Para Escritórios de Contabilidade
                  </span>
                </motion.div>

                <div className="space-y-6">
                  <h1 className="text-4xl lg:text-5xl xl:text-6xl font-bold leading-tight">
                    {dtr.headline}
                  </h1>
                  <p className="text-xl lg:text-2xl text-muted-foreground leading-relaxed">
                    {dtr.subheadline}
                  </p>
                </div>

                <div className="space-y-3">
                  {HERO_BENEFITS.map((benefit, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.4, delay: 0.2 + index * 0.1 }}
                      className="flex items-start gap-3"
                    >
                      <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                      <p className="text-base sm:text-lg text-foreground/90">{benefit}</p>
                    </motion.div>
                  ))}
                </div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.6 }}
                  className="space-y-3 flex flex-col items-center lg:items-start"
                >
                  <Button
                    size="lg"
                    className="bg-primary hover:bg-primary/90 text-primary-foreground text-lg px-8 py-6 h-auto shadow-[0_0_30px_rgba(57,224,142,0.3)] hover:shadow-[0_0_40px_rgba(57,224,142,0.5)] transition-all duration-300"
                    asChild
                  >
                    <a href={`/register?price_id=${PRICE_ID_197}`}>
                      Ver como funciona
                    </a>
                  </Button>
                  <p className="text-sm text-muted-foreground">
                    7 dias grátis. Sem compromisso.
                  </p>
                </motion.div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.7, delay: 0.3 }}
                className="relative"
              >
                <div className="relative rounded-2xl overflow-hidden border border-border/50 shadow-2xl bg-card">
                  <Image
                    src="/landing-images/dashboard.png"
                    alt="Dashboard CaixaHub - Gestão Financeira para Contadores"
                    width={1200}
                    height={675}
                    className="w-full h-auto"
                    priority
                  />
                </div>
                <div className="absolute -inset-4 bg-primary/10 blur-3xl -z-10 rounded-full" />
              </motion.div>
            </div>
          </div>
        </section>

        {/* Social Proof - Métricas */}
        <section className="py-12 bg-muted/30 border-y border-border/30">
          <div className="container mx-auto px-4">
            {/* Métricas */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6 lg:gap-8 mb-8"
            >
              {METRICS.map((metric, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="flex flex-col items-center text-center p-3 sm:p-4"
                >
                  <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-primary/10 flex items-center justify-center mb-2 sm:mb-3">
                    <metric.icon className="w-5 h-5 sm:w-6 sm:h-6 text-primary" />
                  </div>
                  <span className="text-xl sm:text-2xl lg:text-3xl font-bold text-foreground">{metric.value}</span>
                  <span className="text-xs sm:text-sm text-muted-foreground">{metric.label}</span>
                </motion.div>
              ))}
            </motion.div>

            {/* Carrossel de Bancos */}
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="pt-8 border-t border-border/30"
            >
              <p className="text-center text-sm text-muted-foreground mb-6">
                Conecta com mais de 100 bancos brasileiros
              </p>

              {/* Marquee Container */}
              <div className="relative overflow-hidden">
                {/* Gradient Overlays */}
                <div className="absolute left-0 top-0 bottom-0 w-20 bg-gradient-to-r from-muted/30 to-transparent z-10 pointer-events-none" />
                <div className="absolute right-0 top-0 bottom-0 w-20 bg-gradient-to-l from-muted/30 to-transparent z-10 pointer-events-none" />

                {/* Scrolling Track */}
                <div className="flex animate-marquee">
                  {/* First set */}
                  {SUPPORTED_BANKS.map((bank, index) => (
                    <div
                      key={`first-${index}`}
                      className="flex-shrink-0 mx-4 sm:mx-6"
                    >
                      <div
                        className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-card border border-border/50 flex items-center justify-center p-3 hover:scale-110 transition-transform duration-300 shadow-sm"
                        title={bank.name}
                      >
                        <img
                          src={`https://cdn.pluggy.ai/assets/connector-icons/${bank.id}.svg`}
                          alt={bank.name}
                          className="w-full h-full object-contain"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            target.parentElement!.innerHTML = `<span class="text-xl font-bold" style="color: ${bank.color}">${bank.name.charAt(0)}</span>`;
                          }}
                        />
                      </div>
                    </div>
                  ))}
                  {/* Duplicate set for seamless loop */}
                  {SUPPORTED_BANKS.map((bank, index) => (
                    <div
                      key={`second-${index}`}
                      className="flex-shrink-0 mx-4 sm:mx-6"
                    >
                      <div
                        className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-card border border-border/50 flex items-center justify-center p-3 hover:scale-110 transition-transform duration-300 shadow-sm"
                        title={bank.name}
                      >
                        <img
                          src={`https://cdn.pluggy.ai/assets/connector-icons/${bank.id}.svg`}
                          alt={bank.name}
                          className="w-full h-full object-contain"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            target.parentElement!.innerHTML = `<span class="text-xl font-bold" style="color: ${bank.color}">${bank.name.charAt(0)}</span>`;
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <p className="text-center text-xs text-muted-foreground/70 mt-4">
                Itaú • Bradesco • Santander • Nubank • Inter • C6 • BB • Caixa • Sicoob • Sicredi • e mais
              </p>
            </motion.div>
          </div>
        </section>

        {/* Problema/Agitação - CONTADORES */}
        <section className="py-24 bg-background">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="max-w-4xl mx-auto"
            >
              <h2 className="text-4xl lg:text-5xl font-bold mb-12 text-center">
                Essa rotina te soa familiar?
              </h2>

              <Card className="p-5 sm:p-8 border-destructive/30 bg-destructive/5 mb-8">
                <div className="space-y-4">
                  {[
                    "Pedir extrato para cada cliente todo mês",
                    "Baixar PDFs de portais diferentes de cada banco",
                    "Categorizar manualmente milhares de transações",
                    "Responder clientes perguntando 'quanto lucrei esse mês?'",
                    "Entregar relatório só quando fecha o mês",
                    "Perder clientes para quem oferece visão em tempo real"
                  ].map((problem, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.4, delay: index * 0.1 }}
                      className="flex items-start gap-3"
                    >
                      <X className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
                      <p className="text-foreground/80 text-lg">{problem}</p>
                    </motion.div>
                  ))}
                </div>
              </Card>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.5 }}
                className="text-center"
              >
                <p className="text-2xl lg:text-3xl font-bold text-primary">
                  O CaixaHub automatiza tudo isso para você.
                </p>
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Como Funciona para Contadores */}
        <section className="py-24 bg-muted/30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold">Como funciona para contadores</h2>
            </motion.div>

            <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto mb-12">
              {[
                {
                  number: 1,
                  icon: Building2,
                  title: "Conecte os bancos dos clientes",
                  description: "Open Finance regulamentado pelo BC.",
                  detail: "Cada cliente em 2 minutos."
                },
                {
                  number: 2,
                  icon: Bot,
                  title: "A IA categoriza automaticamente",
                  description: "95% de precisão na categorização.",
                  detail: "Aprende com cada negócio."
                },
                {
                  number: 3,
                  icon: FileSpreadsheet,
                  title: "Relatórios prontos sempre",
                  description: "DRE, fluxo de caixa, comparativo.",
                  detail: "Seus clientes veem em tempo real."
                }
              ].map((step, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.2 }}
                >
                  <Card className="p-5 sm:p-8 h-full relative overflow-hidden text-center">
                    <div className="absolute top-4 right-4 text-7xl font-bold text-primary/20">
                      {step.number}
                    </div>
                    <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-6">
                      <step.icon className="w-8 h-8 text-primary" />
                    </div>
                    <h3 className="text-xl font-bold mb-3">{step.title}</h3>
                    <p className="text-muted-foreground mb-2">{step.description}</p>
                    <p className="text-sm text-primary font-medium">{step.detail}</p>
                  </Card>
                </motion.div>
              ))}
            </div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="text-center"
            >
              <Button
                size="lg"
                className="bg-primary hover:bg-primary/90 text-primary-foreground"
                asChild
              >
                <a href={`/register?price_id=${PRICE_ID_197}`}>
                  Testar agora
                </a>
              </Button>
            </motion.div>
          </div>
        </section>

        {/* Benefícios para o Contador */}
        <section className="py-24 bg-background">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold">
                Por que contadores escolhem o CaixaHub
              </h2>
            </motion.div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
              {[
                {
                  icon: TrendingUp,
                  title: "Escale sem contratar",
                  description: "Atenda 2x mais clientes com a mesma equipe. Automatize o operacional e foque em análise estratégica."
                },
                {
                  icon: BarChart3,
                  title: "Diferencie seu escritório",
                  description: "Entregue visão em tempo real enquanto concorrentes só entregam no fim do mês. Seja referência em inovação."
                },
                {
                  icon: Clock,
                  title: "Economize 15h/mês por cliente",
                  description: "Elimine trabalho manual de categorização. A IA faz em segundos o que levaria horas."
                },
                {
                  icon: Shield,
                  title: "Reduza erros e retrabalho",
                  description: "95% de precisão na categorização. Menos correções, mais produtividade."
                },
                {
                  icon: Users,
                  title: "Clientes mais satisfeitos",
                  description: "Seus clientes acessam relatórios 24/7. Menos ligações, menos urgências."
                },
                {
                  icon: Sparkles,
                  title: "Fidelize com tecnologia",
                  description: "Ofereça um diferencial que seus concorrentes não têm. Tecnologia que gera valor."
                }
              ].map((benefit, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                  <Card className="p-6 h-full">
                    <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                      <benefit.icon className="w-6 h-6 text-primary" />
                    </div>
                    <h3 className="text-xl font-bold mb-2">{benefit.title}</h3>
                    <p className="text-muted-foreground">{benefit.description}</p>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Vídeo Demonstração */}
        <section className="py-24 bg-muted/30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-12"
            >
              <h2 className="text-4xl lg:text-5xl font-bold mb-4">
                Veja o CaixaHub em ação
              </h2>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                Em menos de 3 minutos, entenda como configurar clientes e automatizar relatórios
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7 }}
              className="max-w-4xl mx-auto"
            >
              <Card className="overflow-hidden border-border/50 shadow-2xl">
                <div className="relative aspect-video bg-black">
                  <video
                    controls
                    poster="/landing-images/dashboard.png"
                    className="w-full h-full object-contain"
                    preload="metadata"
                  >
                    <source src="/videos/demo.mp4" type="video/mp4" />
                    Seu navegador não suporta vídeos.
                  </video>
                </div>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="text-center mt-12"
            >
              <Button
                size="lg"
                className="bg-primary hover:bg-primary/90 text-primary-foreground"
                asChild
              >
                <a href={`/register?price_id=${PRICE_ID_197}`}>
                  Conhecer na prática
                </a>
              </Button>
            </motion.div>
          </div>
        </section>

        {/* Funcionalidades (com screenshots) */}
        <section className="py-24 bg-background border-t border-border/30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold">
                Ferramentas para seu escritório
              </h2>
            </motion.div>

            <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
              {[
                {
                  title: "Categorização automática com IA",
                  description: "Cada transação dos seus clientes é classificada automaticamente. Vendas, despesas, fornecedores, impostos - tudo separado e organizado.",
                  image: "/landing-images/transactions.png"
                },
                {
                  title: "Multi-empresa em um painel",
                  description: "Gerencie todos os seus clientes em um único lugar. Troque de empresa com um clique. Visão consolidada ou individual.",
                  image: "/landing-images/dashboard.png"
                },
                {
                  title: "Relatórios prontos para seus clientes",
                  description: "DRE, fluxo de caixa, comparativo mensal. Seus clientes acessam em tempo real ou você exporta PDF/Excel.",
                  image: "/landing-images/reports.png"
                },
                {
                  title: "Contas a pagar com OCR",
                  description: "Seus clientes fotografam boletos, o sistema extrai automaticamente. Você tem visão do contas a pagar de todos.",
                  image: "/landing-images/bills.png"
                }
              ].map((feature, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                >
                  <Card className="p-6 h-full flex flex-col">
                    <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                    <p className="text-muted-foreground mb-4 flex-grow">{feature.description}</p>
                    <div className="relative rounded-lg overflow-hidden border border-border/50">
                      <Image
                        src={feature.image}
                        alt={feature.title}
                        width={500}
                        height={280}
                        className="w-full h-auto"
                      />
                    </div>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Objeções (Accordion) - CONTADORES */}
        <section className="py-24 bg-muted/30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold">Perguntas frequentes</h2>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="max-w-3xl mx-auto"
            >
              <Accordion type="single" collapsible className="space-y-4">
                {[
                  {
                    question: "Como funciona para múltiplos clientes?",
                    answer: "Você cadastra cada cliente no CaixaHub e conecta os bancos deles via Open Finance. Cada cliente tem seu próprio ambiente, e você acessa todos de um único painel. Pode alternar entre empresas com um clique."
                  },
                  {
                    question: "Meus clientes precisam fazer algo?",
                    answer: "Apenas autorizar a conexão bancária via Open Finance (leva 2 minutos). Depois disso, tudo é automático. Se quiserem, podem acessar os próprios relatórios em tempo real."
                  },
                  {
                    question: "Integra com meu sistema contábil?",
                    answer: "Sim. Você pode exportar relatórios em PDF ou Excel para importar no seu sistema. Estamos desenvolvendo integrações diretas com os principais ERPs contábeis."
                  },
                  {
                    question: "É seguro conectar as contas dos clientes?",
                    answer: "Sim. Usamos Open Finance regulamentado pelo Banco Central. Só lemos dados - não temos acesso para movimentar dinheiro. Mesma tecnologia dos grandes bancos digitais."
                  },
                  {
                    question: "Qual o investimento?",
                    answer: "R$ 197/mês. Você pode repassar o custo aos clientes ou absorver como diferencial competitivo. 7 dias grátis para testar sem compromisso."
                  },
                  {
                    question: "Funciona com todos os bancos?",
                    answer: "Sim. Conectamos com 100+ bancos brasileiros: Itaú, Bradesco, Santander, Nubank, Inter, C6, Sicoob, Sicredi, Caixa, BB e a maioria dos regionais."
                  }
                ].map((faq, index) => (
                  <AccordionItem key={index} value={`item-${index}`} className="border rounded-lg px-6 bg-card">
                    <AccordionTrigger className="text-left text-lg font-semibold hover:no-underline py-6">
                      {faq.question}
                    </AccordionTrigger>
                    <AccordionContent className="text-muted-foreground pb-6">
                      {faq.answer}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </motion.div>
          </div>
        </section>

        {/* CTA Final */}
        <section id="pricing" className="py-24 bg-gradient-to-br from-primary/20 via-background to-background relative overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,_rgba(74,170,123,0.1)_0%,_transparent_50%)]" />

          <div className="container mx-auto px-4 relative z-10">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="max-w-3xl mx-auto text-center space-y-8"
            >
              <h2 className="text-4xl lg:text-5xl font-bold leading-tight">
                Automatize o financeiro dos seus clientes
              </h2>
              <p className="text-xl text-muted-foreground">
                Diferencie seu escritório. Escale sem contratar. Entregue valor em tempo real.
              </p>

              <Card className="p-6 sm:p-10 border-primary/50 bg-card/50 backdrop-blur">
                <div className="space-y-6">
                  <div>
                    <div className="text-5xl lg:text-6xl font-bold text-foreground">
                      R$ 197<span className="text-2xl text-muted-foreground">/mês</span>
                    </div>
                    <p className="text-muted-foreground mt-2">(menos de R$ 7/dia)</p>
                  </div>

                  <Button
                    size="lg"
                    className="w-full max-w-md bg-primary hover:bg-primary/90 text-primary-foreground text-lg md:text-xl px-8 py-6 h-auto shadow-[0_0_30px_rgba(57,224,142,0.3)] hover:shadow-[0_0_40px_rgba(57,224,142,0.5)] transition-all duration-300"
                    asChild
                  >
                    <a href={`/register?price_id=${PRICE_ID_197}`}>
                      Testar agora
                    </a>
                  </Button>

                  <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-8 text-sm text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-primary" />
                      7 dias grátis
                    </div>
                    <div className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-primary" />
                      Cancele quando quiser
                    </div>
                    <div className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-primary" />
                      Suporte incluso
                    </div>
                  </div>
                </div>
              </Card>
            </motion.div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

export default function ContadoresLandingPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Carregando...</div>
      </div>
    }>
      <LandingContent />
    </Suspense>
  );
}
