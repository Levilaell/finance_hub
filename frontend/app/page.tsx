"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  BanknotesIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  CpuChipIcon,
  ClockIcon,
  CheckCircleIcon,
  ArrowRightIcon,
  SparklesIcon,
  XMarkIcon,
  Bars3Icon
} from "@heroicons/react/24/outline";
import { useState, useEffect } from "react";
import { trackViewContent } from "@/lib/meta-pixel";

// Price ID para o plano de R$197
const PRICE_ID_197 = process.env.NEXT_PUBLIC_PRICE_197 || "price_1SXwA6AhSWJIUR4PV1BYoKLt";

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
              <Button asChild variant="outline" className="flex h-10 min-w-[100px] items-center justify-center rounded-lg px-5 text-sm font-medium transition-colors">
                <Link href="/login">
                  Login
                </Link>
              </Button>
              <Button asChild className="flex h-10 min-w-[120px] items-center justify-center rounded-lg bg-primary px-5 text-sm font-bold text-primary-foreground shadow-sm transition-transform hover:scale-105">
                <Link href={`/register?price_id=${PRICE_ID_197}`}>
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
              <Button asChild variant="outline" className="w-full h-10 justify-center rounded-lg text-sm font-medium">
                <Link href="/login" onClick={() => setMobileMenuOpen(false)}>
                  Login
                </Link>
              </Button>
              <Button asChild className="w-full h-10 justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
                <Link href={`/register?price_id=${PRICE_ID_197}`} onClick={() => setMobileMenuOpen(false)}>
                  Comece Agora
                </Link>
              </Button>
            </div>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden px-4 py-20 sm:py-28 lg:py-36">
        {/* Animated background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-background via-primary/5 to-background">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,_rgba(74,170,123,0.15)_0%,_transparent_50%)]" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,_rgba(74,170,123,0.1)_0%,_transparent_50%)]" />
        </div>

        {/* Floating decorative elements */}
        <div className="absolute top-20 left-10 h-32 w-32 rounded-full bg-primary/10 blur-3xl animate-pulse" />
        <div className="absolute bottom-20 right-10 h-40 w-40 rounded-full bg-primary/5 blur-3xl animate-pulse delay-1000" />

        <div className="container mx-auto relative z-10">
          <div className="max-w-5xl mx-auto text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-2 mb-8 border border-primary/20">
              <SparklesIcon className="h-4 w-4 text-primary animate-pulse" />
              <span className="text-sm font-medium text-primary">IA + Open Banking = Automação Total</span>
            </div>

            {/* Main heading with gradient */}
            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight mb-6 leading-tight">
              <span className="block text-foreground">O Sistema Financeiro</span>
              <span className="block mt-2 bg-gradient-to-r from-primary via-primary/80 to-primary bg-clip-text text-transparent">
                que Trabalha Sozinho
              </span>
            </h1>

            {/* Description */}
            <p className="text-lg sm:text-xl md:text-2xl text-muted-foreground mb-8 max-w-3xl mx-auto leading-relaxed">
              Conecte seu banco em <span className="font-bold text-primary">5 minutos</span> e deixe nossa IA automatizar suas finanças.
              Automação financeira sem esforço para o pequeno e médio varejista brasileiro.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
              <Button
                asChild
                size="lg"
                className="h-14 px-8 text-lg font-bold bg-primary hover:bg-primary/90 text-primary-foreground shadow-[0_0_30px_rgba(74,170,123,0.3)] hover:shadow-[0_0_40px_rgba(74,170,123,0.5)] transition-all duration-300 group"
              >
                <Link href={`/register?price_id=${PRICE_ID_197}`} className="flex items-center gap-2">
                  Comece Grátis
                  <ArrowRightIcon className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </Link>
              </Button>
            </div>

            {/* Trust indicators */}
            <div className="flex flex-wrap items-center justify-center gap-6 sm:gap-8 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <CheckCircleIcon className="h-5 w-5 text-primary" />
                <span>7 dias grátis</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircleIcon className="h-5 w-5 text-primary" />
                <span>Cancele quando quiser</span>
              </div>
            </div>

            {/* Stats bar */}
            <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
              <div className="bg-card/50 backdrop-blur-sm rounded-xl p-6 border border-primary/10">
                <div className="text-3xl font-bold text-primary mb-1">2 min</div>
                <div className="text-sm text-muted-foreground">Setup inicial</div>
              </div>
              <div className="bg-card/50 backdrop-blur-sm rounded-xl p-6 border border-primary/10">
                <div className="text-3xl font-bold text-primary mb-1">99%</div>
                <div className="text-sm text-muted-foreground">Precisão da IA</div>
              </div>
              <div className="bg-card/50 backdrop-blur-sm rounded-xl p-6 border border-primary/10">
                <div className="text-3xl font-bold text-primary mb-1">15h</div>
                <div className="text-sm text-muted-foreground">Economizadas/mês</div>
              </div>
              <div className="bg-card/50 backdrop-blur-sm rounded-xl p-6 border border-primary/10">
                <div className="text-3xl font-bold text-primary mb-1">24/7</div>
                <div className="text-sm text-muted-foreground">Sincronização</div>
              </div>
            </div>
          </div>
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
                  <span className="text-muted-foreground">A partir de R$ 197/mês</span>
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
              <Link href={`/register?price_id=${PRICE_ID_197}`}>
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
          <div className="grid gap-8 md:grid-cols-1 lg:grid-cols-3 max-w-6xl mx-auto">
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

      {/* Pricing Section */}
      <section id="pricing" className="w-full bg-muted/30 py-16 sm:py-24 lg:py-32">
        <div className="container mx-auto px-4 md:px-6">
          <div className="max-w-2xl mx-auto">
            <Card className="p-10 relative overflow-hidden border-primary/50">
              <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 rounded-full -translate-y-16 translate-x-16" />

              <div className="text-center mb-8">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-full text-sm font-medium mb-4">
                  <SparklesIcon className="w-4 h-4" />
                  Oferta Especial
                </div>
                <h2 className="text-5xl font-bold mb-4">
                  R$ 197<span className="text-2xl text-muted-foreground">/mês</span>
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
                    <CheckCircleIcon className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
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
                <p className="text-center text-base text-foreground font-medium">
                  R$ 197/mês para automatizar 100% do seu financeiro
                </p>
              </div>
            </Card>
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
            <div className="grid gap-6 md:grid-cols-2 mb-8 max-w-3xl mx-auto">
              <div className="flex flex-col items-center gap-3 text-center">
                <CheckCircleIcon className="h-6 w-6 text-primary flex-shrink-0" />
                <div>
                  <h3 className="font-bold text-foreground mb-1">7 Dias Grátis</h3>
                  <p className="text-sm text-muted-foreground">Teste todas as funcionalidades sem compromisso</p>
                </div>
              </div>

              <div className="flex flex-col items-center gap-3 text-center">
                <CheckCircleIcon className="h-6 w-6 text-primary flex-shrink-0" />
                <div>
                  <h3 className="font-bold text-foreground mb-1">Cancele a Qualquer Momento</h3>
                  <p className="text-sm text-muted-foreground">Um clique para cancelar, sem taxas ou multas</p>
                </div>
              </div>
            </div>
            <Button asChild size="lg" className="h-14 min-w-[240px] text-lg font-bold shadow-xl hover:scale-105 transition-transform">
              <Link href={`/register?price_id=${PRICE_ID_197}`}>
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
              <Link href={`/register?price_id=${PRICE_ID_197}`}>
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
            <Link href={`/register?price_id=${PRICE_ID_197}`}>
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
              <a href="https://wa.me/5517992679645" target="_blank" rel="noopener noreferrer" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                Contato
              </a>
            </div>
            <div className="flex justify-center gap-4">
              <a className="text-muted-foreground hover:text-primary transition-colors" href="https://www.instagram.com/caixahub/" target="_blank" rel="noopener noreferrer">
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