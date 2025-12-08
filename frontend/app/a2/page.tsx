"use client";

import { Header } from "@/components/landing-v2/Header";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { CheckCircle2, X, Check, Building2, Bot, LayoutDashboard, Sparkles } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Footer } from "@/components/landing-v2/Footer";
import Image from "next/image";

// Price ID para o plano de R$197 (teste A/B)
const PRICE_ID_197 = process.env.NEXT_PUBLIC_PRICE_197 || "price_1SXwA6AhSWJIUR4PV1BYoKLt";

export default function LandingA2Page() {
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
                  <h1 className="text-5xl lg:text-6xl xl:text-7xl font-bold leading-tight">
                    Um auxiliar financeiro custa{" "}
                    <span className="text-primary">R$ 2.500/mês com encargos.</span>
                  </h1>
                  <p className="text-xl lg:text-2xl text-muted-foreground leading-relaxed">
                    E ainda erra, falta, pede aumento. O CaixaHub faz a parte operacional — categorizar, consolidar, gerar relatório — por R$ 197/mês. Sem CLT, sem dor de cabeça.
                  </p>
                </div>

                <div className="space-y-4">
                  {[
                    "Categorização automática de todas as transações",
                    "Consolidação de múltiplos bancos",
                    "Relatórios prontos em 2 cliques"
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
                  className="flex justify-center lg:justify-start"
                >
                  <Button
                    size="lg"
                    className="bg-primary hover:bg-primary/90 text-primary-foreground text-lg px-8 py-6 h-auto shadow-[0_0_30px_rgba(57,224,142,0.3)] hover:shadow-[0_0_40px_rgba(57,224,142,0.5)] transition-all duration-300"
                    asChild
                  >
                    <a href={`/register?price_id=${PRICE_ID_197}`}>
                      Economizar agora
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
                    alt="Dashboard CaixaHub - Substituição de Auxiliar Financeiro"
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
              <h2 className="text-4xl lg:text-5xl font-bold mb-8 text-center">
                O problema de contratar alguém pra isso
              </h2>

              <div className="text-xl text-muted-foreground leading-relaxed space-y-6">
                <p>
                  Você quer organização financeira. Aí pensa: "vou contratar um auxiliar".
                </p>

                <Card className="p-6">
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span>Salário:</span>
                      <span className="font-semibold text-foreground">R$ 1.800</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>FGTS, INSS, férias, 13º:</span>
                      <span className="font-semibold text-foreground">+R$ 700</span>
                    </div>
                    <div className="flex justify-between items-center border-t pt-3">
                      <span className="font-bold text-foreground">Total real:</span>
                      <span className="font-bold text-destructive text-xl">R$ 2.500/mês</span>
                    </div>
                  </div>
                </Card>

                <p className="text-foreground font-semibold">E aí começa:</p>

                <div className="space-y-3">
                  {[
                    "Erra na categorização",
                    "Falta na segunda-feira",
                    "Pede aumento em 6 meses",
                    "Sai e você precisa treinar outro"
                  ].map((problem, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <X className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
                      <p className="text-foreground/80">{problem}</p>
                    </div>
                  ))}
                </div>

                <p className="text-foreground font-semibold text-center text-2xl pt-4">
                  Pra fazer o quê? Baixar extrato, categorizar transação, montar planilha. Trabalho repetitivo que robô faz melhor.
                </p>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Problem/Solution Section */}
        <section className="py-24 bg-background">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold mb-6">
                R$ 2.500/mês vs R$ 197/mês
              </h2>
            </motion.div>

            <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6 }}
              >
                <Card className="p-8 h-full border-destructive/50 bg-destructive/5">
                  <h3 className="text-2xl font-bold mb-2 text-destructive">AUXILIAR FINANCEIRO</h3>
                  <p className="text-destructive/80 mb-6 text-lg">R$ 2.500 por mês com encargos</p>
                  <div className="space-y-4">
                    {[
                      "Erra, falta, pede aumento",
                      "Você treina e gerencia",
                      "40 horas por semana"
                    ].map((problem, index) => (
                      <div key={index} className="flex items-start gap-3">
                        <X className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
                        <p className="text-foreground/80">{problem}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <Card className="p-8 h-full border-primary/50 bg-primary/5">
                  <h3 className="text-2xl font-bold mb-2 text-primary">CAIXAHUB</h3>
                  <p className="text-primary/80 mb-6 text-lg">R$ 197/mês</p>
                  <div className="space-y-4">
                    {[
                      "Não erra, não falta, não pede aumento",
                      "Zero gestão de pessoas",
                      "Funciona 24/7"
                    ].map((solution, index) => (
                      <div key={index} className="flex items-start gap-3">
                        <Check className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                        <p className="text-foreground/80">{solution}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              </motion.div>
            </div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="text-center mt-12"
            >
              <Button size="lg" className="bg-primary hover:bg-primary/90 text-primary-foreground" asChild>
                <a href={`/register?price_id=${PRICE_ID_197}`}>
                  Economizar agora
                </a>
              </Button>
            </motion.div>
          </div>
        </section>

        {/* How It Works Section */}
        <section className="py-24 bg-muted/30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold mb-4">Automatize a parte operacional</h2>
            </motion.div>

            <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto mb-12">
              {[
                {
                  number: 1,
                  icon: Building2,
                  title: "Conecte seus bancos",
                  description: "Open Banking seguro, regulado pelo Banco Central",
                  time: "2 minutos"
                },
                {
                  number: 2,
                  icon: Bot,
                  title: "IA categoriza automaticamente",
                  description: "Cada transação é classificada: venda, despesa, fornecedor, imposto",
                  time: "Automático"
                },
                {
                  number: 3,
                  icon: LayoutDashboard,
                  title: "Veja relatórios em tempo real",
                  description: "Dashboard completo, exporta Excel, manda pro contador",
                  time: "1 minuto"
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

        {/* Clarity Section */}
        <section className="py-24 bg-background">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="max-w-4xl mx-auto"
            >
              <h2 className="text-4xl lg:text-5xl font-bold mb-8 text-center">
                O que o CaixaHub não faz
              </h2>
              <Card className="p-8">
                <div className="text-xl text-muted-foreground leading-relaxed space-y-6">
                  <p>
                    O CaixaHub automatiza <strong className="text-foreground">organização financeira</strong>. Categorização, consolidação, relatórios.
                  </p>
                  <p>
                    Se você precisa de alguém pra negociar com fornecedor, emitir NF ou ir no banco, ainda vai precisar de gente.
                  </p>
                  <p className="text-foreground font-semibold text-2xl">
                    Mas pra organizar transação e gerar relatório? Paga R$ 197, não R$ 2.500.
                  </p>
                </div>
              </Card>
            </motion.div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="py-24 bg-muted/30">
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
                    Economize mais de R$ 2.300/mês
                  </div>
                  <h2 className="text-5xl font-bold mb-4">
                    R$ 197<span className="text-2xl text-muted-foreground">/mês</span>
                  </h2>
                  <p className="text-muted-foreground">vs R$ 2.500+ de auxiliar financeiro</p>
                </div>

                <div className="space-y-4 mb-8">
                  {[
                    "Conexão ilimitada com bancos",
                    "Categorização automática por IA",
                    "Dashboard consolidado",
                    "Relatórios em Excel/CSV",
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
                      Começar Trial de 7 Dias
                    </a>
                  </Button>
                  <p className="text-center text-sm text-muted-foreground">
                    7 dias grátis • Cancele quando quiser
                  </p>
                </div>
              </Card>
            </motion.div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="py-24 bg-background">
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
                    question: "Mas e se eu precisar de alguém pra outras coisas?",
                    answer: "O CaixaHub substitui a parte operacional — categorizar, consolidar, gerar relatório. Se você precisa de alguém pra tarefas que exigem julgamento humano, contrata pra isso. Mas não paga R$ 2.500 pra alguém copiar extrato pra planilha."
                  },
                  {
                    question: "A categorização é realmente boa?",
                    answer: "Sim. Nossa IA aprende com milhares de transações e melhora constantemente. Você pode ajustar categorias, e o sistema aprende com suas correções."
                  },
                  {
                    question: "E se eu já tiver alguém contratado?",
                    answer: "Não precisa demitir ninguém pra testar. Usa os 7 dias grátis, vê se faz sentido. Se fizer, você libera a pessoa pra tarefas mais estratégicas — ou reduz custo."
                  },
                  {
                    question: "É seguro?",
                    answer: "Sim. Usamos Open Banking regulado pelo Banco Central. Não temos acesso à sua senha. A conexão é criptografada e você pode revogar a qualquer momento."
                  },
                  {
                    question: "Funciona com qualquer banco?",
                    answer: "Funciona com mais de 100 bancos brasileiros: Itaú, Bradesco, Santander, Banco do Brasil, Nubank, Inter, C6, e muitos outros."
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
                Chega de pagar caro por trabalho operacional
              </h2>
              <p className="text-2xl text-muted-foreground">
                Auxiliar financeiro custa R$ 2.500/mês. CaixaHub custa R$ 197.
              </p>
              <Button
                size="lg"
                className="bg-primary hover:bg-primary/90 text-primary-foreground text-lg md:text-xl px-8 md:px-12 py-6 md:py-8 h-auto shadow-[0_0_30px_rgba(57,224,142,0.3)] hover:shadow-[0_0_40px_rgba(57,224,142,0.5)] transition-all duration-300"
                asChild
              >
                <a href={`/register?price_id=${PRICE_ID_197}`}>
                  Começar agora - 7 dias grátis
                </a>
              </Button>
            </motion.div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
