"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Check, CheckCircle2, Building2, Bot, FileSpreadsheet, Zap, Clock, PiggyBank, Landmark, ShieldCheck, TrendingUp, BarChart3 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Footer } from "@/components/landing-v2/Footer";
import Image from "next/image";
import Link from "next/link";
import { BanknotesIcon } from "@heroicons/react/24/outline";
import { Suspense } from "react";

// Price ID para o plano de R$197
const PRICE_ID_197 = process.env.NEXT_PUBLIC_PRICE_197 || "price_1SXwA6AhSWJIUR4PV1BYoKLt";

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

// Métricas de social proof
const METRICS = [
  { icon: Zap, value: "50.000+", label: "transações categorizadas" },
  { icon: Landmark, value: "100+", label: "bancos conectados" },
  { icon: Clock, value: "2 min", label: "para começar" },
  { icon: PiggyBank, value: "R$ 1.300+", label: "economia média/mês" }
];

// Benefícios da solução para varejistas
const SOLUTION_BENEFITS = [
  { icon: Building2, text: "Conexão automática com bancos (em minutos)" },
  { icon: Bot, text: "Categorização inteligente de todas as movimentações" },
  { icon: CheckCircle2, text: "Conciliação automática, sem configuração manual" },
  { icon: TrendingUp, text: "Fluxo de caixa sempre atualizado e confiável" },
  { icon: BarChart3, text: "Dashboards claros, pensados para quem não é contador" },
];

function RetailLandingContent() {
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
                  <span className="hidden sm:inline">Começar teste grátis</span>
                  <span className="sm:hidden">Testar grátis</span>
                </a>
              </Button>
            </div>
          </div>
        </div>
      </motion.header>

      <main className="pt-20">
        {/* SEÇÃO 1 - Hero */}
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
                <div className="space-y-6">
                  <h1 className="text-4xl lg:text-5xl xl:text-6xl font-bold leading-tight">
                    O sistema de organização financeira feito para varejistas que precisam de{" "}
                    <span className="text-primary">previsibilidade e velocidade</span>.
                  </h1>
                  <p className="text-xl lg:text-2xl text-muted-foreground leading-relaxed">
                    O CaixaHub conecta suas contas bancárias e usa inteligência artificial para categorizar, conciliar e organizar seu fluxo de caixa em tempo real — sem planilhas, sem BPO financeiro e sem trabalho manual.
                  </p>
                </div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.4 }}
                  className="flex flex-col items-center lg:items-start"
                >
                  <Button
                    size="lg"
                    className="bg-primary hover:bg-primary/90 text-primary-foreground text-lg px-8 py-6 h-auto shadow-[0_0_30px_rgba(57,224,142,0.3)] hover:shadow-[0_0_40px_rgba(57,224,142,0.5)] transition-all duration-300"
                    asChild
                  >
                    <a href="#demo">
                      Ver como funciona na prática
                    </a>
                  </Button>
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
                    alt="Dashboard CaixaHub - Gestão Financeira para Varejo"
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

        {/* Social Proof - Métricas e Carrossel de Bancos */}
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

        {/* SEÇÃO 2 - Problema */}
        <section className="py-24 bg-background">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="max-w-4xl mx-auto text-center"
            >
              <h2 className="text-4xl lg:text-5xl font-bold mb-6">
                Crescer no varejo não deveria significar{" "}
                <span className="text-destructive">mais bagunça financeira</span>
              </h2>
              <p className="text-xl lg:text-2xl text-muted-foreground leading-relaxed mb-8">
                Se você é varejista, já conhece o problema: quanto mais vendas, mais movimentações bancárias e menos tempo para entender o que realmente está acontecendo no caixa.
              </p>

              <Card className="p-6 sm:p-8 border-destructive/30 bg-destructive/5 max-w-2xl mx-auto">
                <p className="text-xl lg:text-2xl font-semibold text-destructive">
                  BPO financeiro é caro, lento e depende de pessoas.
                </p>
              </Card>
            </motion.div>
          </div>
        </section>

        {/* SEÇÃO 3 - Solução */}
        <section className="py-24 bg-muted/30">
          <div className="container mx-auto px-4">
            <div className="max-w-6xl mx-auto">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6 }}
                className="text-center mb-12"
              >
                <h2 className="text-3xl lg:text-4xl xl:text-5xl font-bold mb-6">
                  O CaixaHub faz em segundos o que hoje custa{" "}
                  <span className="text-primary">tempo, dinheiro e retrabalho</span>.
                </h2>
                <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
                  Um sistema de automação financeira criado para varejistas ocupados.
                </p>
              </motion.div>

              <div className="grid lg:grid-cols-2 gap-12 items-center">
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6 }}
                  className="space-y-6"
                >
                  <p className="text-lg text-foreground font-medium">
                    Você conecta suas contas bancárias e a inteligência artificial faz o resto:
                  </p>

                  <div className="space-y-4">
                    {SOLUTION_BENEFITS.map((benefit, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.4, delay: index * 0.1 }}
                        className="flex items-start gap-4 p-4 rounded-xl bg-card border border-border/50"
                      >
                        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                          <benefit.icon className="w-5 h-5 text-primary" />
                        </div>
                        <p className="text-foreground text-lg pt-1.5">{benefit.text}</p>
                      </motion.div>
                    ))}
                  </div>

                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5, delay: 0.6 }}
                    className="pt-4"
                  >
                    <Button
                      size="lg"
                      className="bg-primary hover:bg-primary/90 text-primary-foreground text-lg px-8 py-6 h-auto shadow-[0_0_30px_rgba(57,224,142,0.3)] hover:shadow-[0_0_40px_rgba(57,224,142,0.5)] transition-all duration-300"
                      asChild
                    >
                      <a href={`/register?price_id=${PRICE_ID_197}`}>
                        Teste agora
                      </a>
                    </Button>
                  </motion.div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.7 }}
                  className="relative"
                >
                  <div className="relative rounded-2xl overflow-hidden border border-border/50 shadow-2xl bg-card">
                    <Image
                      src="/landing-images/transactions.png"
                      alt="Categorização automática de transações"
                      width={600}
                      height={400}
                      className="w-full h-auto"
                    />
                  </div>
                  <div className="absolute -inset-4 bg-primary/10 blur-3xl -z-10 rounded-full" />
                </motion.div>
              </div>
            </div>
          </div>
        </section>

        {/* Vídeo Demonstração */}
        <section id="demo" className="py-24 bg-background">
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
                Em menos de 3 minutos, entenda como configurar e usar todas as funcionalidades
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

              {/* Timestamps/Capítulos */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.3 }}
                className="mt-8 grid sm:grid-cols-2 lg:grid-cols-3 gap-4"
              >
                {[
                  { time: "0:00", title: "Conectar banco", desc: "Open Finance em 2 minutos" },
                  { time: "0:30", title: "Dashboard", desc: "Visão geral das finanças" },
                  { time: "1:00", title: "Transações", desc: "Categorização automática com IA" },
                  { time: "1:30", title: "Contas", desc: "A pagar e a receber" },
                  { time: "2:00", title: "Categorias", desc: "Personalização completa" },
                  { time: "2:30", title: "Relatórios", desc: "Gráficos e comparativos" },
                ].map((chapter, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-3 p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-xs font-mono font-bold flex-shrink-0">
                      {chapter.time}
                    </div>
                    <div>
                      <p className="font-semibold text-sm">{chapter.title}</p>
                      <p className="text-xs text-muted-foreground">{chapter.desc}</p>
                    </div>
                  </div>
                ))}
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Funcionalidades (com screenshots) */}
        <section className="py-24 bg-muted/30 border-t border-border/30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold">
                Tudo que seu varejo precisa
              </h2>
            </motion.div>

            <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
              {[
                {
                  title: "Categorização automática com IA",
                  description: "Cada transação é classificada automaticamente. Vendas, despesas, fornecedores, impostos - tudo separado e organizado.",
                  image: "/landing-images/transactions.png"
                },
                {
                  title: "Contas a pagar com OCR de boletos",
                  description: "Tire foto do boleto, o sistema extrai valor, vencimento e código de barras. Cadastro em segundos.",
                  image: "/landing-images/bills.png"
                },
                {
                  title: "Relatórios e DRE automático",
                  description: "DRE, fluxo de caixa, comparativo mensal. Exporta PDF ou Excel pro seu contador em 2 cliques.",
                  image: "/landing-images/reports.png"
                },
                {
                  title: "Dashboard unificado multi-banco",
                  description: "Veja saldo e transações de todos os seus bancos em uma única tela. Sempre atualizado.",
                  image: "/landing-images/dashboard.png"
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

        {/* SEÇÃO 4 - CTA Secundário */}
        <section className="py-24 bg-gradient-to-br from-primary/10 via-background to-background relative overflow-hidden">
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
                Tenha controle financeiro real{" "}
                <span className="text-primary">sem complicar sua rotina</span>
              </h2>
              <p className="text-xl text-muted-foreground leading-relaxed">
                Se você quer clareza sobre entradas, saídas e fluxo de caixa sem perder tempo nem depender de processos manuais, o CaixaHub foi feito para sua loja.
              </p>

              <Button
                size="lg"
                className="bg-primary hover:bg-primary/90 text-primary-foreground text-lg px-10 py-6 h-auto shadow-[0_0_30px_rgba(57,224,142,0.3)] hover:shadow-[0_0_40px_rgba(57,224,142,0.5)] transition-all duration-300"
                asChild
              >
                <a href={`/register?price_id=${PRICE_ID_197}`}>
                  Testar o CaixaHub agora
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
            </motion.div>
          </div>
        </section>

        {/* SEÇÃO 5 - FAQ */}
        <section className="py-24 bg-background">
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
                    question: "Preciso entender de finanças ou contabilidade para usar o CaixaHub?",
                    answer: "Não. O CaixaHub foi criado justamente para lojistas que não têm tempo nem conhecimento técnico. A plataforma traduz movimentações bancárias em categorias claras e dashboards simples, focados em entender quanto entra, quanto sai e qual é o caixa real."
                  },
                  {
                    question: "O CaixaHub funciona para varejistas com alto volume de transações?",
                    answer: "Sim. Esse é exatamente o perfil ideal. Quanto maior o volume de movimentações, maior o ganho com a automação. O sistema foi projetado para lidar com muitos lançamentos diários sem perder clareza ou exigir esforço adicional do lojista."
                  },
                  {
                    question: "Meus dados bancários ficam seguros?",
                    answer: "Sim. O CaixaHub utiliza conexões seguras e criptografadas, seguindo padrões de segurança usados por grandes instituições financeiras. O sistema não movimenta dinheiro, apenas lê os dados para organização e análise."
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

        {/* CTA Final com Preço */}
        <section className="py-24 bg-gradient-to-br from-primary/20 via-background to-background relative overflow-hidden">
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
                Comece a ver suas finanças com clareza
              </h2>

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
                      Começar teste grátis
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

export default function RetailLandingPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Carregando...</div>
      </div>
    }>
      <RetailLandingContent />
    </Suspense>
  );
}
