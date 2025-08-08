'use client';

import { Button } from '@/components/ui/button';
import { 
  TrendingUp, 
  TrendingDown, 
  AlertCircle, 
  DollarSign,
  BarChart3,
  Receipt
} from 'lucide-react';
import { testId, TEST_IDS, testIdWithIndex } from '@/utils/test-helpers';

interface QuickActionsProps {
  onSelect: (message: string) => void;
}

const quickActions = [
  {
    icon: TrendingDown,
    label: 'Maiores gastos',
    message: 'Quais foram meus maiores gastos este mês?',
    gradient: 'from-red-500 to-pink-500',
    hoverGradient: 'hover:from-red-600 hover:to-pink-600',
  },
  {
    icon: DollarSign,
    label: 'Como economizar',
    message: 'Como posso reduzir minhas despesas e economizar mais?',
    gradient: 'from-green-500 to-emerald-500',
    hoverGradient: 'hover:from-green-600 hover:to-emerald-600',
  },
  {
    icon: BarChart3,
    label: 'Fluxo de caixa',
    message: 'Mostre uma análise do meu fluxo de caixa',
    gradient: 'from-blue-500 to-cyan-500',
    hoverGradient: 'hover:from-blue-600 hover:to-cyan-600',
  },
  {
    icon: AlertCircle,
    label: 'Anomalias',
    message: 'Existem transações suspeitas ou anormais nas minhas contas?',
    gradient: 'from-orange-500 to-amber-500',
    hoverGradient: 'hover:from-orange-600 hover:to-amber-600',
  },
  {
    icon: TrendingUp,
    label: 'Previsões',
    message: 'Qual é a previsão do meu saldo para os próximos 30 dias?',
    gradient: 'from-purple-500 to-pink-500',
    hoverGradient: 'hover:from-purple-600 hover:to-pink-600',
  },
  {
    icon: Receipt,
    label: 'Relatório mensal',
    message: 'Gere um relatório resumido do mês atual',
    gradient: 'from-indigo-500 to-purple-500',
    hoverGradient: 'hover:from-indigo-600 hover:to-purple-600',
  },
];

export function QuickActions({ onSelect }: QuickActionsProps) {
  return (
    <div className="mt-8" {...testId(TEST_IDS.aiInsights.quickActions)}>
      <p className="text-sm text-gray-600 mb-6 font-medium">Ou escolha uma ação rápida:</p>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-w-3xl mx-auto">
        {quickActions.map((action, index) => {
          const Icon = action.icon;
          return (
            <Button
              key={index}
              variant="outline"
              className={`h-auto flex flex-col items-center gap-3 p-4 bg-white/50 backdrop-blur-sm border-white/20 transition-all duration-300 transform hover:scale-105 hover:shadow-xl group ${action.hoverGradient} hover:text-white hover:border-transparent`}
              onClick={() => onSelect(action.message)}
              {...testIdWithIndex(TEST_IDS.aiInsights.quickActionButton, index)}
            >
              <div className={`p-2 rounded-lg bg-gradient-to-r ${action.gradient} text-white shadow-md group-hover:shadow-lg transition-all duration-300`}>
                <Icon className="h-5 w-5" />
              </div>
              <span className="text-sm font-medium text-center group-hover:text-white transition-colors duration-300">
                {action.label}
              </span>
            </Button>
          );
        })}
      </div>
    </div>
  );
}