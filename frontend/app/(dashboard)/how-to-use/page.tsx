'use client';

import {
  LinkIcon,
  ArrowPathIcon,
  ChartBarIcon,
  TagIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

export default function ComoUsarPage() {
  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-4xl">
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-white">Como Usar o CaixaHub</h1>
          <p className="text-muted-foreground mt-1">
            Guia completo para começar a gerenciar suas finanças
          </p>
        </div>

      {/* Quick Start Guide */}
      <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <InformationCircleIcon className="h-6 w-6 text-blue-400 mt-0.5 flex-shrink-0" />
          <div>
            <h2 className="text-lg font-semibold text-white mb-2">Início Rápido</h2>
            <p className="text-sm text-gray-300">
              Siga os passos abaixo para configurar sua conta e começar a acompanhar suas finanças automaticamente.
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
            <div className="space-y-3 text-gray-300">
              <p>Para começar a sincronizar suas transações automaticamente:</p>
              <ol className="list-decimal list-inside space-y-2 ml-2">
                <li>Acesse a aba <strong className="text-white">Contas Bancárias</strong> no menu lateral</li>
                <li>Clique no botão <strong className="text-white">Conectar Banco</strong></li>
                <li>Uma janela da Pluggy será aberta com a lista de bancos disponíveis</li>
                <li>Selecione seu banco e siga as instruções na tela:
                  <ul className="list-disc list-inside ml-6 mt-1 space-y-1 text-sm">
                    <li><strong className="text-white">PIX/QR Code:</strong> Alguns bancos permitem conexão rápida escaneando um QR Code no app do banco</li>
                    <li><strong className="text-white">Credenciais:</strong> Outros bancos solicitam suas credenciais de acesso (usuário e senha)</li>
                    <li><strong className="text-white">Autenticação:</strong> Pode ser necessário confirmar via token, SMS ou app do banco</li>
                  </ul>
                </li>
                <li>Aguarde a confirmação da conexão bem-sucedida</li>
              </ol>
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-md p-3 mt-4">
                <div className="flex gap-2">
                  <ExclamationTriangleIcon className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm">
                    <p className="font-medium text-amber-300 mb-1">Importante sobre a conexão:</p>
                    <ul className="space-y-1 text-amber-200/80">
                      <li>• Alguns bancos podem estar temporariamente indisponíveis devido a manutenções</li>
                      <li>• A conexão é 100% segura e criptografada via Open Banking regulamentado pelo Banco Central</li>
                      <li>• Suas credenciais <strong>não são armazenadas</strong> pelo CaixaHub</li>
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
            <div className="space-y-3 text-gray-300">
              <p>Após conectar sua conta, é hora de buscar suas transações:</p>
              <ol className="list-decimal list-inside space-y-2 ml-2">
                <li>Na aba <strong className="text-white">Contas</strong>, localize o card da sua conta bancária</li>
                <li>Clique no botão <strong className="text-white">Sincronizar</strong> no card da conta</li>
                <li>O sistema buscará automaticamente suas transações recentes (geralmente até 90 dias)</li>
                <li>Acompanhe o progresso da sincronização através das notificações</li>
                <li>Quando concluído, suas transações aparecerão na aba <strong className="text-white">Transações</strong></li>
              </ol>
              <div className="bg-blue-500/10 border border-blue-500/20 rounded-md p-3 mt-4">
                <div className="flex gap-2">
                  <CheckCircleIcon className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm">
                    <p className="font-medium text-blue-300 mb-1">Dicas de sincronização:</p>
                    <ul className="space-y-1 text-blue-200/80">
                      <li>• Use <strong>Sincronizar Tudo</strong> para atualizar todas as contas de uma vez</li>
                      <li>• A primeira sincronização pode demorar alguns minutos</li>
                      <li>• Sincronizações seguintes são mais rápidas, buscando apenas novas transações</li>
                      <li>• Recomendamos sincronizar pelo menos 1x por semana para manter os dados atualizados</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Step 3: View Reports */}
      <div className="bg-card border border-white/10 rounded-lg p-6">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 rounded-full bg-green-500/20 border border-green-500/30 flex items-center justify-center flex-shrink-0">
            <span className="text-lg font-bold text-green-400">3</span>
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <ChartBarIcon className="h-5 w-5 text-green-400" />
              <h3 className="text-xl font-semibold text-white">Visualize seus Relatórios</h3>
            </div>
            <div className="space-y-3 text-gray-300">
              <p>Agora você pode analisar suas finanças em diferentes abas:</p>
              <div className="space-y-3 ml-2">
                <div>
                  <h4 className="font-semibold text-white mb-1">📊 Dashboard</h4>
                  <p className="text-sm">Visão geral das suas finanças com gráficos de receitas, despesas e saldo</p>
                </div>
                <div>
                  <h4 className="font-semibold text-white mb-1">💳 Transações</h4>
                  <p className="text-sm">Lista completa de todas as suas movimentações com filtros por data, categoria e tipo</p>
                </div>
                <div>
                  <h4 className="font-semibold text-white mb-1">📈 Relatórios</h4>
                  <p className="text-sm">Análises detalhadas por período, categoria e tendências de gastos</p>
                </div>
                <div>
                  <h4 className="font-semibold text-white mb-1">💰 Contas</h4>
                  <p className="text-sm">Gerenciamento das suas contas conectadas, saldos e limites de crédito</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Step 4: Manage Categories */}
      <div className="bg-card border border-white/10 rounded-lg p-6">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 rounded-full bg-orange-500/20 border border-orange-500/30 flex items-center justify-center flex-shrink-0">
            <span className="text-lg font-bold text-orange-400">4</span>
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <TagIcon className="h-5 w-5 text-orange-400" />
              <h3 className="text-xl font-semibold text-white">Organize suas Categorias</h3>
            </div>
            <div className="space-y-3 text-gray-300">
              <p>Personalize como suas transações são categorizadas:</p>
              <ol className="list-decimal list-inside space-y-2 ml-2">
                <li>Acesse a aba <strong className="text-white">Categorias</strong></li>
                <li>O sistema já categoriza automaticamente a maioria das transações</li>
                <li>Você pode recategorizar transações manualmente se necessário</li>
                <li>Crie categorias personalizadas para melhor organização</li>
                <li>Use as categorias para analisar seus gastos por área (alimentação, transporte, etc.)</li>
              </ol>
            </div>
          </div>
        </div>
      </div>

      {/* Tips and Best Practices */}
      <div className="bg-gradient-to-r from-indigo-500/10 to-cyan-500/10 border border-indigo-500/20 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-white mb-4">💡 Dicas e Boas Práticas</h2>
        <ul className="space-y-2 text-gray-300">
          <li className="flex items-start gap-2">
            <CheckCircleIcon className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
            <span><strong className="text-white">Sincronize regularmente:</strong> Mantenha seus dados atualizados sincronizando pelo menos 1x por semana</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircleIcon className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
            <span><strong className="text-white">Revise as categorias:</strong> Verifique se as transações foram categorizadas corretamente</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircleIcon className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
            <span><strong className="text-white">Acompanhe o dashboard:</strong> Use o dashboard para ter uma visão rápida da sua saúde financeira</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircleIcon className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
            <span><strong className="text-white">Segurança:</strong> Todas as conexões são seguras e regulamentadas pelo Open Banking do Banco Central</span>
          </li>
        </ul>
      </div>

      {/* Support */}
      <div className="bg-card border border-white/10 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-white mb-3">🆘 Precisa de Ajuda?</h2>
        <p className="text-gray-300">
          Se você tiver problemas ao conectar sua conta ou sincronizar transações:
        </p>
        <ul className="mt-3 space-y-2 text-gray-300 ml-6 list-disc">
          <li>Verifique se seu banco está em manutenção ou se há problemas temporários</li>
          <li>Tente desconectar e reconectar a conta</li>
          <li>Certifique-se de que suas credenciais estão corretas</li>
          <li>Aguarde alguns minutos entre tentativas de sincronização</li>
        </ul>
      </div>
      </div>
    </div>
  );
}
