// frontend/components/PlanLimitAlert.tsx
'use client';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertTriangle, TrendingUp, X } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

interface PlanLimitAlertProps {
  type: 'transactions' | 'bank_accounts' | 'ai_requests';
  current: number;
  limit: number;
  percentage?: number;
  dismissible?: boolean;
  className?: string;
}

export function PlanLimitAlert({ 
  type, 
  current, 
  limit, 
  percentage, 
  dismissible = true,
  className 
}: PlanLimitAlertProps) {
  const router = useRouter();
  const [dismissed, setDismissed] = useState(false);
  
  if (dismissed) return null;
  
  const actualPercentage = percentage || (limit > 0 ? (current / limit) * 100 : 0);
  const remaining = Math.max(0, limit - current);
  
  // Determinar severity
  let variant: 'default' | 'destructive' = 'default';
  let showAlert = false;
  
  if (actualPercentage >= 100) {
    variant = 'destructive';
    showAlert = true;
  } else if (actualPercentage >= 90) {
    variant = 'destructive';
    showAlert = true;
  } else if (actualPercentage >= 80) {
    variant = 'default';
    showAlert = true;
  }
  
  if (!showAlert) return null;
  
  // Mensagens específicas por tipo
  const messages = {
    transactions: {
      title: actualPercentage >= 100 ? 'Limite de Transações Atingido' : 'Aproximando do Limite de Transações',
      description: actualPercentage >= 100 
        ? `Você atingiu o limite de ${limit} transações mensais. Faça upgrade para continuar adicionando transações.`
        : `Você já usou ${current} de ${limit} transações este mês. Restam apenas ${remaining} transações.`,
      action: 'Aumentar Limite'
    },
    bank_accounts: {
      title: 'Limite de Contas Bancárias',
      description: actualPercentage >= 100
        ? `Você atingiu o limite de ${limit} contas bancárias do seu plano.`
        : `Você tem ${current} de ${limit} contas bancárias permitidas.`,
      action: 'Adicionar Mais Contas'
    },
    ai_requests: {
      title: actualPercentage >= 100 ? 'Limite de IA Atingido' : 'Aproximando do Limite de IA',
      description: actualPercentage >= 100
        ? `Você usou todas as ${limit} requisições de IA deste mês. Faça upgrade para continuar usando IA.`
        : `Você já usou ${current} de ${limit} requisições de IA. Restam apenas ${remaining} requisições.`,
      action: 'Obter IA Ilimitada'
    }
  };
  
  const message = messages[type];
  
  return (
    <Alert variant={variant} className={className}>
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle className="flex items-center justify-between">
        {message.title}
        {dismissible && (
          <Button
            variant="ghost"
            size="icon"
            className="h-4 w-4 p-0 hover:bg-transparent"
            onClick={() => setDismissed(true)}
          >
            <X className="h-3 w-3" />
          </Button>
        )}
      </AlertTitle>
      <AlertDescription className="space-y-2">
        <p>{message.description}</p>
        {actualPercentage >= 80 && (
          <Button 
            size="sm" 
            variant={actualPercentage >= 100 ? 'default' : 'outline'}
            onClick={() => router.push('/dashboard/subscription/upgrade')}
          >
            <TrendingUp className="h-3 w-3 mr-1" />
            {message.action}
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}

// Hook para usar em formulários
export function usePlanLimitCheck(
  type: 'transactions' | 'bank_accounts' | 'ai_requests',
  current: number,
  limit: number
) {
  const canProceed = limit === 0 || current < limit;
  const percentage = limit > 0 ? (current / limit) * 100 : 0;
  const remaining = Math.max(0, limit - current);
  
  return {
    canProceed,
    percentage,
    remaining,
    isAtLimit: percentage >= 100,
    isNearLimit: percentage >= 80,
    isCritical: percentage >= 90
  };
}