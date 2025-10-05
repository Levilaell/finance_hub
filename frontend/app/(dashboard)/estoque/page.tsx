'use client';

import { Package, TrendingUp, AlertCircle, BarChart3, Clock } from 'lucide-react';

export default function EstoquePage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Controle de Estoque</h1>
          <p className="text-muted-foreground mt-1">
            Gerencie seu estoque de forma inteligente
          </p>
        </div>
      </div>

      {/* Coming Soon Section */}
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="text-center space-y-6 max-w-2xl px-4">
          {/* Icon */}
          <div className="flex justify-center">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full blur-xl opacity-50 animate-pulse"></div>
              <div className="relative bg-gradient-to-br from-green-500 to-emerald-500 rounded-full p-6">
                <Package className="h-16 w-16 text-white" />
              </div>
            </div>
          </div>

          {/* Title */}
          <div className="space-y-2">
            <h2 className="text-4xl font-bold bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent">
              Em Breve
            </h2>
            <p className="text-xl text-muted-foreground">
              Estamos preparando algo incrível para você
            </p>
          </div>

          {/* Description */}
          <div className="space-y-4 text-left">
            <p className="text-muted-foreground">
              Em breve você terá acesso a um sistema completo de gestão de estoque, incluindo:
            </p>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex items-start gap-3 p-4 rounded-lg border bg-card">
                <Package className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-medium mb-1">Controle de Produtos</h3>
                  <p className="text-sm text-muted-foreground">
                    Cadastro completo com fotos, categorias e fornecedores
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 rounded-lg border bg-card">
                <TrendingUp className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-medium mb-1">Movimentações</h3>
                  <p className="text-sm text-muted-foreground">
                    Entrada e saída de produtos com histórico completo
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 rounded-lg border bg-card">
                <AlertCircle className="h-5 w-5 text-orange-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-medium mb-1">Alertas de Estoque Baixo</h3>
                  <p className="text-sm text-muted-foreground">
                    Notificações quando produtos atingirem estoque mínimo
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 rounded-lg border bg-card">
                <BarChart3 className="h-5 w-5 text-purple-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-medium mb-1">Relatórios de Giro</h3>
                  <p className="text-sm text-muted-foreground">
                    Análise de produtos mais vendidos e parados
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 rounded-lg border bg-card">
                <Clock className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-medium mb-1">Controle de Validade</h3>
                  <p className="text-sm text-muted-foreground">
                    Gestão de datas de vencimento e produtos perecíveis
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 rounded-lg border bg-card">
                <Package className="h-5 w-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-medium mb-1">Integração Financeira</h3>
                  <p className="text-sm text-muted-foreground">
                    Sincronização automática com suas transações
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Call to Action */}
          <div className="pt-4">
            <p className="text-sm text-muted-foreground">
              Continue usando o CaixaHub e você será notificado quando este recurso estiver disponível.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
