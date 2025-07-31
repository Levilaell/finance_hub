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

interface QuickActionsProps {
  onSelect: (message: string) => void;
}

const quickActions = [
  {
    icon: TrendingDown,
    label: 'Maiores gastos',
    message: 'Quais foram meus maiores gastos este mês?',
    color: 'text-red-600',
  },
  {
    icon: DollarSign,
    label: 'Como economizar',
    message: 'Como posso reduzir minhas despesas e economizar mais?',
    color: 'text-green-600',
  },
  {
    icon: BarChart3,
    label: 'Fluxo de caixa',
    message: 'Mostre uma análise do meu fluxo de caixa',
    color: 'text-blue-600',
  },
  {
    icon: AlertCircle,
    label: 'Anomalias',
    message: 'Existem transações suspeitas ou anormais nas minhas contas?',
    color: 'text-orange-600',
  },
  {
    icon: TrendingUp,
    label: 'Previsões',
    message: 'Qual é a previsão do meu saldo para os próximos 30 dias?',
    color: 'text-purple-600',
  },
  {
    icon: Receipt,
    label: 'Relatório mensal',
    message: 'Gere um relatório resumido do mês atual',
    color: 'text-indigo-600',
  },
];

export function QuickActions({ onSelect }: QuickActionsProps) {
  return (
    <div className="mt-8">
      <p className="text-sm text-gray-500 mb-4">Ou escolha uma ação rápida:</p>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-w-2xl mx-auto">
        {quickActions.map((action, index) => {
          const Icon = action.icon;
          return (
            <Button
              key={index}
              variant="outline"
              className="h-auto flex flex-col items-center gap-2 p-4 hover:shadow-md transition-shadow"
              onClick={() => onSelect(action.message)}
            >
              <Icon className={`h-6 w-6 ${action.color}`} />
              <span className="text-sm font-medium text-center">
                {action.label}
              </span>
            </Button>
          );
        })}
      </div>
    </div>
  );
}