"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { X, Check, CheckCircle2, Building2, Bot, FileSpreadsheet, Sparkles, Zap, Clock, Target, Landmark, TrendingUp, LineChart, Shield, Eye, Gauge } from "lucide-react";
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

// DTR (Dynamic Text Replacement) por ângulo de criativo - GESTORES FINANCEIROS
const DTR_CONFIG = {
  autonomy: {
    headline: "Gestor financeiro que depende de BPO manual não tem controle real",
    subheadline: "O CaixaHub te dá autonomia. Conecta nas contas bancárias, categoriza transações e atualiza seus relatórios automaticamente."
  },
  decision: {
    headline: "Você toma decisão financeira sem saber o saldo real?",
    subheadline: "O CaixaHub mostra seu fluxo de caixa atualizado todo dia. Receitas, despesas e projeções sempre à mão."
  },
  efficiency: {
    headline: "15 horas por mês categorizando extrato manualmente?",
    subheadline: "Esse é o tempo médio que um gestor financeiro perde. O CaixaHub faz em 2 minutos o que levaria sua semana inteira."
  },
  default: {
    headline: "Controle financeiro em tempo real, sem depender de ninguém",
    subheadline: "Conecte seus bancos uma vez. Transações categorizadas, relatórios prontos — você decide com dados atualizados."
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

// Métricas de social proof - GESTORES
const METRICS = [
  { icon: Clock, value: "15h", label: "economia por mês" },
  { icon: Landmark, value: "100+", label: "bancos conectados" },
  { icon: Zap, value: "2 min", label: "para começar" },
  { icon: Target, value: "R$ 450+", label: "economia mensal" }
];

// Benefícios do Hero - GESTORES
const HERO_BENEFITS = [
  "Visão consolidada de todas as contas em tempo real",
  "Categorização 100% automática com IA",
  "Relatórios DRE e fluxo de caixa prontos"
];

function LandingContent() {
  const searchParams = useSearchParams();
  const angle = searchParams.get("a") as keyof typeof DTR_CONFIG | null;

  // Salva o parâmetro de aquisição no localStorage para usar no registro
  useEffect(() => {
    if (angle) {
      localStorage.setItem('acquisition_angle', `gestor_${angle}`);
    } else {
      localStorage.setItem('acquisition_angle', 'gestor_default');
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
                  <span className="hidden sm:inline">Testar 7 dias grátis</span>
                  <span className="sm:hidden">Testar grátis</span>
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
                    <LineChart className="w-4 h-4" />
                    Para Gestores Financeiros
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
                      Testar 7 dias grátis
                    </a>
                  </Button>
                  <p className="text-sm text-muted-foreground">
                    Sem cartão. Cancele quando quiser.
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
                    alt="Dashboard CaixaHub - Controle Financeiro para Gestores"
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

        {/* Problema/Agitação - GESTORES */}
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
                Você reconhece essa situação?
              </h2>

              <Card className="p-5 sm:p-8 border-destructive/30 bg-destructive/5 mb-8">
                <div className="space-y-4">
                  {[
                    "Tomar decisões sem saber o saldo real de todas as contas",
                    "Esperar o BPO fechar o mês pra ver o resultado",
                    "Gastar horas baixando extratos de diferentes bancos",
                    "Categorizar transações manualmente em planilhas",
                    "Não ter visão consolidada do fluxo de caixa",
                    "Depender de terceiros para ter informações básicas"
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
                  O CaixaHub te dá controle total em tempo real.
                </p>
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Como Funciona para Gestores */}
        <section className="py-24 bg-muted/30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold">Como funciona</h2>
            </motion.div>

            <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto mb-12">
              {[
                {
                  number: 1,
                  icon: Building2,
                  title: "Conecte seus bancos",
                  description: "Open Finance regulamentado pelo BC.",
                  detail: "100+ bancos. 2 minutos."
                },
                {
                  number: 2,
                  icon: Bot,
                  title: "Categorização automática",
                  description: "IA classifica cada transação.",
                  detail: "100% automático."
                },
                {
                  number: 3,
                  icon: FileSpreadsheet,
                  title: "Decida com dados reais",
                  description: "DRE, fluxo de caixa, projeções.",
                  detail: "Atualizados todo dia."
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
                  Ver demonstração
                </a>
              </Button>
            </motion.div>
          </div>
        </section>

        {/* Benefícios para o Gestor */}
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
                Por que gestores escolhem o CaixaHub
              </h2>
            </motion.div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
              {[
                {
                  icon: Eye,
                  title: "Visão em tempo real",
                  description: "Saldo consolidado de todas as contas atualizado diariamente. Saiba exatamente quanto tem disponível."
                },
                {
                  icon: Target,
                  title: "Autonomia total",
                  description: "Não dependa de BPO ou terceiros para ter informações. Você decide, não espera."
                },
                {
                  icon: Clock,
                  title: "15 horas de volta por mês",
                  description: "Elimine trabalho manual de extração e categorização. Foque em análise estratégica."
                },
                {
                  icon: Gauge,
                  title: "Decisões com dados reais",
                  description: "Tome decisões financeiras com base em informações atualizadas, não em relatórios do mês passado."
                },
                {
                  icon: TrendingUp,
                  title: "Projeções e tendências",
                  description: "Veja para onde seu fluxo de caixa está indo. Antecipe problemas antes que aconteçam."
                },
                {
                  icon: Shield,
                  title: "Conciliação automática",
                  description: "Transações bancárias conciliadas automaticamente. Sem conferência manual."
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

        {/* Comparativo - Antes vs Depois */}
        <section className="py-24 bg-muted/30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold">
                Seu dia antes e depois do CaixaHub
              </h2>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="max-w-4xl mx-auto"
            >
              <div className="overflow-x-auto">
                <table className="w-full border-collapse bg-card rounded-xl overflow-hidden shadow-lg">
                  <thead>
                    <tr>
                      <th className="text-left p-3 sm:p-6 bg-muted/50"></th>
                      <th className="text-center p-3 sm:p-6 bg-destructive/10 text-destructive font-bold text-sm sm:text-lg">
                        Sem CaixaHub
                      </th>
                      <th className="text-center p-3 sm:p-6 bg-primary/10 text-primary font-bold text-sm sm:text-lg">
                        Com CaixaHub
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { label: "Ver saldo de todas as contas", before: "30 min (login em cada banco)", after: "1 clique" },
                      { label: "Categorizar transações", before: "15h/mês manual", after: "Automático" },
                      { label: "Relatório de fluxo de caixa", before: "Fim do mês", after: "Tempo real" },
                      { label: "Saber o resultado", before: "Esperar o BPO", after: "Imediato" },
                      { label: "Controle", before: "Depende de terceiros", after: "Total autonomia" }
                    ].map((row, index) => (
                      <tr key={index} className="border-t border-border/50">
                        <td className="p-3 sm:p-6 font-semibold text-foreground text-sm sm:text-base">{row.label}</td>
                        <td className="p-3 sm:p-6 text-center text-muted-foreground text-sm sm:text-base">{row.before}</td>
                        <td className="p-3 sm:p-6 text-center text-primary font-semibold text-sm sm:text-base">{row.after}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.3 }}
                className="text-center mt-8"
              >
                <div className="inline-flex items-center gap-2 px-6 py-3 bg-primary/10 text-primary rounded-full text-lg font-bold">
                  <Sparkles className="w-5 h-5" />
                  Economize R$ 450/mês em tempo
                </div>
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Vídeo Demonstração */}
        <section className="py-24 bg-background">
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
                Em menos de 3 minutos, entenda como ter controle total das suas finanças
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
                  Automatizar agora
                </a>
              </Button>
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
                Tudo que você precisa para ter controle
              </h2>
            </motion.div>

            <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
              {[
                {
                  title: "Dashboard consolidado multi-banco",
                  description: "Veja saldo e transações de todos os seus bancos em uma única tela. Itaú, Bradesco, Nubank, Inter - tudo junto, sempre atualizado.",
                  image: "/landing-images/dashboard.png"
                },
                {
                  title: "Categorização inteligente com IA",
                  description: "Cada transação é classificada automaticamente. Sem trabalho manual. A IA aprende com seu negócio e melhora com o tempo.",
                  image: "/landing-images/transactions.png"
                },
                {
                  title: "Relatórios DRE e fluxo de caixa",
                  description: "Relatórios prontos sempre que você precisar. Exporte PDF ou Excel. Compare meses. Veja tendências.",
                  image: "/landing-images/reports.png"
                },
                {
                  title: "Contas a pagar organizadas",
                  description: "Cadastre boletos com OCR (tire foto e pronto). Nunca mais perca um vencimento. Visão clara do que sai.",
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

        {/* Objeções (Accordion) - GESTORES */}
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
                    question: "É seguro conectar minhas contas bancárias?",
                    answer: "Sim. Usamos Open Finance regulamentado pelo Banco Central. Só lemos dados - não temos acesso para movimentar seu dinheiro. É a mesma tecnologia usada pelos maiores bancos digitais do Brasil."
                  },
                  {
                    question: "Funciona com múltiplas empresas?",
                    answer: "Sim. Você pode cadastrar várias empresas e alternar entre elas com um clique. Cada empresa tem seus próprios bancos, categorias e relatórios."
                  },
                  {
                    question: "Preciso parar de usar meu BPO?",
                    answer: "Não necessariamente. O CaixaHub te dá autonomia para ver seus dados em tempo real, mas você pode continuar usando seu BPO para outras funções. Muitos gestores usam como complemento."
                  },
                  {
                    question: "A categorização é realmente automática?",
                    answer: "Sim. Nossa IA categoriza mais de 95% das transações automaticamente. Ela aprende com seu negócio e melhora com o tempo. Você só revisa exceções."
                  },
                  {
                    question: "E se não servir para mim?",
                    answer: "Teste grátis por 7 dias, sem cartão. Se não gostar, não paga nada. Sem pegadinha, sem burocracia."
                  },
                  {
                    question: "Funciona com meu banco?",
                    answer: "Provavelmente sim. Conectamos com 100+ bancos brasileiros: Itaú, Bradesco, Santander, Nubank, Inter, C6, Sicoob, Sicredi, BB, Caixa e a maioria dos regionais."
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
                Tenha controle financeiro de verdade
              </h2>
              <p className="text-xl text-muted-foreground">
                Pare de depender de terceiros. Veja seus dados em tempo real. Decida com autonomia.
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
                      Testar 7 dias grátis
                    </a>
                  </Button>

                  <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-8 text-sm text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-primary" />
                      Sem cartão de crédito
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

export default function GestoresLandingPage() {
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
