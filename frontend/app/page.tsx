"use client";

import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  BanknotesIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  CpuChipIcon,
  ClockIcon,
  CheckCircleIcon,
  ArrowRightIcon,
  StarIcon,
  SparklesIcon,
  XMarkIcon,
  Bars3Icon
} from "@heroicons/react/24/outline";
import { useState, useEffect } from "react";
import { trackViewContent } from "@/lib/meta-pixel";

export default function Home() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    trackViewContent({
      content_name: 'Home Page',
      content_category: 'Landing Page',
    });
  }, []);

  return (
    <main className="min-h-screen bg-background">
      {/* Navigation */}
      <header className="sticky top-0 z-50 border-b border-primary/20 bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 sm:px-6 lg:px-10 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center">
                <BanknotesIcon className="h-6 w-6 text-primary" />
              </div>
              <h2 className="text-xl font-extrabold text-foreground">CaixaHub</h2>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-4">
              <Link href="/pricing" className="text-sm font-medium px-3 text-foreground/80 hover:text-primary transition-colors">
                Preços
              </Link>
              <Button asChild variant="outline" className="flex h-10 min-w-[100px] items-center justify-center rounded-lg px-5 text-sm font-medium transition-colors">
                <Link href="/login">
                  Login
                </Link>
              </Button>
              <Button asChild className="flex h-10 min-w-[120px] items-center justify-center rounded-lg bg-primary px-5 text-sm font-bold text-primary-foreground shadow-sm transition-transform hover:scale-105">
                <Link href="/pricing">
                  Comece Agora
                </Link>
              </Button>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-foreground hover:text-primary transition-colors"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? (
                <XMarkIcon className="h-6 w-6" />
              ) : (
                <Bars3Icon className="h-6 w-6" />
              )}
            </button>
          </div>

          {/* Mobile Navigation */}
          {mobileMenuOpen && (
            <div className="md:hidden mt-4 pb-4 flex flex-col gap-3 border-t border-primary/20 pt-4">
              <Link
                href="/pricing"
                className="text-sm font-medium px-3 py-2 text-foreground/80 hover:text-primary transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Preços
              </Link>
              <Button asChild variant="outline" className="w-full h-10 justify-center rounded-lg text-sm font-medium">
                <Link href="/login" onClick={() => setMobileMenuOpen(false)}>
                  Login
                </Link>
              </Button>
              <Button asChild className="w-full h-10 justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
                <Link href="/pricing" onClick={() => setMobileMenuOpen(false)}>
                  Comece Agora
                </Link>
              </Button>
            </div>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative flex min-h-[60vh] items-center justify-center px-4 py-20 text-center sm:min-h-[70vh] md:px-6 lg:min-h-[80vh] lg:py-32">
        <div className="absolute inset-0 z-0">
          <div className="absolute inset-0 bg-background/70"></div>
          <Image
            className="h-full w-full object-cover opacity-20"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuDi_u3qm17_dO8TwD6XLqj6IzDb-lniDY0KdaUqk4cDlWDxqQ6iu3jJ3gN1XKrY_YNGsy2mj9CPOahTbBwjS2bBSOwqKTBeIY3KBLU62hiEWXmCFxtfIygDXzegyRohRKkzbB7VTAgfaHr1IOCREbiZ_R5B3wvDokVjxYxJMSBtrBqSiwhFDTPNKxUi34yZg6eR6lShgsGIBClkEqRxdj87LQZdyRZVZNSWGy5gpdY0r1LD51kqxxlkI3G7ms2hATGo_w2Sr4lYzQNF"
            alt="Background"
            fill
            priority
          />
        </div>
        <div className="relative z-10 flex flex-col items-center gap-6">
          <h1 className="text-4xl font-extrabold tracking-tighter text-white sm:text-5xl md:text-6xl lg:text-7xl">
            O Sistema Financeiro que Trabalha Sozinho.
          </h1>
          <p className="max-w-3xl text-base text-white/90 sm:text-lg md:text-xl">
            Conecte seu banco em 5 minutos e deixe nossa IA automatizar suas finanças. CaixaHub é automação financeira sem esforço para o pequeno e médio varejista brasileiro.
          </p>
          <Button asChild className="flex h-12 min-w-[160px] items-center justify-center rounded-lg bg-primary px-8 text-base font-bold text-primary-foreground shadow-lg transition-transform hover:scale-105">
            <Link href="/pricing">
              Comece Grátis
            </Link>
          </Button>
        </div>
      </section>

      {/* Problem & Solution Section */}
      <section className="w-full bg-card py-16 sm:py-24 lg:py-32">
        <div className="container mx-auto px-4 md:px-6">
          <div className="grid gap-12 md:grid-cols-2 lg:gap-20">
            <div className="flex flex-col justify-center gap-4">
              <div className="inline-block rounded-lg bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
                O Problema
              </div>
              <h2 className="text-3xl font-bold tracking-tighter text-foreground sm:text-4xl">
                A gestão financeira manual está freando seu crescimento.
              </h2>
              <ul className="mt-4 space-y-3 text-muted-foreground">
                <li className="flex items-start gap-3">
                  <XMarkIcon className="mt-1 h-5 w-5 text-destructive flex-shrink-0" />
                  <span>Horas perdidas em categorização manual de despesas e receitas.</span>
                </li>
                <li className="flex items-start gap-3">
                  <XMarkIcon className="mt-1 h-5 w-5 text-destructive flex-shrink-0" />
                  <span>Erros custosos na conciliação bancária que geram retrabalho.</span>
                </li>
                <li className="flex items-start gap-3">
                  <XMarkIcon className="mt-1 h-5 w-5 text-destructive flex-shrink-0" />
                  <span>Decisões atrasadas pela falta de visibilidade financeira clara e atualizada.</span>
                </li>
                <li className="flex items-start gap-3">
                  <XMarkIcon className="mt-1 h-5 w-5 text-destructive flex-shrink-0" />
                  <span>Oportunidades de negócio perdidas por não ter dados em tempo real.</span>
                </li>
              </ul>
            </div>
            <div className="flex flex-col justify-center gap-4 rounded-xl bg-background p-8 shadow-lg">
              <div className="inline-block rounded-lg bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
                A Solução
              </div>
              <h2 className="text-3xl font-bold tracking-tighter text-foreground sm:text-4xl">
                Automatize tudo e foque no que realmente importa.
              </h2>
              <ul className="mt-4 space-y-3 text-muted-foreground">
                <li className="flex items-start gap-3">
                  <CheckCircleIcon className="mt-1 h-6 w-6 text-primary flex-shrink-0" />
                  <span>Categorização automática com 99% de precisão via IA.</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircleIcon className="mt-1 h-6 w-6 text-primary flex-shrink-0" />
                  <span>Sincronização em tempo real com mais de 20 bancos.</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircleIcon className="mt-1 h-6 w-6 text-primary flex-shrink-0" />
                  <span>Relatórios inteligentes para decisões rápidas e assertivas.</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircleIcon className="mt-1 h-6 w-6 text-primary flex-shrink-0" />
                  <span>Economize 15h/mês e reinvista esse tempo em crescimento.</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="w-full bg-background py-16 sm:py-24 lg:py-32">
        <div className="container mx-auto px-4 md:px-6">
          <div className="flex flex-col items-center justify-center gap-4 text-center mb-12">
            <h2 className="text-3xl font-bold tracking-tighter text-foreground sm:text-4xl md:text-5xl">
              Por Que Escolher o CaixaHub?
            </h2>
            <p className="max-w-[720px] text-muted-foreground md:text-xl">
              Recursos desenvolvidos especificamente para o varejo brasileiro.
            </p>
          </div>
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            <Card className="border-primary/20">
              <CardHeader>
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <CpuChipIcon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>IA Inteligente de Verdade</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Nossa IA aprende com seu negócio e categoriza transações com 99% de precisão, eliminando o trabalho manual.
                </p>
              </CardContent>
            </Card>

            <Card className="border-primary/20">
              <CardHeader>
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <ClockIcon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>Economize Tempo e Dinheiro</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Reduza até 90% do tempo gasto em gestão financeira. Isso significa mais tempo para focar no crescimento do seu negócio.
                </p>
              </CardContent>
            </Card>

            <Card className="border-primary/20">
              <CardHeader>
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <ShieldCheckIcon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>100% Seguro e Regulamentado</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Certificado pelo Banco Central com tecnologia Open Finance. Seus dados são criptografados e nunca compartilhados.
                </p>
              </CardContent>
            </Card>

            <Card className="border-primary/20">
              <CardHeader>
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <ChartBarIcon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>Relatórios que Fazem Sentido</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Dashboards simples e visuais para você entender exatamente para onde vai cada centavo, sem planilhas complexas.
                </p>
              </CardContent>
            </Card>

            <Card className="border-primary/20">
              <CardHeader>
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <BanknotesIcon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>Fluxo de Caixa em Tempo Real</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Saiba exatamente quanto você tem disponível agora e nos próximos 90 dias para tomar decisões com segurança.
                </p>
              </CardContent>
            </Card>

            <Card className="border-primary/20">
              <CardHeader>
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <SparklesIcon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>Insights Acionáveis</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Receba alertas e sugestões práticas para reduzir custos, melhorar margens e planejar investimentos estratégicos.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Comparison Section */}
      <section className="w-full bg-card py-16 sm:py-24 lg:py-32">
        <div className="container mx-auto px-4 md:px-6">
          <div className="flex flex-col items-center justify-center gap-4 text-center mb-12">
            <h2 className="text-3xl font-bold tracking-tighter text-foreground sm:text-4xl md:text-5xl">
              Gestão Manual vs. CaixaHub
            </h2>
            <p className="max-w-[720px] text-muted-foreground md:text-xl">
              Veja a diferença real que a automação faz no seu dia a dia.
            </p>
          </div>
          <div className="grid gap-8 md:grid-cols-2 max-w-5xl mx-auto">
            <div className="rounded-xl bg-destructive/10 border-2 border-destructive/20 p-8">
              <div className="mb-6 flex items-center gap-3">
                <XMarkIcon className="h-8 w-8 text-destructive" />
                <h3 className="text-2xl font-bold text-foreground">Gestão Manual</h3>
              </div>
              <ul className="space-y-4">
                <li className="flex items-start gap-3">
                  <XMarkIcon className="mt-1 h-5 w-5 text-destructive flex-shrink-0" />
                  <span className="text-muted-foreground">15-20 horas/mês categorizando transações</span>
                </li>
                <li className="flex items-start gap-3">
                  <XMarkIcon className="mt-1 h-5 w-5 text-destructive flex-shrink-0" />
                  <span className="text-muted-foreground">Dados desatualizados e espalhados</span>
                </li>
                <li className="flex items-start gap-3">
                  <XMarkIcon className="mt-1 h-5 w-5 text-destructive flex-shrink-0" />
                  <span className="text-muted-foreground">Erros de digitação e duplicação</span>
                </li>
                <li className="flex items-start gap-3">
                  <XMarkIcon className="mt-1 h-5 w-5 text-destructive flex-shrink-0" />
                  <span className="text-muted-foreground">Planilhas complexas e confusas</span>
                </li>
                <li className="flex items-start gap-3">
                  <XMarkIcon className="mt-1 h-5 w-5 text-destructive flex-shrink-0" />
                  <span className="text-muted-foreground">Decisões baseadas em dados do mês passado</span>
                </li>
                <li className="flex items-start gap-3">
                  <XMarkIcon className="mt-1 h-5 w-5 text-destructive flex-shrink-0" />
                  <span className="text-muted-foreground">Custo de R$ 450-900/mês (analista)</span>
                </li>
              </ul>
            </div>

            <div className="rounded-xl bg-primary/10 border-2 border-primary/20 p-8">
              <div className="mb-6 flex items-center gap-3">
                <CheckCircleIcon className="h-8 w-8 text-primary" />
                <h3 className="text-2xl font-bold text-foreground">Com CaixaHub</h3>
              </div>
              <ul className="space-y-4">
                <li className="flex items-start gap-3">
                  <CheckCircleIcon className="mt-1 h-5 w-5 text-primary flex-shrink-0" />
                  <span className="text-muted-foreground">100% automático, zero trabalho manual</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircleIcon className="mt-1 h-5 w-5 text-primary flex-shrink-0" />
                  <span className="text-muted-foreground">Sincronização em tempo real 24/7</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircleIcon className="mt-1 h-5 w-5 text-primary flex-shrink-0" />
                  <span className="text-muted-foreground">99% de precisão com IA treinada</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircleIcon className="mt-1 h-5 w-5 text-primary flex-shrink-0" />
                  <span className="text-muted-foreground">Dashboards visuais e intuitivos</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircleIcon className="mt-1 h-5 w-5 text-primary flex-shrink-0" />
                  <span className="text-muted-foreground">Decisões baseadas em dados atuais</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircleIcon className="mt-1 h-5 w-5 text-primary flex-shrink-0" />
                  <span className="text-muted-foreground">A partir de R$ 97/mês (ROI de 6x)</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="w-full bg-background py-16 sm:py-24 lg:py-32">
        <div className="container mx-auto px-4 md:px-6">
          <div className="flex flex-col items-center justify-center gap-4 text-center">
            <h2 className="text-3xl font-bold tracking-tighter text-foreground sm:text-4xl md:text-5xl">
              Como Funciona
            </h2>
            <p className="max-w-[720px] text-muted-foreground md:text-xl">
              Em apenas 3 passos simples, você terá o controle total das finanças da sua empresa.
            </p>
          </div>
          <div className="mx-auto mt-12 grid max-w-5xl gap-8 sm:grid-cols-1 md:grid-cols-3">
            <div className="flex flex-col items-center gap-4 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-2xl font-bold text-primary-foreground">
                1
              </div>
              <h3 className="text-xl font-bold text-foreground">Conecte seus bancos</h3>
              <p className="text-muted-foreground">
                De forma segura via Open Banking em menos de 2 minutos.
              </p>
            </div>
            <div className="flex flex-col items-center gap-4 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-2xl font-bold text-primary-foreground">
                2
              </div>
              <h3 className="text-xl font-bold text-foreground">A IA categoriza tudo</h3>
              <p className="text-muted-foreground">
                Nossa inteligência artificial organiza suas transações automaticamente.
              </p>
            </div>
            <div className="flex flex-col items-center gap-4 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-2xl font-bold text-primary-foreground">
                3
              </div>
              <h3 className="text-xl font-bold text-foreground">Tome decisões inteligentes</h3>
              <p className="text-muted-foreground">
                Use relatórios detalhados, projeções e insights para crescer.
              </p>
            </div>
          </div>
          <div className="mt-12 flex justify-center">
            <Button asChild className="flex h-12 min-w-[200px] items-center justify-center rounded-lg bg-primary px-8 text-base font-bold text-primary-foreground shadow-lg transition-transform hover:scale-105">
              <Link href="/pricing">
                Começar Agora - É Grátis
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="w-full bg-card py-16 sm:py-24 lg:py-32">
        <div className="container mx-auto px-4 md:px-6">
          <div className="flex flex-col items-center justify-center gap-4 text-center">
            <h2 className="text-3xl font-bold tracking-tighter text-foreground sm:text-4xl md:text-5xl">
              O Impacto Real na Sua Empresa
            </h2>
            <p className="max-w-[720px] text-muted-foreground md:text-xl">
              Projeções baseadas no tempo médio gasto com gestão financeira manual.
            </p>
          </div>
          <div className="mx-auto mt-12 grid max-w-4xl grid-cols-2 gap-8 md:grid-cols-4">
            <div className="flex flex-col items-center gap-2 rounded-xl bg-background p-6 text-center shadow-md">
              <div className="text-4xl font-bold text-primary">2 min</div>
              <p className="font-medium text-foreground">Setup Inicial</p>
            </div>
            <div className="flex flex-col items-center gap-2 rounded-xl bg-background p-6 text-center shadow-md">
              <div className="text-4xl font-bold text-primary">15h</div>
              <p className="font-medium text-foreground">Economizadas/Mês</p>
            </div>
            <div className="flex flex-col items-center gap-2 rounded-xl bg-background p-6 text-center shadow-md">
              <div className="text-4xl font-bold text-primary">R$ 450</div>
              <p className="font-medium text-foreground">Economizados/Mês*</p>
            </div>
            <div className="flex flex-col items-center gap-2 rounded-xl bg-background p-6 text-center shadow-md">
              <div className="text-4xl font-bold text-primary">24/7</div>
              <p className="font-medium text-foreground">Sincronização Automática</p>
            </div>
          </div>
          <p className="mt-8 text-center text-sm text-muted-foreground">
            *Baseado no custo médio de um analista financeiro (R$ 30/hora).
          </p>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="w-full bg-background py-16 sm:py-24 lg:py-32">
        <div className="container mx-auto px-4 md:px-6">
          <div className="flex flex-col items-center justify-center gap-4 text-center mb-12">
            <h2 className="text-3xl font-bold tracking-tighter text-foreground sm:text-4xl md:text-5xl">
              O Que Nossos Clientes Dizem
            </h2>
            <p className="max-w-[720px] text-muted-foreground md:text-xl">
              Varejistas como você já estão economizando tempo e dinheiro com o CaixaHub.
            </p>
          </div>
          <div className="grid gap-8 md:grid-cols-3 max-w-6xl mx-auto">
            <Card className="border-primary/20">
              <CardHeader>
                <div className="flex items-center gap-4 mb-2">
                  <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-lg font-bold text-primary">
                    MC
                  </div>
                  <div>
                    <CardTitle className="text-base">Maria Costa</CardTitle>
                    <CardDescription>Farmácia São José</CardDescription>
                  </div>
                </div>
                <div className="flex gap-1">
                  <StarIcon className="h-5 w-5 fill-primary text-primary" />
                  <StarIcon className="h-5 w-5 fill-primary text-primary" />
                  <StarIcon className="h-5 w-5 fill-primary text-primary" />
                  <StarIcon className="h-5 w-5 fill-primary text-primary" />
                  <StarIcon className="h-5 w-5 fill-primary text-primary" />
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  "Economizei mais de 10 horas por mês. Antes passava o final de semana organizando planilhas, agora tudo acontece sozinho. Incrível!"
                </p>
              </CardContent>
            </Card>

            <Card className="border-primary/20">
              <CardHeader>
                <div className="flex items-center gap-4 mb-2">
                  <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-lg font-bold text-primary">
                    JS
                  </div>
                  <div>
                    <CardTitle className="text-base">João Silva</CardTitle>
                    <CardDescription>Mercearia Central</CardDescription>
                  </div>
                </div>
                <div className="flex gap-1">
                  <StarIcon className="h-5 w-5 fill-primary text-primary" />
                  <StarIcon className="h-5 w-5 fill-primary text-primary" />
                  <StarIcon className="h-5 w-5 fill-primary text-primary" />
                  <StarIcon className="h-5 w-5 fill-primary text-primary" />
                  <StarIcon className="h-5 w-5 fill-primary text-primary" />
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  "Finalmente consigo ver para onde vai meu dinheiro. Os relatórios são simples de entender e me ajudam a tomar decisões melhores."
                </p>
              </CardContent>
            </Card>

            <Card className="border-primary/20">
              <CardHeader>
                <div className="flex items-center gap-4 mb-2">
                  <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-lg font-bold text-primary">
                    AS
                  </div>
                  <div>
                    <CardTitle className="text-base">Ana Santos</CardTitle>
                    <CardDescription>Boutique Elegance</CardDescription>
                  </div>
                </div>
                <div className="flex gap-1">
                  <StarIcon className="h-5 w-5 fill-primary text-primary" />
                  <StarIcon className="h-5 w-5 fill-primary text-primary" />
                  <StarIcon className="h-5 w-5 fill-primary text-primary" />
                  <StarIcon className="h-5 w-5 fill-primary text-primary" />
                  <StarIcon className="h-5 w-5 fill-primary text-primary" />
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  "A integração com meu banco foi super rápida. Em 2 minutos estava tudo funcionando. Valeu cada centavo do investimento."
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Trust & Security Section */}
      <section className="w-full bg-card py-16 sm:py-24 lg:py-32">
        <div className="container mx-auto px-4 md:px-6">
          <div className="flex flex-col items-center justify-center gap-4 text-center mb-12">
            <h2 className="text-3xl font-bold tracking-tighter text-foreground sm:text-4xl md:text-5xl">
              Segurança e Confiança em Primeiro Lugar
            </h2>
            <p className="max-w-[720px] text-muted-foreground md:text-xl">
              Seus dados financeiros protegidos pelos mais altos padrões de segurança.
            </p>
          </div>
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4 max-w-6xl mx-auto">
            <div className="flex flex-col items-center gap-4 text-center p-6 rounded-xl bg-background">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                <ShieldCheckIcon className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-lg font-bold text-foreground">Certificado Banco Central</h3>
              <p className="text-sm text-muted-foreground">
                Regulamentado e certificado pelo Banco Central do Brasil via Open Finance.
              </p>
            </div>

            <div className="flex flex-col items-center gap-4 text-center p-6 rounded-xl bg-background">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                <ShieldCheckIcon className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-lg font-bold text-foreground">Criptografia de Ponta</h3>
              <p className="text-sm text-muted-foreground">
                Seus dados são protegidos com criptografia de nível bancário AES-256.
              </p>
            </div>

            <div className="flex flex-col items-center gap-4 text-center p-6 rounded-xl bg-background">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                <ShieldCheckIcon className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-lg font-bold text-foreground">Modo Somente Leitura</h3>
              <p className="text-sm text-muted-foreground">
                Nunca movemos dinheiro. Acesso 100% em modo leitura para sua segurança.
              </p>
            </div>

            <div className="flex flex-col items-center gap-4 text-center p-6 rounded-xl bg-background">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                <ShieldCheckIcon className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-lg font-bold text-foreground">Privacidade Total</h3>
              <p className="text-sm text-muted-foreground">
                Seus dados nunca são vendidos ou compartilhados com terceiros. Ponto final.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Risk Reversal Section */}
      <section className="w-full bg-background py-16 sm:py-24 lg:py-32">
        <div className="container mx-auto px-4 md:px-6">
          <div className="mx-auto max-w-4xl rounded-2xl bg-primary/5 border-2 border-primary/20 p-8 md:p-12 text-center">
            <Badge className="mb-4 bg-primary text-primary-foreground">Sem Riscos</Badge>
            <h2 className="text-3xl font-bold tracking-tighter text-foreground sm:text-4xl md:text-5xl mb-6">
              Experimente 7 Dias Grátis
            </h2>
            <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
              Cancele quando quiser, sem burocracia.
            </p>
            <div className="grid gap-6 md:grid-cols-3 mb-8 text-left">
              <div className="flex items-start gap-3">
                <CheckCircleIcon className="h-6 w-6 text-primary flex-shrink-0 mt-1" />
                <div>
                  <h3 className="font-bold text-foreground mb-1">7 Dias Grátis</h3>
                  <p className="text-sm text-muted-foreground">Teste todas as funcionalidades sem compromisso</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <CheckCircleIcon className="h-6 w-6 text-primary flex-shrink-0 mt-1" />
                <div>
                  <h3 className="font-bold text-foreground mb-1">Cancele a Qualquer Momento</h3>
                  <p className="text-sm text-muted-foreground">Um clique para cancelar, sem taxas ou multas</p>
                </div>
              </div>
            </div>
            <Button asChild size="lg" className="h-14 min-w-[240px] text-lg font-bold shadow-xl hover:scale-105 transition-transform">
              <Link href="/pricing">
                Começar Teste Grátis
                <ArrowRightIcon className="ml-2 h-5 w-5" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* For Who Section */}
      <section className="w-full bg-card py-16 sm:py-24 lg:py-32">
        <div className="container mx-auto px-4 md:px-6">
          <div className="flex flex-col items-center justify-center gap-4 text-center mb-12">
            <h2 className="text-3xl font-bold tracking-tighter text-foreground sm:text-4xl md:text-5xl">
              Feito Para o Varejo Brasileiro
            </h2>
            <p className="max-w-[720px] text-muted-foreground md:text-xl">
              Pequenos e médios varejistas já usam o CaixaHub para transformar sua gestão financeira.
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 max-w-5xl mx-auto">
            <div className="rounded-xl bg-background p-6 border border-primary/20">
              <h3 className="text-xl font-bold text-foreground mb-3">🛒 Supermercados e Mercearias</h3>
              <p className="text-muted-foreground">
                Gerencie alto volume de transações e identifique suas categorias de maior custo automaticamente.
              </p>
            </div>

            <div className="rounded-xl bg-background p-6 border border-primary/20">
              <h3 className="text-xl font-bold text-foreground mb-3">💊 Farmácias e Drogarias</h3>
              <p className="text-muted-foreground">
                Controle estoque financeiro, margens e vencimentos com relatórios específicos para o setor.
              </p>
            </div>

            <div className="rounded-xl bg-background p-6 border border-primary/20">
              <h3 className="text-xl font-bold text-foreground mb-3">👗 Lojas de Roupa e Acessórios</h3>
              <p className="text-muted-foreground">
                Acompanhe sazonalidade, margem por produto e planeje coleções com dados reais de vendas.
              </p>
            </div>

            <div className="rounded-xl bg-background p-6 border border-primary/20">
              <h3 className="text-xl font-bold text-foreground mb-3">🍕 Restaurantes e Lanchonetes</h3>
              <p className="text-muted-foreground">
                Monitore CMV (Custo de Mercadoria Vendida), desperdícios e otimize compras de insumos.
              </p>
            </div>

            <div className="rounded-xl bg-background p-6 border border-primary/20">
              <h3 className="text-xl font-bold text-foreground mb-3">🔧 Lojas de Materiais e Ferramentas</h3>
              <p className="text-muted-foreground">
                Controle produtos de alto ticket, fornecedores e margem de lucro em tempo real.
              </p>
            </div>

            <div className="rounded-xl bg-background p-6 border border-primary/20">
              <h3 className="text-xl font-bold text-foreground mb-3">🏪 Pet Shops e Agropecuárias</h3>
              <p className="text-muted-foreground">
                Gerencie produtos perecíveis, controle de estoque e despesas operacionais com precisão.
              </p>
            </div>
          </div>
          <div className="mt-12 text-center">
            <p className="text-muted-foreground mb-6">
              Não viu seu tipo de negócio aqui? O CaixaHub funciona para qualquer varejo!
            </p>
            <Button asChild variant="outline" size="lg">
              <Link href="/pricing">
                Começar Agora
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="w-full bg-background py-16 sm:py-24 lg:py-32">
        <div className="container mx-auto max-w-3xl px-4 md:px-6">
          <div className="flex flex-col items-center justify-center gap-4 text-center">
            <h2 className="text-3xl font-bold tracking-tighter text-foreground sm:text-4xl md:text-5xl">
              Perguntas Frequentes
            </h2>
          </div>
          <div className="mt-12 space-y-6">
            <details className="group rounded-lg bg-card p-6">
              <summary className="flex cursor-pointer list-none items-center justify-between font-medium text-foreground">
                O CaixaHub é seguro?
                <span className="transition group-open:rotate-180">
                  <svg
                    fill="none"
                    height="24"
                    stroke="currentColor"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    width="24"
                  >
                    <path d="M6 9l6 6 6-6"></path>
                  </svg>
                </span>
              </summary>
              <p className="mt-4 text-muted-foreground">
                Sim. Utilizamos a tecnologia Open Finance, regulamentada pelo Banco Central do Brasil, para garantir a conexão segura com seus bancos. Seus dados são criptografados e acessados apenas em modo de leitura.
              </p>
            </details>
            <details className="group rounded-lg bg-card p-6">
              <summary className="flex cursor-pointer list-none items-center justify-between font-medium text-foreground">
                Preciso instalar algum software?
                <span className="transition group-open:rotate-180">
                  <svg
                    fill="none"
                    height="24"
                    stroke="currentColor"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    width="24"
                  >
                    <path d="M6 9l6 6 6-6"></path>
                  </svg>
                </span>
              </summary>
              <p className="mt-4 text-muted-foreground">
                Não. O CaixaHub é 100% online. Você pode acessá-lo de qualquer dispositivo com conexão à internet, seja computador, tablet ou celular.
              </p>
            </details>
            <details className="group rounded-lg bg-card p-6">
              <summary className="flex cursor-pointer list-none items-center justify-between font-medium text-foreground">
                Quais bancos são suportados?
                <span className="transition group-open:rotate-180">
                  <svg
                    fill="none"
                    height="24"
                    stroke="currentColor"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    width="24"
                  >
                    <path d="M6 9l6 6 6-6"></path>
                  </svg>
                </span>
              </summary>
              <p className="mt-4 text-muted-foreground">
                Integramos com os maiores bancos do Brasil, incluindo Itaú, Bradesco, Banco do Brasil, Santander, Caixa, Nubank, Inter e muitos outros. A lista completa está sempre crescendo.
              </p>
            </details>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="w-full bg-primary/10 py-16 sm:py-24 lg:py-32">
        <div className="container mx-auto flex flex-col items-center gap-6 px-4 text-center md:px-6">
          <h2 className="text-3xl font-bold tracking-tighter text-foreground sm:text-4xl md:text-5xl">
            Pronto para Automatizar Suas Finanças?
          </h2>
          <p className="max-w-[720px] text-muted-foreground md:text-xl">
            Junte-se a milhares de empresas brasileiras que confiam no CaixaHub para simplificar sua gestão financeira.
          </p>
          <Button asChild className="mt-4 flex h-12 min-w-[200px] items-center justify-center rounded-lg bg-primary px-8 text-base font-bold text-primary-foreground shadow-lg transition-transform hover:scale-105">
            <Link href="/pricing">
              Experimente de Graça
            </Link>
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-primary/20 bg-background">
        <div className="container mx-auto max-w-5xl px-4 py-10 text-center sm:px-6">
          <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
            <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
              <Link href="#produto" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                Produto
              </Link>
              <Link href="/pricing" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                Preços
              </Link>
              <a href="https://wa.me/5517992679645" target="_blank" rel="noopener noreferrer" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                Contato
              </a>
            </div>
            <div className="flex justify-center gap-4">
              <a className="text-muted-foreground hover:text-primary transition-colors" href="#">
                <svg fill="currentColor" height="24" viewBox="0 0 256 256" width="24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M247.39,68.94A8,8,0,0,0,240,64H209.57A48.66,48.66,0,0,0,168.1,40a46.91,46.91,0,0,0-33.75,13.7A47.9,47.9,0,0,0,120,88v6.09C79.74,83.47,46.81,50.72,46.46,50.37a8,8,0,0,0-13.65,4.92c-4.31,47.79,9.57,79.77,22,98.18a110.93,110.93,0,0,0,21.88,24.2c-15.23,17.53-39.21,26.74-39.47,26.84a8,8,0,0,0-3.85,11.93c.75,1.12,3.75,5.05,11.08,8.72C53.51,229.7,65.48,232,80,232c70.67,0,129.72-54.42,135.75-124.44l29.91-29.9A8,8,0,0,0,247.39,68.94Zm-45,29.41a8,8,0,0,0-2.32,5.14C196,166.58,143.28,216,80,216c-10.56,0-18-1.4-23.22-3.08,11.51-6.25,27.56-17,37.88-32.48A8,8,0,0,0,92,169.08c-.47-.27-43.91-26.34-44-96,16,13,45.25,33.17,78.67,38.79A8,8,0,0,0,136,104V88a32,32,0,0,1,9.6-22.92A30.94,30.94,0,0,1,167.9,56c12.66.16,24.49,7.88,29.44,19.21A8,8,0,0,0,204.67,80h16Z"></path>
                </svg>
              </a>
              <a className="text-muted-foreground hover:text-primary transition-colors" href="#">
                <svg fill="currentColor" height="24" viewBox="0 0 256 256" width="24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M128,80a48,48,0,1,0,48,48A48.05,48.05,0,0,0,128,80Zm0,80a32,32,0,1,1,32-32A32,32,0,0,1,128,160ZM176,24H80A56.06,56.06,0,0,0,24,80v96a56.06,56.06,0,0,0,56,56h96a56.06,56.06,0,0,0,56-56V80A56.06,56.06,0,0,0,176,24Zm40,152a40,40,0,0,1-40,40H80a40,40,0,0,1-40-40V80A40,40,0,0,1,80,40h96a40,40,0,0,1,40,40Z"></path>
                </svg>
              </a>
            </div>
          </div>
          <p className="mt-6 text-xs text-muted-foreground">
            © 2025 CaixaHub. Todos os direitos reservados.
          </p>
        </div>
      </footer>
    </main>
  );
}