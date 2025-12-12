"use client";

import { Header } from "@/components/landing-v2/Header";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { CheckCircle2, X, Check, Building2, Bot, LayoutDashboard, Sparkles, Zap, Clock, PiggyBank, Landmark } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Footer } from "@/components/landing-v2/Footer";
import Image from "next/image";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

// Price ID para o plano de R$197 (teste A/B)
// Fallback para o price_id de produção caso a env var não esteja configurada
const PRICE_ID_197 = process.env.NEXT_PUBLIC_PRICE_197 || "price_1SXwA6AhSWJIUR4PV1BYoKLt";

// Configuração de DTR (Dynamic Text Replacement)
const DTR_CONFIG = {
  bpo: {
    headline: "Você está pagando R$ 1.500/mês pra alguém",
    headlineHighlight: "categorizar seu extrato?",
    subheadline: "A maior parte do trabalho de BPO financeiro é organizar transações. O CaixaHub faz isso com IA por R$ 197/mês."
  },
  banks: {
    headline: "Tem dinheiro em mais de um banco PJ e perde tempo",
    headlineHighlight: "consolidando extrato?",
    subheadline: "O CaixaHub conecta todos os seus bancos PJ e consolida automaticamente. Categorização por IA, R$ 197/mês."
  },
  pdf: {
    headline: "Ainda exporta extrato em PDF e",
    headlineHighlight: "joga na planilha?",
    subheadline: "O CaixaHub puxa seus extratos via Open Banking e categoriza tudo automaticamente. Sem PDF, sem planilha."
  },
  auto: {
    headline: "E se seu BPO financeiro funcionasse",
    headlineHighlight: "no automático?",
    subheadline: "O CaixaHub automatiza categorização, consolidação e relatórios. Sem depender de terceiros, sem esperar relatório."
  }
};

// Bancos suportados
const SUPPORTED_BANKS = [
  "Itaú", "Bradesco", "Santander", "Banco do Brasil", "Caixa",
  "Nubank", "Inter", "Sicoob", "Sicredi"
];

// Métricas de social proof
const METRICS = [
  { icon: Zap, value: "50.000+", label: "transações categorizadas" },
  { icon: Landmark, value: "+100", label: "bancos suportados" },
  { icon: Clock, value: "3 min", label: "setup completo" },
  { icon: PiggyBank, value: "R$ 1.300+", label: "economia média/mês" }
];

// Benefícios reescritos com foco em outcomes
const PRICING_BENEFITS = [
  "Conecte Itaú, Bradesco, Nubank, Inter... todos num único lugar",
  "Veja todas as suas contas PJ em um único dashboard",
  "Saiba exatamente de onde veio cada entrada e saída",
  "Nunca mais categorize transação manualmente",
  "Clareza financeira em tempo real, não em dias",
  "Exporte e mande pro contador em 2 cliques",
  "Dúvidas? Resposta em minutos no WhatsApp"
];

function LandingContent() {
  const searchParams = useSearchParams();
  const angle = searchParams.get("angle") as keyof typeof DTR_CONFIG | null;

  // Usa configuração baseada no parâmetro angle, default é 'bpo'
  const dtr = DTR_CONFIG[angle || "bpo"] || DTR_CONFIG.bpo;

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
                    {dtr.headline}{" "}
                    <span className="text-primary">{dtr.headlineHighlight}</span>
                  </h1>
                  <p className="text-xl lg:text-2xl text-muted-foreground leading-relaxed">
                    {dtr.subheadline}
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
                      Testar 7 dias grátis
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
                    src="/landing-images/bank-accounts.png"
                    alt="CaixaHub - Múltiplas contas bancárias PJ conectadas"
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

        {/* Social Proof Numbers Section */}
        <section className="py-12 bg-background border-y border-border/30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="grid grid-cols-2 md:grid-cols-4 gap-6 lg:gap-8"
            >
              {METRICS.map((metric, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="flex flex-col items-center text-center p-4"
                >
                  <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-3">
                    <metric.icon className="w-6 h-6 text-primary" />
                  </div>
                  <span className="text-2xl lg:text-3xl font-bold text-foreground">{metric.value}</span>
                  <span className="text-sm text-muted-foreground">{metric.label}</span>
                </motion.div>
              ))}
            </motion.div>

            {/* Supported Banks */}
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="mt-8 pt-8 border-t border-border/30"
            >
              <div className="flex flex-col items-center gap-3">
                <span className="text-sm text-muted-foreground">Funciona com:</span>
                <div className="flex flex-wrap justify-center gap-x-4 gap-y-2">
                  {SUPPORTED_BANKS.map((bank, index) => (
                    <span
                      key={index}
                      className="text-sm font-medium text-muted-foreground/70 hover:text-foreground transition-colors"
                    >
                      {bank}
                    </span>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Provocation Section */}
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
                Você sabe pelo que está pagando?
              </h2>
              <div className="text-xl text-muted-foreground leading-relaxed space-y-6 text-left">
                <p>
                  BPO financeiro tradicional cobra <strong className="text-foreground">R$ 1.000 a R$ 3.000 por mês</strong>.
                </p>
                <p>
                  Sabe o que consome 80% desse tempo? Baixar extrato, categorizar transação por transação, organizar em planilha, montar relatório.
                </p>
                <p className="text-foreground font-semibold">
                  Isso não é trabalho estratégico. É trabalho repetitivo. E trabalho repetitivo se automatiza.
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
                R$ 1.500/mês vs R$ 197/mês
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
                  <h3 className="text-2xl font-bold mb-6 text-destructive">BPO TRADICIONAL</h3>
                  <div className="space-y-4">
                    {[
                      "R$ 1.500+ por mês",
                      "Relatório demora dias",
                      "Você depende do horário deles",
                      "Paga por trabalho manual"
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
                  <h3 className="text-2xl font-bold mb-6 text-primary">CAIXAHUB</h3>
                  <div className="space-y-4">
                    {[
                      "R$ 197/mês",
                      "Tempo real, sempre atualizado",
                      "Acessa quando quiser",
                      "IA faz em segundos o que humano faz em horas"
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
                  Começar trial gratuito
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
              <h2 className="text-4xl lg:text-5xl font-bold mb-4">Automatize o que não precisa de humano</h2>
            </motion.div>

            <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto mb-12">
              {[
                {
                  number: 1,
                  icon: Building2,
                  title: "Conecte seus bancos",
                  description: "Open Banking seguro, regulado pelo Banco Central",
                  time: "2 minutos",
                  image: "/landing-images/bank-connect.png",
                  imageAlt: "Modal do Pluggy com bancos empresariais"
                },
                {
                  number: 2,
                  icon: Bot,
                  title: "IA categoriza automaticamente",
                  description: "Cada transação é classificada: venda, despesa, fornecedor, imposto",
                  time: "Automático",
                  image: "/landing-images/transactions.png",
                  imageAlt: "Lista de transações categorizadas"
                },
                {
                  number: 3,
                  icon: LayoutDashboard,
                  title: "Veja relatórios em tempo real",
                  description: "Dashboard completo, exporta Excel, manda pro contador",
                  time: "1 minuto",
                  image: "/landing-images/reports.png",
                  imageAlt: "Gráfico de receitas vs despesas"
                }
              ].map((step, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.2 }}
                >
                  <Card className="p-6 h-full relative overflow-hidden">
                    <div className="absolute top-4 right-4 text-6xl font-bold text-primary/30">
                      {step.number}
                    </div>
                    <step.icon className="w-10 h-10 text-primary mb-4" />
                    <h3 className="text-xl font-bold mb-2">{step.title}</h3>
                    <p className="text-muted-foreground text-sm mb-4">{step.description}</p>

                    {/* Screenshot thumbnail */}
                    <div className="relative rounded-lg overflow-hidden border border-border/50 mb-4 aspect-video">
                      <Image
                        src={step.image}
                        alt={step.imageAlt}
                        fill
                        className="object-cover object-top"
                        sizes="(max-width: 768px) 100vw, 33vw"
                      />
                    </div>

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
                O que você ainda pode precisar de humano
              </h2>
              <Card className="p-8">
                <div className="text-xl text-muted-foreground leading-relaxed space-y-6">
                  <p>
                    O CaixaHub automatiza a <strong className="text-foreground">organização financeira</strong>. Categorização, consolidação, relatórios.
                  </p>
                  <p>
                    Se você precisa de emissão de NF, folha de pagamento ou contabilidade fiscal, ainda vai precisar de contador.
                  </p>
                  <p className="text-foreground font-semibold text-2xl">
                    Mas pra clareza financeira? Paga R$ 197, não R$ 1.500.
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
                    Economize mais de R$ 1.300/mês
                  </div>
                  <h2 className="text-5xl font-bold mb-4">
                    R$ 197<span className="text-2xl text-muted-foreground">/mês</span>
                  </h2>
                  <p className="text-muted-foreground">vs R$ 1.500+ do BPO tradicional</p>
                </div>

                <div className="space-y-4 mb-8">
                  {PRICING_BENEFITS.map((benefit, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <Check className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                      <p className="text-foreground/90">{benefit}</p>
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
                    question: "Como a IA é tão mais barata que BPO?",
                    answer: "BPO cobra pelo tempo de humanos fazendo trabalho repetitivo. IA faz o mesmo trabalho em segundos, automaticamente. Sem horas de trabalho manual."
                  },
                  {
                    question: "A categorização é realmente boa?",
                    answer: "Sim. Nossa IA aprende com milhares de transações e melhora constantemente. Você pode ajustar categorias, e o sistema aprende com suas correções."
                  },
                  {
                    question: "Preciso cancelar meu BPO?",
                    answer: "Não necessariamente. Se você precisa de NF, folha e contabilidade, mantenha. Mas a parte de organização financeira você economiza com o CaixaHub."
                  },
                  {
                    question: "É seguro?",
                    answer: "Sim. Open Banking certificado pelo Banco Central. Mesma tecnologia dos grandes bancos."
                  },
                  {
                    question: "Funciona com qualquer banco?",
                    answer: "Sim. Nubank, Itaú, Bradesco, Santander, Inter, C6, qualquer banco com Open Banking."
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
                Pare de pagar caro por trabalho que robô faz melhor
              </h2>
              <p className="text-2xl text-muted-foreground">
                Teste 7 dias grátis. Veja seu financeiro organizado automaticamente.
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

export default function LandingB32Page() {
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
