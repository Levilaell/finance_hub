'use client';

import { useRouter } from 'next/navigation';
import {
  LinkIcon,
  ArrowPathIcon,
  ChartBarIcon,
  TagIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  CogIcon,
  SparklesIcon,
  BanknotesIcon,
  ArrowDownTrayIcon,
  CalendarDaysIcon,
  PlayIcon,
} from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';
import { useOnboarding } from '@/lib/onboarding/useOnboarding';

export default function ComoUsarPage() {
  const router = useRouter();
  const { resetTour } = useOnboarding();

  const handleRestartTour = () => {
    resetTour();
    router.push('/dashboard');
  };
  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-4xl">
      <div className="space-y-8 pb-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white">Como Usar o CaixaHub</h1>
            <p className="text-muted-foreground mt-1">
              Guia completo para gerenciar suas finanças de forma simples
            </p>
          </div>
          <Button
            onClick={handleRestartTour}
            variant="outline"
            className="flex items-center gap-2 shrink-0"
          >
            <PlayIcon className="h-4 w-4" />
            Refazer Tour
          </Button>
        </div>

        {/* Quick Start Guide */}
        <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <InformationCircleIcon className="h-6 w-6 text-blue-400 mt-0.5 flex-shrink-0" />
            <div>
              <h2 className="text-lg font-semibold text-white mb-2">Primeiros Passos</h2>
              <p className="text-sm text-muted-foreground">
                Conecte seu banco, sincronize suas transações e pronto! O CaixaHub organiza tudo automaticamente para você.
              </p>
            </div>
          </div>
        </div>

        {/* Step 1: Connect Bank */}
        <div className="bg-card border border-white/10 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <div className="h-10 w-10 rounded-full bg-blue-500/20 border border-blue-500/30 flex items-center justify-center flex-shrink-0">
              <span className="text-lg font-bold text-blue-400">1</span>
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <LinkIcon className="h-5 w-5 text-blue-400" />
                <h3 className="text-xl font-semibold text-white">Conecte sua Conta Bancária</h3>
              </div>
              <div className="space-y-3 text-muted-foreground">
                <p>Para começar a sincronizar suas transações automaticamente:</p>
                <ol className="list-decimal list-inside space-y-2 ml-2">
                  <li>Acesse <strong className="text-white">Contas Bancárias</strong> no menu lateral</li>
                  <li>Clique em <strong className="text-white">Conectar Banco</strong></li>
                  <li>Selecione seu banco e siga as instruções</li>
                  <li>Aguarde a confirmação da conexão</li>
                </ol>
                <div className="bg-amber-500/10 border border-amber-500/20 rounded-md p-3 mt-4">
                  <div className="flex gap-2">
                    <ExclamationTriangleIcon className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
                    <div className="text-sm">
                      <p className="font-medium text-amber-300 mb-1">Segurança</p>
                      <ul className="space-y-1 text-amber-200/80">
                        <li>Conexão via Open Banking regulamentado pelo Banco Central</li>
                        <li>Suas credenciais <strong>nunca são armazenadas</strong></li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Step 2: Sync Transactions */}
        <div className="bg-card border border-white/10 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <div className="h-10 w-10 rounded-full bg-purple-500/20 border border-purple-500/30 flex items-center justify-center flex-shrink-0">
              <span className="text-lg font-bold text-purple-400">2</span>
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <ArrowPathIcon className="h-5 w-5 text-purple-400" />
                <h3 className="text-xl font-semibold text-white">Sincronize suas Transações</h3>
              </div>
              <div className="space-y-3 text-muted-foreground">
                <p>Após conectar, suas transações são importadas automaticamente:</p>
                <ol className="list-decimal list-inside space-y-2 ml-2">
                  <li>Clique em <strong className="text-white">Sincronizar</strong> no card da conta</li>
                  <li>O sistema busca até 90 dias de transações</li>
                  <li>As transações aparecem na aba <strong className="text-white">Transações</strong></li>
                </ol>
                <div className="bg-blue-500/10 border border-blue-500/20 rounded-md p-3 mt-4">
                  <div className="flex gap-2">
                    <CheckCircleIcon className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-blue-200/80">
                      <strong className="text-blue-300">Dica:</strong> Use "Sincronizar Tudo" para atualizar todas as contas de uma vez
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="border-t border-white/10 pt-8">
          <h2 className="text-2xl font-bold text-white mb-6">Funcionalidades</h2>
        </div>

        {/* Dashboard */}
        <div className="bg-card border border-white/10 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-10 w-10 rounded-lg bg-green-500/20 border border-green-500/30 flex items-center justify-center">
              <ChartBarIcon className="h-5 w-5 text-green-400" />
            </div>
            <h3 className="text-xl font-semibold text-white">Dashboard</h3>
          </div>
          <p className="text-muted-foreground mb-3">Visão completa das suas finanças em uma única tela:</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-green-400" />
              <span>Saldo total e resultado mensal</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-green-400" />
              <span>Receitas e despesas do mês</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-green-400" />
              <span>Contas a receber/pagar/vencidas</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-green-400" />
              <span>Últimas 7 transações</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-green-400" />
              <span>Top 5 categorias de gastos</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-green-400" />
              <span>Atalhos rápidos</span>
            </div>
          </div>
        </div>

        {/* Transactions */}
        <div className="bg-card border border-white/10 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-10 w-10 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
              <BanknotesIcon className="h-5 w-5 text-blue-400" />
            </div>
            <h3 className="text-xl font-semibold text-white">Transações</h3>
          </div>
          <p className="text-muted-foreground mb-3">Todas as suas movimentações organizadas:</p>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-blue-400" />
              <span><strong className="text-white">Filtros:</strong> por conta, tipo, categoria e período</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-blue-400" />
              <span><strong className="text-white">Busca:</strong> por descrição, categoria ou estabelecimento</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-blue-400" />
              <span><strong className="text-white">Categorização:</strong> automática + edição manual</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-blue-400" />
              <span><strong className="text-white">Exportar:</strong> CSV ou Excel</span>
            </li>
          </ul>
        </div>

        {/* Bills */}
        <div className="bg-card border border-white/10 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-10 w-10 rounded-lg bg-orange-500/20 border border-orange-500/30 flex items-center justify-center">
              <CalendarDaysIcon className="h-5 w-5 text-orange-400" />
            </div>
            <h3 className="text-xl font-semibold text-white">Contas a Pagar/Receber</h3>
          </div>
          <p className="text-muted-foreground mb-3">Gerencie suas contas e compromissos financeiros:</p>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-orange-400" />
              <span><strong className="text-white">Recorrência:</strong> única, semanal, mensal ou anual</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-orange-400" />
              <span><strong className="text-white">Status:</strong> Pendente, Parcial ou Pago</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-orange-400" />
              <span><strong className="text-white">Pagamentos parciais:</strong> registre valores pagos aos poucos</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-orange-400" />
              <span><strong className="text-white">Filtros:</strong> por tipo, status e nome</span>
            </li>
          </ul>
        </div>

        {/* Categories */}
        <div className="bg-card border border-white/10 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-10 w-10 rounded-lg bg-pink-500/20 border border-pink-500/30 flex items-center justify-center">
              <TagIcon className="h-5 w-5 text-pink-400" />
            </div>
            <h3 className="text-xl font-semibold text-white">Categorias</h3>
          </div>
          <p className="text-muted-foreground mb-3">Personalize a organização das suas transações:</p>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-pink-400" />
              <span>Crie categorias personalizadas</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-pink-400" />
              <span>Separe por tipo: Receitas vs Despesas</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-pink-400" />
              <span>Escolha cor (16 opções) e emoji (24 opções)</span>
            </li>
          </ul>
        </div>

        {/* Reports */}
        <div className="bg-card border border-white/10 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-10 w-10 rounded-lg bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center">
              <DocumentTextIcon className="h-5 w-5 text-cyan-400" />
            </div>
            <h3 className="text-xl font-semibold text-white">Relatórios</h3>
          </div>
          <p className="text-muted-foreground mb-3">Análises detalhadas em 4 abas:</p>
          <div className="space-y-3 text-sm">
            <div className="bg-white/5 rounded-md p-3">
              <h4 className="font-semibold text-white mb-1">Visão Geral</h4>
              <p className="text-muted-foreground">Receitas vs Despesas mensal e Evolução do saldo</p>
            </div>
            <div className="bg-white/5 rounded-md p-3">
              <h4 className="font-semibold text-white mb-1">Categorias</h4>
              <p className="text-muted-foreground">Top gastos/receitas com gráficos de pizza</p>
            </div>
            <div className="bg-white/5 rounded-md p-3">
              <h4 className="font-semibold text-white mb-1">Fluxo de Caixa</h4>
              <p className="text-muted-foreground">Projeção 12 meses e Realizado vs Previsto</p>
            </div>
            <div className="bg-white/5 rounded-md p-3">
              <h4 className="font-semibold text-white mb-1">Comparativo</h4>
              <p className="text-muted-foreground">Análise período vs período anterior</p>
            </div>
          </div>
          <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
            <ArrowDownTrayIcon className="h-4 w-4 text-cyan-400" />
            <span><strong className="text-white">Exportar:</strong> PDF, Excel ou CSV</span>
          </div>
        </div>

        {/* AI Insights */}
        <div className="bg-card border border-white/10 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-10 w-10 rounded-lg bg-violet-500/20 border border-violet-500/30 flex items-center justify-center">
              <SparklesIcon className="h-5 w-5 text-violet-400" />
            </div>
            <div className="flex items-center gap-2">
              <h3 className="text-xl font-semibold text-white">Insights IA</h3>
              <span className="text-xs bg-violet-500/20 text-violet-300 px-2 py-0.5 rounded-full">Beta</span>
            </div>
          </div>
          <p className="text-muted-foreground mb-3">Análise inteligente das suas finanças:</p>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-violet-400" />
              <span>Score de saúde financeira (0-10)</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-violet-400" />
              <span>Alertas e oportunidades de economia</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-violet-400" />
              <span>Previsões e recomendações personalizadas</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-violet-400" />
              <span>Histórico de insights anteriores</span>
            </li>
          </ul>
        </div>

        {/* Settings */}
        <div className="bg-card border border-white/10 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-10 w-10 rounded-lg bg-gray-500/20 border border-gray-500/30 flex items-center justify-center">
              <CogIcon className="h-5 w-5 text-gray-400" />
            </div>
            <h3 className="text-xl font-semibold text-white">Configurações</h3>
          </div>
          <p className="text-muted-foreground mb-3">Gerencie sua conta:</p>
          <div className="grid grid-cols-2 gap-2 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-gray-400" />
              <span>Editar perfil</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-gray-400" />
              <span>Alterar senha</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-gray-400" />
              <span>Gerenciar assinatura</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-gray-400" />
              <span>Excluir conta</span>
            </div>
          </div>
        </div>

        {/* Tips */}
        <div className="bg-gradient-to-r from-indigo-500/10 to-cyan-500/10 border border-indigo-500/20 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Dicas</h2>
          <ul className="space-y-2 text-muted-foreground">
            <li className="flex items-start gap-2">
              <CheckCircleIcon className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
              <span><strong className="text-white">Sincronize semanalmente</strong> para manter os dados atualizados</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircleIcon className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
              <span><strong className="text-white">Revise as categorias</strong> para relatórios mais precisos</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircleIcon className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
              <span><strong className="text-white">Use Contas a Pagar</strong> para não esquecer compromissos</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircleIcon className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
              <span><strong className="text-white">Confira os Insights IA</strong> para dicas de economia</span>
            </li>
          </ul>
        </div>

        {/* Support */}
        <div className="bg-card border border-white/10 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-3">Precisa de Ajuda?</h2>
          <p className="text-muted-foreground">
            Se tiver problemas ao conectar sua conta ou sincronizar:
          </p>
          <ul className="mt-3 space-y-2 text-muted-foreground ml-6 list-disc text-sm">
            <li>Verifique se seu banco está disponível</li>
            <li>Tente desconectar e reconectar a conta</li>
            <li>Aguarde alguns minutos entre tentativas</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
