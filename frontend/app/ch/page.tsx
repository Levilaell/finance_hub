"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { X, Check, CheckCircle2, Building2, Bot, FileSpreadsheet, Sparkles, Zap, Clock, PiggyBank, Landmark } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Footer } from "@/components/landing-v2/Footer";
import Image from "next/image";
import Link from "next/link";
import { BanknotesIcon } from "@heroicons/react/24/outline";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

// Price ID para o plano de R$197
const PRICE_ID_197 = process.env.NEXT_PUBLIC_PRICE_197 || "price_1SXwA6AhSWJIUR4PV1BYoKLt";

// DTR (Dynamic Text Replacement) por ângulo de criativo
const DTR_CONFIG = {
  price: {
    headline: "Você paga R$ 1.500/mês pra alguém organizar suas finanças?",
    subheadline: "O CaixaHub faz o mesmo por R$ 197. Conecta no banco. Categoriza sozinho. Relatórios prontos."
  },
  time: {
    headline: "Quantas horas você perde copiando extrato pra planilha?",
    subheadline: "O CaixaHub conecta direto no banco e organiza tudo sozinho. Você só consulta."
  },
  profit: {
    headline: "Você sabe quanto sua empresa lucrou esse mês?",
    subheadline: "O CaixaHub puxa suas transações do banco e monta os relatórios automaticamente."
  },
  result: {
    headline: "Você tem banco, ERP, planilha... mas não consegue ver o resultado?",
    subheadline: "O CaixaHub conecta suas contas e calcula seu lucro automaticamente. Quanto tem. Quanto entra. Quanto sai. Quanto sobra."
  },
  bpo: {
    headline: "BPO financeiro cobra R$ 1.500 pra fazer isso aqui:",
    subheadline: "Baixar extrato. Categorizar transação. Montar relatório. O CaixaHub faz sozinho por R$ 197/mês."
  },
  accountant: {
    headline: "Você só descobre o resultado da empresa quando o contador fecha?",
    subheadline: "O CaixaHub mostra seu lucro real todo dia, não só no fim do mês."
  },
  default: {
    headline: "Gestão financeira da sua empresa no automático",
    subheadline: "Conecte seus bancos uma vez. Transações categorizadas, relatórios prontos — tudo automático."
  }
};

// Logos dos bancos
const BANK_LOGOS = [
  { name: "Itaú", logo: "/banks/itau.svg" },
  { name: "Bradesco", logo: "/banks/bradesco.svg" },
  { name: "Santander", logo: "/banks/santander.svg" },
  { name: "Nubank", logo: "/banks/nubank.svg" },
  { name: "Inter", logo: "/banks/inter.svg" },
  { name: "C6 Bank", logo: "/banks/c6.svg" },
  { name: "Sicoob", logo: "/banks/sicoob.svg" },
  { name: "BB", logo: "/banks/bb.svg" },
];

// Métricas de social proof
const METRICS = [
  { icon: Zap, value: "50.000+", label: "transações categorizadas" },
  { icon: Landmark, value: "100+", label: "bancos conectados" },
  { icon: Clock, value: "2 min", label: "para começar" },
  { icon: PiggyBank, value: "R$ 1.300+", label: "economia média/mês" }
];

// Benefícios do Hero
const HERO_BENEFITS = [
  "Categorização automática de todas as transações",
  "Consolidação de múltiplos bancos em um só lugar",
  "Relatórios e DRE prontos em 2 cliques"
];

function LandingContent() {
  const searchParams = useSearchParams();
  const angle = searchParams.get("a") as keyof typeof DTR_CONFIG | null;

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
                  <span className="hidden sm:inline">Começar teste grátis</span>
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
                <div className="space-y-6">
                  <h1 className="text-5xl lg:text-6xl xl:text-7xl font-bold leading-tight">
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
                      Começar teste grátis
                    </a>
                  </Button>
                  <p className="text-sm text-muted-foreground">
                    7 dias grátis. Cancele quando quiser.
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
                    alt="Dashboard CaixaHub - Gestão Financeira Automatizada"
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

            {/* Bancos */}
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="pt-6 border-t border-border/30"
            >
              <div className="flex flex-col items-center gap-3">
                <span className="text-sm text-muted-foreground">Funciona com:</span>
                <div className="flex flex-wrap justify-center gap-x-4 sm:gap-x-6 gap-y-2">
                  {BANK_LOGOS.map((bank, index) => (
                    <span
                      key={index}
                      className="text-sm sm:text-base font-medium text-muted-foreground/70 hover:text-foreground transition-colors"
                    >
                      {bank.name}
                    </span>
                  ))}
                  <span className="text-sm sm:text-base font-medium text-primary">+100</span>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Problema/Agitação */}
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
                Você reconhece isso?
              </h2>

              <Card className="p-5 sm:p-8 border-destructive/30 bg-destructive/5 mb-8">
                <div className="space-y-4">
                  {[
                    "Baixar extrato de 3 bancos diferentes todo mês",
                    "Copiar transação por transação para a planilha",
                    "Categorizar manualmente centenas de lançamentos",
                    "Descobrir o resultado só quando o contador fecha",
                    "Pagar R$ 1.500/mês para alguém fazer isso por você"
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
                  O CaixaHub elimina tudo isso.
                </p>
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Como Funciona (3 passos) */}
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
                  title: "A IA organiza tudo",
                  description: "Transações categorizadas automaticamente.",
                  detail: "Aprende com seu negócio."
                },
                {
                  number: 3,
                  icon: FileSpreadsheet,
                  title: "Você só consulta",
                  description: "DRE, fluxo de caixa, relatórios.",
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
                  Começar teste grátis
                </a>
              </Button>
            </motion.div>
          </div>
        </section>

        {/* Funcionalidades (com screenshots) */}
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
                Tudo que você precisa
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

        {/* Comparativo de Preço */}
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
                Comparativo de preço
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
                        BPO Tradicional
                      </th>
                      <th className="text-center p-3 sm:p-6 bg-primary/10 text-primary font-bold text-sm sm:text-lg">
                        CaixaHub
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { label: "Preço mensal", traditional: "R$ 1.500", caixahub: "R$ 197" },
                      { label: "Atualização", traditional: "Mensal", caixahub: "Diária" },
                      { label: "Nº de bancos", traditional: "Limitado", caixahub: "100+" },
                      { label: "Relatórios", traditional: "PDF no fim do mês", caixahub: "Tempo real" },
                      { label: "Setup", traditional: "Semanas", caixahub: "2 minutos" }
                    ].map((row, index) => (
                      <tr key={index} className="border-t border-border/50">
                        <td className="p-3 sm:p-6 font-semibold text-foreground text-sm sm:text-base">{row.label}</td>
                        <td className="p-3 sm:p-6 text-center text-muted-foreground text-sm sm:text-base">{row.traditional}</td>
                        <td className="p-3 sm:p-6 text-center text-primary font-semibold text-sm sm:text-base">{row.caixahub}</td>
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
                  Economia de R$ 15.636/ano
                </div>
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Objeções (Accordion) */}
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
                    question: "É seguro conectar minha conta?",
                    answer: "Sim. Usamos Open Finance regulamentado pelo Banco Central. Só lemos dados - não temos acesso para movimentar seu dinheiro. Mesma tecnologia dos grandes bancos digitais."
                  },
                  {
                    question: "Funciona com meu banco?",
                    answer: "Sim. Conectamos com 100+ bancos brasileiros: Itaú, Bradesco, Santander, Nubank, Inter, C6, Sicoob, Sicredi, Caixa, BB e a maioria dos regionais."
                  },
                  {
                    question: "Preciso saber de finanças?",
                    answer: "Não. Conectou, funciona sozinho. A IA categoriza tudo automaticamente. Você só consulta os relatórios prontos."
                  },
                  {
                    question: "E se não servir para mim?",
                    answer: "Teste grátis por 7 dias. Não gostou, não paga nada. Cancele quando quiser, sem multa."
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

export default function CaixaHubLandingPage() {
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
