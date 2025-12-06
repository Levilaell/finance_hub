"use client";

import { Header } from "@/components/landing-v2/Header";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { CheckCircle2, X, Check, Building2, Bot, LayoutDashboard, Clock, Zap, AlertTriangle, Sparkles, CalendarClock } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Footer } from "@/components/landing-v2/Footer";
import Image from "next/image";

const PRICE_ID_197 = process.env.NEXT_PUBLIC_PRICE_197 || "price_1SXwA6AhSWJIUR4PV1BYoKLt";

export default function LandingAtrasoPage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
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
                  <div className="inline-flex items-center gap-2 px-4 py-2 bg-destructive/10 text-destructive rounded-full text-sm font-medium">
                    <CalendarClock className="w-4 h-4" />
                    30-60 dias de atraso
                  </div>
                  <h1 className="text-5xl lg:text-6xl xl:text-7xl font-bold leading-tight">
                    Seu contador manda o financeiro do mês passado{" "}
                    <span className="text-primary">no final do mês seguinte?</span>
                  </h1>
                  <p className="text-xl lg:text-2xl text-muted-foreground leading-relaxed">
                    Você toma decisão com dado velho. O CaixaHub te mostra o fluxo de caixa em tempo real - não daqui 30 dias.
                  </p>
                </div>

                <div className="space-y-4">
                  {[
                    "Dados atualizados em tempo real",
                    "Fluxo de caixa projetado automaticamente",
                    "Tome decisões com informação de hoje"
                  ].map((benefit, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.5, delay: 0.2 + index * 0.1 }}
                      className="flex items-start gap-3"
                    >
                      <CheckCircle2 className="w-6 h-6 text-primary flex-shrink-0 mt-1" />
                      <p className="text-lg text-foreground/90">{benefit}</p>
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
                      Ver meu financeiro agora
                    </a>
                  </Button>
                  <p className="text-sm text-muted-foreground">
                    7 dias grátis • Cancele quando quiser
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
                    alt="Dashboard em tempo real"
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

        {/* Problem Section */}
        <section className="py-24 bg-muted/30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="max-w-4xl mx-auto"
            >
              <h2 className="text-4xl lg:text-5xl font-bold mb-12 text-center">
                Você está dirigindo olhando pelo retrovisor
              </h2>

              <div className="grid md:grid-cols-2 gap-8 mb-12">
                <Card className="p-8 border-destructive/30 bg-destructive/5">
                  <AlertTriangle className="w-12 h-12 text-destructive mb-4" />
                  <h3 className="text-2xl font-bold mb-4">O problema</h3>
                  <div className="space-y-4 text-foreground/80">
                    <p>Contador fecha o mês em 15-30 dias.</p>
                    <p>Quando você recebe o relatório, já tomou 30 decisões às cegas.</p>
                    <p>Aquela despesa que estourou? Você só descobre 45 dias depois.</p>
                    <p className="font-semibold text-foreground">Isso não é gestão. É arqueologia financeira.</p>
                  </div>
                </Card>

                <Card className="p-8 border-primary/50 bg-primary/5">
                  <Zap className="w-12 h-12 text-primary mb-4" />
                  <h3 className="text-2xl font-bold mb-4">A solução</h3>
                  <div className="space-y-4 text-foreground/80">
                    <p>CaixaHub conecta no banco via Open Banking.</p>
                    <p>Transações aparecem em tempo real, categorizadas.</p>
                    <p>Dashboard sempre atualizado. Zero atraso.</p>
                    <p className="font-semibold text-foreground">Você vê o que está acontecendo AGORA.</p>
                  </div>
                </Card>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Timeline Comparison */}
        <section className="py-24 bg-background">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold mb-4">
                Quando você descobre o que aconteceu?
              </h2>
            </motion.div>

            <div className="max-w-4xl mx-auto">
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr>
                      <th className="text-left p-4 bg-muted/50 rounded-tl-lg">Evento</th>
                      <th className="text-center p-4 bg-destructive/10 text-destructive font-bold">Método tradicional</th>
                      <th className="text-center p-4 bg-primary/10 text-primary font-bold rounded-tr-lg">CaixaHub</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { event: "Cliente pagou uma fatura", traditional: "Vê no extrato em 2-3 dias", caixahub: "Instantâneo" },
                      { event: "Despesa inesperada apareceu", traditional: "Descobre no fechamento do mês", caixahub: "Aparece na hora" },
                      { event: "Categoria estourou orçamento", traditional: "30-45 dias depois", caixahub: "Alerta em tempo real" },
                      { event: "Precisa do relatório mensal", traditional: "Pede e espera dias", caixahub: "2 cliques, pronto" },
                      { event: "Quer saber o saldo atual", traditional: "Abre cada app de banco", caixahub: "Dashboard consolidado" }
                    ].map((row, index) => (
                      <motion.tr
                        key={index}
                        initial={{ opacity: 0, y: 10 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.3, delay: index * 0.1 }}
                        className="border-b border-border/50"
                      >
                        <td className="p-4 font-medium text-foreground">{row.event}</td>
                        <td className="p-4 text-center text-muted-foreground">{row.traditional}</td>
                        <td className="p-4 text-center text-primary font-medium">{row.caixahub}</td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-24 bg-muted/30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold mb-4">
                Informação em tempo real muda tudo
              </h2>
            </motion.div>

            <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              {[
                {
                  icon: Zap,
                  title: "Transações instantâneas",
                  description: "Cada movimentação aparece no momento que acontece. Sem esperar ninguém processar."
                },
                {
                  icon: Clock,
                  title: "Fluxo de caixa projetado",
                  description: "Veja não só o que aconteceu, mas o que VAI acontecer. Contas a pagar e receber projetadas."
                },
                {
                  icon: LayoutDashboard,
                  title: "Dashboard sempre atual",
                  description: "Abriu o sistema, está atualizado. Não precisa pedir relatório pra ninguém."
                }
              ].map((feature, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.2 }}
                >
                  <Card className="p-8 h-full text-center">
                    <feature.icon className="w-12 h-12 text-primary mx-auto mb-4" />
                    <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                    <p className="text-muted-foreground">{feature.description}</p>
                  </Card>
                </motion.div>
              ))}
            </div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="max-w-4xl mx-auto mt-12"
            >
              <div className="relative rounded-2xl overflow-hidden border border-border/50 shadow-xl bg-card">
                <Image
                  src="/landing-images/reports.png"
                  alt="Relatórios em tempo real"
                  width={1200}
                  height={675}
                  className="w-full h-auto"
                />
              </div>
            </motion.div>
          </div>
        </section>

        {/* How It Works Section */}
        <section className="py-24 bg-background">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold mb-4">Como funciona</h2>
            </motion.div>

            <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
              {[
                {
                  number: 1,
                  icon: Building2,
                  title: "Conecte seus bancos",
                  description: "Open Banking seguro, regulado pelo Banco Central. Seus dados em tempo real.",
                  time: "2 minutos"
                },
                {
                  number: 2,
                  icon: Bot,
                  title: "IA categoriza tudo",
                  description: "Transações aparecem categorizadas automaticamente. Zero trabalho manual.",
                  time: "Automático"
                },
                {
                  number: 3,
                  icon: LayoutDashboard,
                  title: "Veja tudo em tempo real",
                  description: "Dashboard mostra o que está acontecendo AGORA. Não o que aconteceu há 30 dias.",
                  time: "Instantâneo"
                }
              ].map((step, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.2 }}
                >
                  <Card className="p-8 h-full relative overflow-hidden">
                    <div className="absolute top-4 right-4 text-6xl font-bold text-primary/30">
                      {step.number}
                    </div>
                    <step.icon className="w-12 h-12 text-primary mb-4" />
                    <h3 className="text-xl font-bold mb-3">{step.title}</h3>
                    <p className="text-muted-foreground mb-4">{step.description}</p>
                    <div className="inline-block px-3 py-1 bg-primary/10 text-primary rounded-full text-sm font-medium">
                      {step.time}
                    </div>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* More Features Section */}
        <section className="py-24 bg-muted/30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold">E mais...</h2>
            </motion.div>

            <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
              {[
                "Consolidação de múltiplas contas em um painel",
                "Contas a pagar e receber com projeção de fluxo",
                "Relatórios DRE e comparativo mensal",
                "Exportação para Excel, PDF e CSV",
                "Categorização automática por IA",
                "Suporte via WhatsApp"
              ].map((feature, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="flex items-start gap-3"
                >
                  <Check className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                  <p className="text-foreground/90">{feature}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="py-24 bg-background">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="max-w-2xl mx-auto"
            >
              <Card className="p-10 relative overflow-hidden border-primary/50">
                <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 rounded-full -translate-y-16 translate-x-16" />

                <div className="text-center mb-8">
                  <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-full text-sm font-medium mb-4">
                    <Sparkles className="w-4 h-4" />
                    Tempo real, não tempo velho
                  </div>
                  <h2 className="text-5xl font-bold mb-4">
                    R$ 197<span className="text-2xl text-muted-foreground">/mês</span>
                  </h2>
                  <p className="text-muted-foreground">Decisões baseadas em dados de hoje, não de 30 dias atrás</p>
                </div>

                <div className="space-y-4 mb-8">
                  {[
                    "Dados em tempo real",
                    "Conexão ilimitada com bancos",
                    "Categorização automática por IA",
                    "Fluxo de caixa projetado",
                    "Relatórios prontos em 2 cliques",
                    "Suporte via WhatsApp"
                  ].map((feature, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <Check className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                      <p className="text-foreground/90">{feature}</p>
                    </div>
                  ))}
                </div>

                <div className="space-y-4">
                  <Button size="lg" className="w-full bg-primary hover:bg-primary/90 text-primary-foreground text-lg py-6" asChild>
                    <a href={`/register?price_id=${PRICE_ID_197}`}>
                      Começar - 7 dias grátis
                    </a>
                  </Button>
                  <p className="text-center text-sm text-muted-foreground">
                    Teste grátis por 7 dias • Cancele quando quiser
                  </p>
                </div>
              </Card>
            </motion.div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="py-24 bg-muted/30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold">Perguntas Frequentes</h2>
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
                    question: "Quão 'tempo real' é o tempo real?",
                    answer: "As transações aparecem assim que o banco as processa. Na maioria dos casos, em minutos. Muito melhor que esperar 30-45 dias pelo fechamento do contador."
                  },
                  {
                    question: "Isso substitui meu contador?",
                    answer: "Não. O CaixaHub organiza seu financeiro operacional (caixa, transações, fluxo). Seu contador cuida de impostos e obrigações fiscais. A gente complementa - e ainda facilita o trabalho dele com relatórios prontos."
                  },
                  {
                    question: "Funciona com qual banco?",
                    answer: "Mais de 300 instituições: Nubank, Itaú, Bradesco, Santander, Inter, C6, Sicoob, Sicredi, Caixa, BB e outros."
                  },
                  {
                    question: "É seguro?",
                    answer: "Sim. Open Banking regulado pelo Banco Central. Não armazenamos senhas. Ninguém acessa seu dinheiro - só leitura de transações."
                  },
                  {
                    question: "Posso exportar relatórios pro contador?",
                    answer: "Sim. Exporta em PDF, Excel ou CSV. Seu contador recebe tudo organizado, categorizado, pronto pra usar."
                  }
                ].map((faq, index) => (
                  <AccordionItem key={index} value={`item-${index}`} className="border rounded-lg px-6">
                    <AccordionTrigger className="text-left text-lg font-semibold hover:no-underline">
                      {faq.question}
                    </AccordionTrigger>
                    <AccordionContent className="text-muted-foreground">
                      {faq.answer}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </motion.div>
          </div>
        </section>

        {/* Final CTA Section */}
        <section className="py-24 bg-gradient-to-br from-primary/20 via-background to-background relative overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,_rgba(74,170,123,0.1)_0%,_transparent_50%)]" />

          <div className="container mx-auto px-4 relative z-10">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="max-w-4xl mx-auto text-center space-y-8"
            >
              <h2 className="text-5xl lg:text-6xl font-bold leading-tight">
                Chega de tomar decisão com dado velho
              </h2>
              <p className="text-2xl text-muted-foreground">
                Seu financeiro em tempo real. Não daqui 30 dias.
              </p>
              <div className="space-y-3">
                <Button
                  size="lg"
                  className="bg-primary hover:bg-primary/90 text-primary-foreground text-lg md:text-xl px-8 md:px-12 py-6 md:py-8 h-auto shadow-[0_0_30px_rgba(57,224,142,0.3)] hover:shadow-[0_0_40px_rgba(57,224,142,0.5)] transition-all duration-300"
                  asChild
                >
                  <a href={`/register?price_id=${PRICE_ID_197}`}>
                    Ver meu financeiro agora - 7 dias grátis
                  </a>
                </Button>
                <p className="text-sm text-muted-foreground">
                  R$ 197/mês após o teste. Cancele quando quiser.
                </p>
              </div>
            </motion.div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
