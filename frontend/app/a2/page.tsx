"use client";

import { Header } from "@/components/landing-v2/Header";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { CheckCircle2, X, Check, Building2, Bot, LayoutDashboard, CreditCard, Layers, Eye, Sparkles } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Footer } from "@/components/landing-v2/Footer";
import Image from "next/image";

const PRICE_ID_197 = process.env.NEXT_PUBLIC_PRICE_197 || "price_1SXwA6AhSWJIUR4PV1BYoKLt";

export default function LandingContasPage() {
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
                    <Layers className="w-4 h-4" />
                    Dinheiro espalhado = dinheiro perdido
                  </div>
                  <h1 className="text-5xl lg:text-6xl xl:text-7xl font-bold leading-tight">
                    Você tem dinheiro em 5 bancos e{" "}
                    <span className="text-primary">não sabe quanto tem ao todo?</span>
                  </h1>
                  <p className="text-xl lg:text-2xl text-muted-foreground leading-relaxed">
                    Pular de app em app todo dia não é gestão financeira. O CaixaHub consolida tudo num painel só - atualizado em tempo real.
                  </p>
                </div>

                <div className="space-y-4">
                  {[
                    "Todas as contas em um dashboard único",
                    "Saldo total sempre atualizado",
                    "Saiba exatamente quanto sua empresa tem"
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
                      Consolidar minhas contas
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
                    src="/landing-images/bank-accounts.png"
                    alt="Todas as contas bancárias consolidadas"
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

        {/* Pain Visualization Section */}
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
                Sua manhã parece com isso?
              </h2>

              <div className="grid md:grid-cols-2 gap-8">
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6 }}
                >
                  <Card className="p-6 h-full border-destructive/30 bg-destructive/5">
                    <h3 className="text-xl font-bold mb-4 text-destructive">Todo dia você:</h3>
                    <div className="space-y-3">
                      {[
                        "Abre o app do Nubank",
                        "Abre o app do Itaú",
                        "Abre o app do Inter",
                        "Abre o app da conta PJ",
                        "Abre o app do cartão corporativo",
                        "Tenta somar de cabeça...",
                        "Desiste e abre uma planilha"
                      ].map((item, index) => (
                        <div key={index} className="flex items-start gap-3">
                          <X className="w-4 h-4 text-destructive flex-shrink-0 mt-1" />
                          <p className="text-sm text-foreground/80">{item}</p>
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
                  <Card className="p-6 h-full border-primary/50 bg-primary/5">
                    <h3 className="text-xl font-bold mb-4 text-primary">Com CaixaHub você:</h3>
                    <div className="space-y-3">
                      {[
                        "Abre um único dashboard",
                        "Vê o saldo total consolidado",
                        "Vê cada conta separadamente",
                        "Vê todas as transações juntas",
                        "Vê relatórios prontos",
                        "Toma decisão com base em dados reais"
                      ].map((item, index) => (
                        <div key={index} className="flex items-start gap-3">
                          <Check className="w-4 h-4 text-primary flex-shrink-0 mt-1" />
                          <p className="text-sm text-foreground/80">{item}</p>
                        </div>
                      ))}
                    </div>
                  </Card>
                </motion.div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Banks Supported Section */}
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
                +300 bancos conectam no CaixaHub
              </h2>
              <p className="text-xl text-muted-foreground">
                Nubank, Itaú, Bradesco, Santander, Inter, C6, Caixa, BB, Sicoob, Sicredi e mais
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="max-w-4xl mx-auto"
            >
              <div className="relative rounded-2xl overflow-hidden border border-border/50 shadow-xl bg-card">
                <Image
                  src="/landing-images/bank-connect.png"
                  alt="Conexão com múltiplos bancos"
                  width={1200}
                  height={675}
                  className="w-full h-auto"
                />
              </div>
            </motion.div>
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
                Um painel. Controle total.
              </h2>
            </motion.div>

            <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              {[
                {
                  icon: Layers,
                  title: "Saldo consolidado",
                  description: "Soma automática de todas as contas. Veja quanto sua empresa tem no total, em tempo real."
                },
                {
                  icon: CreditCard,
                  title: "Cada conta separada",
                  description: "Filtre por banco, por conta, por período. Compare performance entre contas diferentes."
                },
                {
                  icon: Eye,
                  title: "Visão unificada",
                  description: "Transações de todos os bancos em uma lista só. Busque qualquer movimentação em segundos."
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
                  title: "Conecte todos os bancos",
                  description: "Adicione cada conta que sua empresa usa. PJ, PF, cartão, o que precisar.",
                  time: "2 min por banco"
                },
                {
                  number: 2,
                  icon: Bot,
                  title: "IA organiza tudo",
                  description: "Transações de todos os bancos são categorizadas automaticamente.",
                  time: "Automático"
                },
                {
                  number: 3,
                  icon: LayoutDashboard,
                  title: "Veja tudo junto",
                  description: "Dashboard mostra saldo total, por conta, e todas as movimentações.",
                  time: "Tempo real"
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
              <h2 className="text-4xl lg:text-5xl font-bold">Além da consolidação...</h2>
            </motion.div>

            <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
              {[
                "Categorização automática por IA de todas as transações",
                "Contas a pagar e receber com lembretes",
                "Fluxo de caixa projetado automaticamente",
                "Relatórios DRE e comparativo mensal",
                "Exportação para Excel, PDF e CSV",
                "Open Banking seguro, regulado pelo Banco Central"
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
                    Bancos ilimitados
                  </div>
                  <h2 className="text-5xl font-bold mb-4">
                    R$ 197<span className="text-2xl text-muted-foreground">/mês</span>
                  </h2>
                  <p className="text-muted-foreground">Conecte quantos bancos precisar. Mesmo preço.</p>
                </div>

                <div className="space-y-4 mb-8">
                  {[
                    "Conexão ilimitada de bancos",
                    "Saldo consolidado em tempo real",
                    "Categorização automática por IA",
                    "Dashboard unificado",
                    "Relatórios prontos para exportar",
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
                    question: "Quantos bancos posso conectar?",
                    answer: "Quantos precisar. Não tem limite. PJ, PF, cartão de crédito empresarial - conecta tudo pelo mesmo preço."
                  },
                  {
                    question: "Funciona com qual banco?",
                    answer: "Mais de 300 instituições: Nubank, Itaú, Bradesco, Santander, Inter, C6, Sicoob, Sicredi, Caixa, BB e outros."
                  },
                  {
                    question: "O saldo atualiza em tempo real?",
                    answer: "Sim. Cada vez que você abre o dashboard, os saldos estão atualizados. Transações novas aparecem automaticamente."
                  },
                  {
                    question: "É seguro conectar vários bancos?",
                    answer: "Sim. Cada conexão é feita via Open Banking, regulado pelo Banco Central. Não armazenamos senhas. Ninguém acessa seu dinheiro."
                  },
                  {
                    question: "Posso ver as contas separadamente também?",
                    answer: "Sim. Você vê o saldo total consolidado E pode filtrar por cada banco/conta individualmente."
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
                Chega de pular de app em app
              </h2>
              <p className="text-2xl text-muted-foreground">
                Todas as suas contas em um lugar só. Saldo total na hora. Controle de verdade.
              </p>
              <div className="space-y-3">
                <Button
                  size="lg"
                  className="bg-primary hover:bg-primary/90 text-primary-foreground text-lg md:text-xl px-8 md:px-12 py-6 md:py-8 h-auto shadow-[0_0_30px_rgba(57,224,142,0.3)] hover:shadow-[0_0_40px_rgba(57,224,142,0.5)] transition-all duration-300"
                  asChild
                >
                  <a href={`/register?price_id=${PRICE_ID_197}`}>
                    Consolidar minhas contas - 7 dias grátis
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
