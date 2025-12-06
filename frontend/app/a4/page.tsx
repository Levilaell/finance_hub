"use client";

import { Header } from "@/components/landing-v2/Header";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { CheckCircle2, X, Check, Building2, Bot, LayoutDashboard, HelpCircle, TrendingUp, FileSpreadsheet, Sparkles, Target } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Footer } from "@/components/landing-v2/Footer";
import Image from "next/image";

const PRICE_ID_197 = process.env.NEXT_PUBLIC_PRICE_197 || "price_1SXwA6AhSWJIUR4PV1BYoKLt";

export default function LandingClarezaPage() {
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
                    <HelpCircle className="w-4 h-4" />
                    Lucro ou prejuízo?
                  </div>
                  <h1 className="text-5xl lg:text-6xl xl:text-7xl font-bold leading-tight">
                    Final do mês chega e você não sabe se{" "}
                    <span className="text-primary">deu lucro ou prejuízo?</span>
                  </h1>
                  <p className="text-xl lg:text-2xl text-muted-foreground leading-relaxed">
                    Extrato espalhado, planilha desatualizada, categoria errada. O CaixaHub resolve isso em 5 minutos.
                  </p>
                </div>

                <div className="space-y-4">
                  {[
                    "Veja se o mês fechou positivo ou negativo",
                    "Entenda pra onde seu dinheiro está indo",
                    "Relatórios claros, prontos em 2 cliques"
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
                      Ter clareza agora
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
                    src="/landing-images/reports.png"
                    alt="Relatórios claros e organizados"
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

        {/* Chaos Section */}
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
                Reconhece essa situação?
              </h2>

              <div className="space-y-4 mb-12">
                {[
                  "Extrato do banco em um lugar, planilha em outro",
                  "Categorias que você criou há 2 anos e nunca atualizou",
                  "Transações que você não sabe de onde vieram",
                  "Final do mês: soma no papel, não bate, desiste",
                  "Sensação constante de que está vazando dinheiro",
                  "Contador pede relatório e você precisa de 2 dias pra montar"
                ].map((item, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.4, delay: index * 0.1 }}
                  >
                    <Card className="p-4 flex items-center gap-4 border-destructive/30 bg-destructive/5">
                      <X className="w-5 h-5 text-destructive flex-shrink-0" />
                      <span className="text-foreground/90">{item}</span>
                    </Card>
                  </motion.div>
                ))}
              </div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6 }}
                className="text-center"
              >
                <p className="text-2xl font-bold text-foreground mb-2">
                  Isso não é falta de disciplina.
                </p>
                <p className="text-xl text-muted-foreground">
                  É falta de ferramenta certa.
                </p>
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Solution Section */}
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
                Do caos à clareza em 5 minutos
              </h2>
            </motion.div>

            <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              {[
                {
                  icon: Target,
                  title: "Tudo em um lugar",
                  description: "Conecta seus bancos e todas as transações vêm pro mesmo lugar. Acabou a bagunça de arquivos e planilhas."
                },
                {
                  icon: Bot,
                  title: "Categorizado automaticamente",
                  description: "IA categoriza cada transação: venda, despesa, fornecedor, imposto. Você vê onde o dinheiro está indo."
                },
                {
                  icon: TrendingUp,
                  title: "Resultado claro",
                  description: "Dashboard mostra: receitas, despesas, resultado do mês. Lucro ou prejuízo - na hora, sem fazer conta."
                }
              ].map((feature, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.2 }}
                >
                  <Card className="p-8 h-full text-center border-primary/30 bg-primary/5">
                    <feature.icon className="w-12 h-12 text-primary mx-auto mb-4" />
                    <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                    <p className="text-muted-foreground">{feature.description}</p>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Dashboard Preview */}
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
                Abriu o sistema, sabe como está
              </h2>
              <p className="text-xl text-muted-foreground">
                Sem precisar fazer conta, sem abrir planilha, sem perguntar pra ninguém
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
                  src="/landing-images/dashboard.png"
                  alt="Dashboard com clareza total"
                  width={1200}
                  height={675}
                  className="w-full h-auto"
                />
              </div>
            </motion.div>
          </div>
        </section>

        {/* What You See Section */}
        <section className="py-24 bg-background">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold">O que você passa a enxergar</h2>
            </motion.div>

            <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
              {[
                {
                  icon: TrendingUp,
                  title: "Resultado do mês",
                  description: "Receitas menos despesas. Lucro ou prejuízo. Sem precisar fazer conta."
                },
                {
                  icon: FileSpreadsheet,
                  title: "Top categorias de gasto",
                  description: "Onde está indo a maior parte do dinheiro. Fornecedores, impostos, operacional."
                },
                {
                  icon: LayoutDashboard,
                  title: "Evolução do saldo",
                  description: "Gráfico mostrando como seu caixa evoluiu ao longo do tempo."
                },
                {
                  icon: Target,
                  title: "Comparativo mensal",
                  description: "Este mês vs mês passado. Está melhorando ou piorando?"
                }
              ].map((item, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                  <Card className="p-6 h-full">
                    <item.icon className="w-10 h-10 text-primary mb-4" />
                    <h3 className="text-xl font-bold mb-2">{item.title}</h3>
                    <p className="text-muted-foreground">{item.description}</p>
                  </Card>
                </motion.div>
              ))}
            </div>
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
              <h2 className="text-4xl lg:text-5xl font-bold mb-4">Como funciona</h2>
            </motion.div>

            <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
              {[
                {
                  number: 1,
                  icon: Building2,
                  title: "Conecte seus bancos",
                  description: "Open Banking seguro. Transações dos últimos 90 dias importadas automaticamente.",
                  time: "2 minutos"
                },
                {
                  number: 2,
                  icon: Bot,
                  title: "IA categoriza tudo",
                  description: "Cada transação é classificada automaticamente. Você ajusta se quiser, sistema aprende.",
                  time: "Automático"
                },
                {
                  number: 3,
                  icon: LayoutDashboard,
                  title: "Veja com clareza",
                  description: "Dashboard mostra receitas, despesas, resultado. Relatórios prontos em 2 cliques.",
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
        <section className="py-24 bg-background">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold">Além da clareza...</h2>
            </motion.div>

            <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
              {[
                "Consolidação de múltiplas contas bancárias",
                "Contas a pagar e receber com lembretes",
                "Fluxo de caixa projetado automaticamente",
                "Exportação para Excel, PDF e CSV",
                "Open Banking seguro, regulado pelo Banco Central",
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
                    Clareza total
                  </div>
                  <h2 className="text-5xl font-bold mb-4">
                    R$ 197<span className="text-2xl text-muted-foreground">/mês</span>
                  </h2>
                  <p className="text-muted-foreground">Saiba exatamente como está sua empresa</p>
                </div>

                <div className="space-y-4 mb-8">
                  {[
                    "Resultado do mês na hora (lucro/prejuízo)",
                    "Categorização automática por IA",
                    "Dashboard consolidado",
                    "Relatórios DRE e comparativo",
                    "Conexão ilimitada com bancos",
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
                    question: "Preciso fazer alguma coisa manual?",
                    answer: "Quase nada. Você conecta os bancos uma vez, e o sistema faz o resto. A IA categoriza automaticamente. Se quiser ajustar alguma categoria, pode - e o sistema aprende."
                  },
                  {
                    question: "A categorização automática é confiável?",
                    answer: "Sim. Nossa IA foi treinada com milhões de transações brasileiras. Acerta a maioria. Quando erra, você corrige e ela aprende com suas correções."
                  },
                  {
                    question: "Funciona com qual banco?",
                    answer: "Mais de 300 instituições: Nubank, Itaú, Bradesco, Santander, Inter, C6, Sicoob, Sicredi, Caixa, BB e outros."
                  },
                  {
                    question: "É seguro conectar meu banco?",
                    answer: "Sim. Open Banking regulado pelo Banco Central. Não armazenamos senhas. Ninguém acessa seu dinheiro - só leitura de transações."
                  },
                  {
                    question: "Posso exportar relatórios?",
                    answer: "Sim. Exporta em PDF, Excel ou CSV. Manda pro contador, arquiva, usa como quiser."
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
                Chega de não saber se deu lucro ou prejuízo
              </h2>
              <p className="text-2xl text-muted-foreground">
                Clareza total sobre seu financeiro. Em 5 minutos.
              </p>
              <div className="space-y-3">
                <Button
                  size="lg"
                  className="bg-primary hover:bg-primary/90 text-primary-foreground text-lg md:text-xl px-8 md:px-12 py-6 md:py-8 h-auto shadow-[0_0_30px_rgba(57,224,142,0.3)] hover:shadow-[0_0_40px_rgba(57,224,142,0.5)] transition-all duration-300"
                  asChild
                >
                  <a href={`/register?price_id=${PRICE_ID_197}`}>
                    Ter clareza agora - 7 dias grátis
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
