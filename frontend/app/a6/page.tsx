"use client";

import { Header } from "@/components/landing-v2/Header";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { CheckCircle2, X, Check, Building2, Bot, LayoutDashboard, FileText, Zap, Shield, Lock, Sparkles, Users } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Footer } from "@/components/landing-v2/Footer";
import Image from "next/image";

const PRICE_ID_197 = process.env.NEXT_PUBLIC_PRICE_197 || "price_1SXwA6AhSWJIUR4PV1BYoKLt";

export default function LandingAutomaticoPage() {
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
                  <div className="inline-flex items-center gap-2 px-4 py-2 bg-muted text-muted-foreground rounded-full text-sm font-medium">
                    <FileText className="w-4 h-4" />
                    Método de 2015
                  </div>
                  <h1 className="text-5xl lg:text-6xl xl:text-7xl font-bold leading-tight">
                    Você ainda exporta extrato em PDF e{" "}
                    <span className="text-primary">cola na planilha?</span>
                  </h1>
                  <p className="text-xl lg:text-2xl text-muted-foreground leading-relaxed">
                    A concorrência já conectou o banco no sistema e vê tudo em tempo real. Open Banking é regulado pelo Banco Central. Seguro e automático.
                  </p>
                </div>

                <div className="space-y-4">
                  {[
                    "Conexão direta com seu banco via Open Banking",
                    "Regulado pelo Banco Central do Brasil",
                    "Transações aparecem automaticamente, categorizadas"
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
                      Automatizar meu financeiro
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
                    src="/landing-images/bank-connect.png"
                    alt="Conexão bancária via Open Banking"
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

        {/* Old vs New Section */}
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
                Dois mundos diferentes
              </h2>
            </motion.div>

            <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6 }}
              >
                <Card className="p-8 h-full border-muted bg-muted/20">
                  <div className="flex items-center gap-3 mb-6">
                    <FileText className="w-10 h-10 text-muted-foreground" />
                    <h3 className="text-2xl font-bold text-muted-foreground">Método Manual</h3>
                  </div>
                  <div className="space-y-4">
                    {[
                      "Baixa PDF do extrato todo mês",
                      "Abre planilha, copia, cola, formata",
                      "Categoriza transação por transação",
                      "Gasta horas em trabalho repetitivo",
                      "Informação sempre desatualizada",
                      "Erro humano em cada etapa"
                    ].map((item, index) => (
                      <div key={index} className="flex items-start gap-3">
                        <X className="w-5 h-5 text-muted-foreground flex-shrink-0 mt-0.5" />
                        <p className="text-muted-foreground">{item}</p>
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
                  <div className="flex items-center gap-3 mb-6">
                    <Zap className="w-10 h-10 text-primary" />
                    <h3 className="text-2xl font-bold text-primary">Open Banking</h3>
                  </div>
                  <div className="space-y-4">
                    {[
                      "Conecta uma vez, dados fluem automaticamente",
                      "Transações aparecem em tempo real",
                      "IA categoriza tudo instantaneamente",
                      "Zero trabalho manual",
                      "Sempre atualizado",
                      "Sem erro humano"
                    ].map((item, index) => (
                      <div key={index} className="flex items-start gap-3">
                        <Check className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                        <p className="text-foreground/90">{item}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              </motion.div>
            </div>
          </div>
        </section>

        {/* What is Open Banking Section */}
        <section className="py-24 bg-background">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="max-w-4xl mx-auto"
            >
              <div className="text-center mb-12">
                <Shield className="w-16 h-16 text-primary mx-auto mb-6" />
                <h2 className="text-4xl lg:text-5xl font-bold mb-6">
                  O que é Open Banking?
                </h2>
              </div>

              <Card className="p-8 border-primary/30">
                <div className="space-y-6 text-lg text-foreground/80">
                  <p>
                    <strong className="text-foreground">Open Banking</strong> é um sistema regulado pelo <strong className="text-foreground">Banco Central do Brasil</strong> que permite você autorizar aplicativos a ler seus dados bancários de forma segura.
                  </p>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <Lock className="w-4 h-4 text-primary" />
                      </div>
                      <div>
                        <p className="font-semibold text-foreground">Somente leitura</p>
                        <p className="text-sm text-muted-foreground">Ninguém pode movimentar seu dinheiro</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <Shield className="w-4 h-4 text-primary" />
                      </div>
                      <div>
                        <p className="font-semibold text-foreground">Regulado pelo Bacen</p>
                        <p className="text-sm text-muted-foreground">Mesmo padrão de segurança dos bancos</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <Users className="w-4 h-4 text-primary" />
                      </div>
                      <div>
                        <p className="font-semibold text-foreground">Você controla</p>
                        <p className="text-sm text-muted-foreground">Autoriza e revoga quando quiser</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <Building2 className="w-4 h-4 text-primary" />
                      </div>
                      <div>
                        <p className="font-semibold text-foreground">+300 bancos</p>
                        <p className="text-sm text-muted-foreground">Nubank, Itaú, Bradesco, Santander e mais</p>
                      </div>
                    </div>
                  </div>
                  <p className="text-center text-muted-foreground">
                    Grandes empresas já usam. Seu concorrente provavelmente também.
                  </p>
                </div>
              </Card>
            </motion.div>
          </div>
        </section>

        {/* Competition Section */}
        <section className="py-24 bg-muted/30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="max-w-4xl mx-auto text-center"
            >
              <h2 className="text-4xl lg:text-5xl font-bold mb-8">
                Enquanto você cola extrato na planilha...
              </h2>
              <p className="text-xl text-muted-foreground mb-12">
                Seu concorrente está vendo o financeiro dele em tempo real, tomando decisões mais rápidas, identificando problemas antes. A vantagem competitiva está na velocidade da informação.
              </p>

              <Card className="p-8 border-primary/50 bg-primary/5">
                <p className="text-2xl font-bold text-primary mb-4">
                  Open Banking não é mais "novidade".
                </p>
                <p className="text-lg text-foreground/80">
                  É o padrão. Quem não usa está ficando para trás.
                </p>
              </Card>
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
              <h2 className="text-4xl lg:text-5xl font-bold mb-4">Simples de conectar</h2>
            </motion.div>

            <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
              {[
                {
                  number: 1,
                  icon: Building2,
                  title: "Selecione seu banco",
                  description: "Nubank, Itaú, Bradesco, Santander, Inter, C6 - mais de 300 bancos disponíveis.",
                  time: "30 segundos"
                },
                {
                  number: 2,
                  icon: Lock,
                  title: "Autorize a leitura",
                  description: "Login seguro no app do banco. Você autoriza somente leitura de transações.",
                  time: "1 minuto"
                },
                {
                  number: 3,
                  icon: Zap,
                  title: "Pronto, automático",
                  description: "Transações aparecem categorizadas. Zero trabalho manual daqui pra frente.",
                  time: "Automático"
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

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="max-w-4xl mx-auto mt-12"
            >
              <div className="relative rounded-2xl overflow-hidden border border-border/50 shadow-xl bg-card">
                <Image
                  src="/landing-images/dashboard.png"
                  alt="Dashboard automatizado"
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
              <h2 className="text-4xl lg:text-5xl font-bold">O que você ganha com automação</h2>
            </motion.div>

            <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
              {[
                "Transações importadas automaticamente em tempo real",
                "Categorização por IA - sem trabalho manual",
                "Consolidação de múltiplas contas bancárias",
                "Dashboard sempre atualizado",
                "Relatórios prontos em 2 cliques",
                "Contas a pagar e receber com projeção de fluxo",
                "Exportação para Excel, PDF e CSV",
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
                    100% Automático
                  </div>
                  <h2 className="text-5xl font-bold mb-4">
                    R$ 197<span className="text-2xl text-muted-foreground">/mês</span>
                  </h2>
                  <p className="text-muted-foreground">Chega de copiar e colar extrato</p>
                </div>

                <div className="space-y-4 mb-8">
                  {[
                    "Conexão automática via Open Banking",
                    "Transações em tempo real",
                    "Categorização por IA",
                    "Dashboard consolidado",
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
                    question: "Open Banking é seguro mesmo?",
                    answer: "Sim. É regulado pelo Banco Central do Brasil desde 2020. Usa a mesma tecnologia de segurança dos próprios bancos. Nenhum app pode movimentar seu dinheiro - só leitura."
                  },
                  {
                    question: "Vocês têm acesso à minha senha do banco?",
                    answer: "Não. A autorização é feita diretamente no app do seu banco. Nós nunca vemos sua senha. O banco é quem valida e envia os dados."
                  },
                  {
                    question: "Posso revogar o acesso quando quiser?",
                    answer: "Sim. Tanto pelo CaixaHub quanto diretamente no seu banco. Você tem controle total."
                  },
                  {
                    question: "Funciona com qual banco?",
                    answer: "Mais de 300 instituições: Nubank, Itaú, Bradesco, Santander, Inter, C6, Sicoob, Sicredi, Caixa, BB e outros."
                  },
                  {
                    question: "Por que não usar só o app do banco?",
                    answer: "App do banco mostra uma conta só. CaixaHub consolida todas as suas contas, categoriza automaticamente, gera relatórios. É gestão financeira, não só extrato."
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
                Chega de exportar PDF e colar na planilha
              </h2>
              <p className="text-2xl text-muted-foreground">
                Open Banking é o presente. Quem não usa está ficando para trás.
              </p>
              <div className="space-y-3">
                <Button
                  size="lg"
                  className="bg-primary hover:bg-primary/90 text-primary-foreground text-lg md:text-xl px-8 md:px-12 py-6 md:py-8 h-auto shadow-[0_0_30px_rgba(57,224,142,0.3)] hover:shadow-[0_0_40px_rgba(57,224,142,0.5)] transition-all duration-300"
                  asChild
                >
                  <a href={`/register?price_id=${PRICE_ID_197}`}>
                    Automatizar agora - 7 dias grátis
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
