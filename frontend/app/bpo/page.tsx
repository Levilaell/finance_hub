"use client";

import { Header } from "@/components/landing-v2/Header";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { CheckCircle2, X, Check, Building2, Bot, LayoutDashboard, FileSpreadsheet, Calendar, TrendingUp, CreditCard, Shield, Sparkles } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Footer } from "@/components/landing-v2/Footer";
import Image from "next/image";

export default function LandingBPOPage() {
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
                    Todo seu BPO financeiro{" "}
                    <span className="text-primary">em um só lugar</span>
                  </h1>
                  <p className="text-xl lg:text-2xl text-muted-foreground leading-relaxed">
                    Contas a pagar, contas a receber, fluxo de caixa, relatórios - tudo automatizado. Sem planilha, sem esperar ninguém, sem pagar R$ 1.500/mês.
                  </p>
                </div>

                <div className="space-y-4">
                  {[
                    "Conecta no banco e importa tudo automaticamente",
                    "Categoriza cada transação com IA",
                    "Contas a pagar e receber com recorrência",
                    "Fluxo de caixa projetado em tempo real",
                    "Relatórios prontos para exportar"
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
                  transition={{ duration: 0.5, delay: 0.8 }}
                  className="space-y-3"
                >
                  <Button
                    size="lg"
                    className="bg-primary hover:bg-primary/90 text-primary-foreground text-lg px-8 py-6 h-auto shadow-[0_0_30px_rgba(57,224,142,0.3)] hover:shadow-[0_0_40px_rgba(57,224,142,0.5)] transition-all duration-300"
                    asChild
                  >
                    <a href="/register">
                      Começar agora - 7 dias grátis
                    </a>
                  </Button>
                  <p className="text-sm text-muted-foreground">
                    R$ 97/mês após o teste. Cancele quando quiser.
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
                    alt="Dashboard CaixaHub - BPO Financeiro Automatizado"
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

        {/* Comparison Table Section */}
        <section className="py-24 bg-muted/30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold mb-6">
                BPO tradicional vs CaixaHub
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
                <table className="w-full border-collapse">
                  <thead>
                    <tr>
                      <th className="text-left p-4 bg-muted/50 rounded-tl-lg"></th>
                      <th className="text-center p-4 bg-destructive/10 text-destructive font-bold">BPO Tradicional</th>
                      <th className="text-center p-4 bg-primary/10 text-primary font-bold rounded-tr-lg">CaixaHub</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { label: "Preço", traditional: "R$ 1.000 - 3.000/mês", caixahub: "R$ 97/mês" },
                      { label: "Tempo de setup", traditional: "Dias ou semanas", caixahub: "5 minutos" },
                      { label: "Atualização", traditional: "Manual, demora dias", caixahub: "Tempo real, automático" },
                      { label: "Relatórios", traditional: "Pede e espera", caixahub: "Gera na hora, exporta em 2 cliques" },
                      { label: "Depende de", traditional: "Horário de terceiros", caixahub: "Só de você" },
                      { label: "Categorização", traditional: "Humano faz na mão", caixahub: "IA faz em segundos" }
                    ].map((row, index) => (
                      <tr key={index} className="border-b border-border/50">
                        <td className="p-4 font-medium text-foreground">{row.label}</td>
                        <td className="p-4 text-center text-muted-foreground">{row.traditional}</td>
                        <td className="p-4 text-center text-primary font-medium">{row.caixahub}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="text-center mt-12"
            >
              <Button variant="outline" size="lg" asChild>
                <a href="#como-funciona">
                  Ver como funciona ↓
                </a>
              </Button>
            </motion.div>
          </div>
        </section>

        {/* Features Section */}
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
                Tudo que um BPO financeiro faz. Sem o BPO.
              </h2>
            </motion.div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
              {[
                {
                  icon: Calendar,
                  title: "Contas a Pagar",
                  description: "Cadastre despesas fixas, parcelas, boletos. Com recorrência automática (semanal, mensal, anual). Nunca mais esqueça um vencimento.",
                  image: "/landing-images/bills.png"
                },
                {
                  icon: CreditCard,
                  title: "Contas a Receber",
                  description: "Controle vendas a prazo, parcelas de clientes, receitas futuras. Saiba exatamente quanto vai entrar e quando.",
                  image: "/landing-images/bills.png"
                },
                {
                  icon: TrendingUp,
                  title: "Fluxo de Caixa Projetado",
                  description: "Visão dos próximos 12 meses. Veja antes se vai faltar dinheiro. Compare previsto vs realizado.",
                  image: "/landing-images/reports.png"
                },
                {
                  icon: Bot,
                  title: "Extrato Categorizado",
                  description: "Todas as transações do banco, categorizadas automaticamente por IA. Vendas, fornecedores, impostos, despesas - tudo separado.",
                  image: "/landing-images/transactions.png"
                },
                {
                  icon: FileSpreadsheet,
                  title: "Relatórios Completos",
                  description: "DRE, comparativo mensal, evolução de saldo, top categorias. Exporta PDF, Excel ou CSV pro seu contador.",
                  image: "/landing-images/reports.png"
                },
                {
                  icon: Building2,
                  title: "Conexão Bancária Automática",
                  description: "Conecta Nubank, Itaú, Bradesco, Inter e +300 bancos via Open Banking. Regulado pelo Banco Central. Seus dados seguros.",
                  image: "/landing-images/bank-connect.png"
                }
              ].map((feature, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                >
                  <Card className="p-6 h-full">
                    <feature.icon className="w-10 h-10 text-primary mb-4" />
                    <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                    <p className="text-muted-foreground mb-4">{feature.description}</p>
                    {feature.image && (
                      <div className="relative rounded-lg overflow-hidden border border-border/50 mt-4">
                        <Image
                          src={feature.image}
                          alt={feature.title}
                          width={400}
                          height={225}
                          className="w-full h-auto"
                        />
                      </div>
                    )}
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* How It Works Section */}
        <section id="como-funciona" className="py-24 bg-muted/30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold mb-4">De zero a controle total em 5 minutos</h2>
            </motion.div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-6xl mx-auto mb-12">
              {[
                {
                  number: 1,
                  icon: Building2,
                  title: "Conecte seus bancos",
                  description: "Selecione seu banco, faça login seguro via Open Banking. Transações dos últimos 90 dias são importadas automaticamente.",
                  time: "2 minutos"
                },
                {
                  number: 2,
                  icon: Bot,
                  title: "IA organiza tudo",
                  description: "Cada transação é categorizada: venda, despesa, fornecedor, imposto. Você ajusta se quiser.",
                  time: "Automático"
                },
                {
                  number: 3,
                  icon: Calendar,
                  title: "Cadastre contas futuras",
                  description: "Adicione contas a pagar e receber. Configure recorrência. Sistema projeta seu fluxo de caixa.",
                  time: "2 minutos"
                },
                {
                  number: 4,
                  icon: LayoutDashboard,
                  title: "Acompanhe em tempo real",
                  description: "Dashboard mostra tudo: saldo, receitas, despesas, projeções, alertas. Relatórios prontos pra exportar.",
                  time: "Sempre"
                }
              ].map((step, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.15 }}
                >
                  <Card className="p-6 h-full relative overflow-hidden">
                    <div className="absolute top-4 right-4 text-5xl font-bold text-primary/30">
                      {step.number}
                    </div>
                    <step.icon className="w-10 h-10 text-primary mb-4" />
                    <h3 className="text-lg font-bold mb-2">{step.title}</h3>
                    <p className="text-muted-foreground text-sm mb-4">{step.description}</p>
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
              className="max-w-4xl mx-auto"
            >
              <div className="relative rounded-2xl overflow-hidden border border-border/50 shadow-xl bg-card">
                <Image
                  src="/landing-images/bank-connect.png"
                  alt="Conexão bancária simplificada"
                  width={1200}
                  height={675}
                  className="w-full h-auto"
                />
              </div>
            </motion.div>
          </div>
        </section>

        {/* For Who Section */}
        <section className="py-24 bg-background">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold">Ideal para quem:</h2>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="max-w-3xl mx-auto"
            >
              <Card className="p-8">
                <div className="grid md:grid-cols-2 gap-4">
                  {[
                    "Paga caro em BPO e quer reduzir custo",
                    "Está cotando BPO mas quer algo mais simples",
                    "Tem dinheiro em vários bancos e não consegue consolidar",
                    "Perde horas organizando extrato e planilha",
                    "Nunca sabe se o mês fechou positivo ou negativo",
                    "Quer autonomia pra ver o financeiro quando quiser"
                  ].map((item, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <Check className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                      <p className="text-foreground/80">{item}</p>
                    </div>
                  ))}
                </div>
              </Card>
            </motion.div>
          </div>
        </section>

        {/* What We Don't Do Section */}
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
                O que o CaixaHub não faz
              </h2>

              <Card className="p-8 border-muted mb-8">
                <div className="space-y-4 mb-6">
                  {[
                    "Emissão de nota fiscal (você precisa de sistema de NF ou contador)",
                    "Folha de pagamento (você precisa de DP ou contador)",
                    "Obrigações fiscais e contábeis (você precisa de contador)"
                  ].map((item, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <X className="w-5 h-5 text-muted-foreground flex-shrink-0 mt-0.5" />
                      <p className="text-muted-foreground">{item}</p>
                    </div>
                  ))}
                </div>
                <p className="text-foreground leading-relaxed">
                  O CaixaHub é <strong>BPO financeiro, não contábil</strong>. Organizamos seu caixa, não seus impostos. Se você já tem contador, a gente complementa. Se não tem, os relatórios que geramos facilitam a vida dele.
                </p>
              </Card>
            </motion.div>
          </div>
        </section>

        {/* Security Section */}
        <section className="py-24 bg-background">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="max-w-4xl mx-auto text-center"
            >
              <Shield className="w-16 h-16 text-primary mx-auto mb-6" />
              <h2 className="text-4xl lg:text-5xl font-bold mb-8">
                Seus dados bancários estão seguros
              </h2>

              <div className="grid md:grid-cols-2 gap-6 mb-8">
                {[
                  "Conexão via Open Banking - regulado pelo Banco Central",
                  "Não armazenamos suas senhas bancárias",
                  "Criptografia de ponta a ponta",
                  "Mesmo padrão de segurança usado por bancos digitais"
                ].map((item, index) => (
                  <div key={index} className="flex items-center gap-3 text-left">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <Shield className="w-4 h-4 text-primary" />
                    </div>
                    <p className="text-foreground/80">{item}</p>
                  </div>
                ))}
              </div>

              <p className="text-muted-foreground text-lg">
                Usamos a Pluggy, infraestrutura de Open Banking usada por fintechs e bancos. Você autoriza a leitura dos dados, não a movimentação. <strong className="text-foreground">Ninguém acessa seu dinheiro.</strong>
              </p>
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
              className="text-center mb-12"
            >
              <h2 className="text-4xl lg:text-5xl font-bold mb-4">
                Um preço. Tudo incluso.
              </h2>
            </motion.div>

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
                    Plano Único
                  </div>
                  <h2 className="text-5xl font-bold mb-4">
                    R$ 97<span className="text-2xl text-muted-foreground">/mês</span>
                  </h2>
                </div>

                <div className="space-y-4 mb-8">
                  {[
                    "Conexão ilimitada de bancos",
                    "Transações ilimitadas",
                    "Contas a pagar e receber",
                    "Fluxo de caixa projetado",
                    "Relatórios completos",
                    "Categorização com IA",
                    "Exportação PDF/Excel/CSV",
                    "Suporte por chat"
                  ].map((feature, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <Check className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                      <p className="text-foreground/90">{feature}</p>
                    </div>
                  ))}
                </div>

                <div className="space-y-4">
                  <Button size="lg" className="w-full bg-primary hover:bg-primary/90 text-primary-foreground text-lg py-6" asChild>
                    <a href="/register">
                      Começar teste grátis
                    </a>
                  </Button>
                  <p className="text-center text-sm text-muted-foreground">
                    Teste grátis por 7 dias. Cancele quando quiser.
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
                    question: "O CaixaHub substitui meu contador?",
                    answer: "Não. O CaixaHub organiza seu financeiro (caixa, contas, fluxo). Seu contador cuida de impostos, NF e obrigações fiscais. A gente complementa, não substitui."
                  },
                  {
                    question: "É seguro conectar meu banco?",
                    answer: "Sim. Usamos Open Banking regulado pelo Banco Central. Não armazenamos senhas e não temos acesso pra movimentar seu dinheiro. Só leitura."
                  },
                  {
                    question: "Funciona com qual banco?",
                    answer: "Mais de 300 instituições: Nubank, Itaú, Bradesco, Santander, Inter, C6, Sicoob, Sicredi, Caixa, BB e outros."
                  },
                  {
                    question: "Posso cancelar quando quiser?",
                    answer: "Sim. Sem fidelidade, sem multa. Cancela direto no sistema."
                  },
                  {
                    question: "Consigo exportar relatórios pro meu contador?",
                    answer: "Sim. Exporta em PDF, Excel ou CSV. Seu contador recebe tudo organizado."
                  },
                  {
                    question: "Quanto tempo leva pra configurar?",
                    answer: "5 minutos. Conecta o banco, IA categoriza, você já vê o dashboard funcionando."
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
                Seu financeiro no piloto automático
              </h2>
              <p className="text-2xl text-muted-foreground">
                Chega de planilha, de esperar BPO, de não saber quanto tem. Conecta, automatiza, acompanha.
              </p>
              <div className="space-y-3">
                <Button
                  size="lg"
                  className="bg-primary hover:bg-primary/90 text-primary-foreground text-lg md:text-xl px-8 md:px-12 py-6 md:py-8 h-auto shadow-[0_0_30px_rgba(57,224,142,0.3)] hover:shadow-[0_0_40px_rgba(57,224,142,0.5)] transition-all duration-300"
                  asChild
                >
                  <a href="/register">
                    Começar agora - 7 dias grátis
                  </a>
                </Button>
                <p className="text-sm text-muted-foreground">
                  R$ 97/mês após o teste. Cancele quando quiser.
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
