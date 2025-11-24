"use client";

import { Header } from "@/components/landing-v2/Header";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { CheckCircle2, X, Check, Building2, Bot, LayoutDashboard, Quote, Sparkles } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Footer } from "@/components/landing-v2/Footer";
import Image from "next/image";

export default function LandingV3Page() {
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
                    Dono de varejo: cansado de{" "}
                    <span className="text-primary">sistema financeiro que complica tudo?</span>
                  </h1>
                  <p className="text-xl lg:text-2xl text-muted-foreground leading-relaxed">
                    O CaixaHub é simples: conecta o banco, arruma tudo sozinho. Sem complicação.
                  </p>
                </div>

                <div className="space-y-4">
                  {[
                    "Configure em 5 minutos (não em 5 dias)",
                    "Não precisa de treinamento (se usa WhatsApp, sabe usar)",
                    "Sem implantação complexa (conecta e funciona)"
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
                >
                  <Button
                    size="lg"
                    className="bg-primary hover:bg-primary/90 text-primary-foreground text-lg px-8 py-6 h-auto shadow-[0_0_30px_rgba(57,224,142,0.3)] hover:shadow-[0_0_40px_rgba(57,224,142,0.5)] transition-all duration-300"
                    asChild
                  >
                    <a href="https://caixahub.com.br/register" target="_blank" rel="noopener noreferrer">
                      Quero simplicidade
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
                    src="/landing-images/hero-a.png"
                    alt="Interface Simples e Intuitiva do CaixaHub"
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

        {/* Problem/Solution Section */}
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
                Sistema financeiro não deveria ser essa dor de cabeça
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
                  <h3 className="text-2xl font-bold mb-6 text-destructive">SEM CAIXAHUB (sistemas complicados)</h3>
                  <div className="space-y-4">
                    {[
                      "Implantação de 2 semanas com consultor",
                      "Precisa de treinamento para usar",
                      "Mil botões que você nunca vai usar",
                      "Quando dá erro, ninguém sabe resolver"
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
                  <h3 className="text-2xl font-bold mb-6 text-primary">COM CAIXAHUB (simplicidade)</h3>
                  <div className="space-y-4">
                    {[
                      "Configure em 5 minutos sozinho",
                      "Interface intuitiva (você já sabe usar)",
                      "Faz uma coisa muito bem: organiza seu financeiro",
                      "Suporte rápido via WhatsApp"
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
                <a href="https://caixahub.com.br/register" target="_blank" rel="noopener noreferrer">
                  Testar agora
                </a>
              </Button>
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
              <h2 className="text-4xl lg:text-5xl font-bold mb-4">Simplicidade em 3 passos</h2>
              <p className="text-xl text-muted-foreground">Sem implantação. Sem treinamento. Sem complicação.</p>
            </motion.div>

            <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto mb-12">
              {[
                {
                  number: 1,
                  icon: Building2,
                  title: "Conecte seu banco",
                  description: "2 cliques. Open Banking seguro. Pronto.",
                  time: "2 minutos"
                },
                {
                  number: 2,
                  icon: Bot,
                  title: "Sistema arruma sozinho",
                  description: "IA categoriza tudo automaticamente. Você não faz nada.",
                  time: "2 minutos"
                },
                {
                  number: 3,
                  icon: LayoutDashboard,
                  title: "Veja tudo organizado",
                  description: "Dashboard limpo, simples, direto. Você entende na hora.",
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

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center space-y-6"
            >
              <p className="text-2xl font-semibold text-foreground">
                É tão simples que parece mágica. Mas é só tecnologia bem feita.
              </p>
              <Button size="lg" className="bg-primary hover:bg-primary/90 text-primary-foreground" asChild>
                <a href="https://caixahub.com.br/register" target="_blank" rel="noopener noreferrer">
                  Começar agora - 7 dias grátis
                </a>
              </Button>
            </motion.div>
          </div>
        </section>

        {/* Use Case Section */}
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
                Exemplo: Lojista que desistiu de 3 sistemas 'completos'
              </h2>
              <Card className="p-8">
                <p className="text-lg text-muted-foreground mb-6 leading-relaxed">
                  Tentou ContaAzul (complicado demais), Omie (precisa de contador para configurar), sistema local (trava toda hora).
                  Com o CaixaHub: conectou o banco em 5 minutos, tudo funcionou. Simples. Direto. Sem dor de cabeça.
                </p>
                <div className="relative rounded-lg overflow-hidden border border-border/50 bg-muted/30 aspect-video flex items-center justify-center mb-4">
                  <div className="text-center space-y-4">
                    <div className="text-6xl">🎯</div>
                    <p className="text-muted-foreground">Interface limpa e intuitiva do CaixaHub</p>
                  </div>
                </div>
                <p className="text-center text-sm text-muted-foreground mb-6">
                  Interface que você entende sem ler manual
                </p>
                <div className="text-center">
                  <Button size="lg" className="bg-primary hover:bg-primary/90 text-primary-foreground" asChild>
                    <a href="https://caixahub.com.br/register" target="_blank" rel="noopener noreferrer">
                      Quero essa simplicidade
                    </a>
                  </Button>
                </div>
              </Card>
            </motion.div>
          </div>
        </section>

        {/* Testimonials Section */}
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
                Lojistas que trocaram complicação por simplicidade
              </h2>
            </motion.div>

            <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
              {[
                {
                  quote: "Desisti de 2 sistemas porque eram complicados demais. O CaixaHub eu configurei sozinho em 10 minutos. Finalmente algo que funciona.",
                  name: "Roberto Lima",
                  role: "Loja de Materiais"
                },
                {
                  quote: "Meu sistema antigo travava toda hora. Ligava pro suporte e ninguém resolvia. CaixaHub funciona. Simples assim.",
                  name: "Ana Paula",
                  role: "Pet Shop"
                }
              ].map((testimonial, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.2 }}
                >
                  <Card className="p-8 h-full relative">
                    <Quote className="w-10 h-10 text-primary/20 mb-4" />
                    <p className="text-lg text-foreground/90 mb-6 leading-relaxed">
                      "{testimonial.quote}"
                    </p>
                    <div className="flex items-center gap-4">
                      <Avatar>
                        <AvatarFallback className="bg-primary/10 text-primary">
                          {testimonial.name.split(' ').map(n => n[0]).join('')}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-semibold">{testimonial.name}</p>
                        <p className="text-sm text-muted-foreground">{testimonial.role}</p>
                      </div>
                    </div>
                  </Card>
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
                    Oferta Especial
                  </div>
                  <h2 className="text-5xl font-bold mb-4">
                    R$ 97<span className="text-2xl text-muted-foreground">/mês</span>
                  </h2>
                </div>

                <div className="space-y-4 mb-8">
                  {[
                    "Conexão ilimitada com bancos",
                    "Integração de múltiplas contas",
                    "Rastreio de origem de transações",
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
                    <a href="https://caixahub.com.br/register" target="_blank" rel="noopener noreferrer">
                      Começar Trial de 7 Dias
                    </a>
                  </Button>
                  <p className="text-center text-sm text-muted-foreground">
                    7 dias grátis • Cancele quando quiser
                  </p>
                  <p className="text-center text-base text-foreground font-medium">
                    R$ 97/mês por um sistema que funciona. Sem complicação.
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
                    question: "Preciso de treinamento?",
                    answer: "Não. A interface é intuitiva. Se você usa WhatsApp, já sabe usar o CaixaHub."
                  },
                  {
                    question: "Quanto tempo leva a implantação?",
                    answer: "5 minutos. Conecta o banco e já está funcionando. Sem consultor, sem complicação."
                  },
                  {
                    question: "É complicado usar?",
                    answer: "É o oposto. Foi feito para ser simples. Dashboard limpo, direto ao ponto."
                  },
                  {
                    question: "E se eu tiver dúvida?",
                    answer: "Suporte rápido via WhatsApp. Respostas em minutos, não em dias."
                  },
                  {
                    question: "Funciona para minha loja?",
                    answer: "Sim. Qualquer varejo. Se tem conta bancária, funciona."
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
                Chega de sistema complicado
              </h2>
              <p className="text-2xl text-muted-foreground">
                Simples. Direto. Funciona.
              </p>
              <Button
                size="lg"
                className="bg-primary hover:bg-primary/90 text-primary-foreground text-xl px-12 py-8 h-auto shadow-[0_0_30px_rgba(57,224,142,0.3)] hover:shadow-[0_0_40px_rgba(57,224,142,0.5)] transition-all duration-300"
                asChild
              >
                <a href="https://caixahub.com.br/register" target="_blank" rel="noopener noreferrer">
                  Testar CaixaHub Agora
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
