// frontend/hooks/usePlanLimits.ts
'use client';

import { useToast } from '@/components/ui/use-toast';
import { useRouter } from 'next/navigation';
import { useCallback } from 'react';

interface LimitError {
  error: string;
  limit_type?: 'transactions' | 'bank_accounts' | 'ai_requests';
  current?: number;
  limit?: number;
  usage_info?: {
    current: number;
    limit: number;
    remaining: number;
  };
  upgrade_required?: boolean;
  suggested_plan?: string;
  redirect?: string;
}

export function usePlanLimits() {
  const { toast } = useToast();
  const router = useRouter();
  
  const handleLimitError = useCallback((error: LimitError | any) => {
    // Se não for erro de limite, retorna false
    if (!error?.upgrade_required && !error?.limit_type) {
      return false;
    }
    
    // Mensagens específicas por tipo de limite
    const limitMessages = {
      transactions: {
        title: 'Limite de Transações Atingido',
        description: `Você atingiu o limite de ${error.limit || error.usage_info?.limit} transações mensais.`,
        action: 'Fazer Upgrade'
      },
      bank_accounts: {
        title: 'Limite de Contas Bancárias',
        description: `Você atingiu o limite de ${error.limit} contas bancárias do seu plano.`,
        action: 'Aumentar Limite'
      },
      ai_requests: {
        title: 'Limite de IA Atingido',
        description: error.usage_info 
          ? `Você usou ${error.usage_info.current} de ${error.usage_info.limit} requisições de IA este mês.`
          : 'Você atingiu o limite de requisições de IA do seu plano.',
        action: 'Obter IA Ilimitada'
      }
    };
    
    const message = limitMessages[error.limit_type as keyof typeof limitMessages] || {
      title: 'Limite do Plano Atingido',
      description: error.error || 'Você atingiu um limite do seu plano atual.',
      action: 'Fazer Upgrade'
    };
    
    // Mostrar toast com ação
    toast({
      title: message.title,
      description: message.description,
      variant: 'destructive',
      action: (
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            router.push(error.redirect || '/dashboard/subscription/upgrade');
          }}
        >
          {message.action}
        </Button>
      ),
    });
    
    return true;
  }, [toast, router]);
  
  const checkCanProceed = useCallback((
    type: 'transactions' | 'bank_accounts' | 'ai_requests',
    current: number,
    limit: number
  ): { canProceed: boolean; message?: string } => {
    if (limit === 0 || limit === 999999) {
      return { canProceed: true };
    }
    
    if (current >= limit) {
      const messages = {
        transactions: 'Você atingiu o limite de transações deste mês',
        bank_accounts: 'Você atingiu o limite de contas bancárias',
        ai_requests: 'Você atingiu o limite de requisições de IA deste mês'
      };
      
      return {
        canProceed: false,
        message: messages[type]
      };
    }
    
    return { canProceed: true };
  }, []);
  
  return {
    handleLimitError,
    checkCanProceed
  };
}

// Hook para interceptar respostas de API e tratar erros de limite
export function useApiWithLimits() {
  const { handleLimitError } = usePlanLimits();
  const { toast } = useToast();
  
  const apiCall = useCallback(async <T,>(
    fn: () => Promise<T>,
    options?: {
      onSuccess?: (data: T) => void;
      onError?: (error: any) => void;
      showSuccessToast?: boolean;
      successMessage?: string;
    }
  ): Promise<T | null> => {
    try {
      const result = await fn();
      
      if (options?.showSuccessToast) {
        toast({
          title: 'Sucesso',
          description: options.successMessage || 'Operação realizada com sucesso',
        });
      }
      
      options?.onSuccess?.(result);
      return result;
    } catch (error: any) {
      // Tenta tratar como erro de limite
      const isLimitError = handleLimitError(error.response?.data || error);
      
      // Se não for erro de limite, mostra erro genérico
      if (!isLimitError) {
        toast({
          title: 'Erro',
          description: error.response?.data?.message || error.message || 'Ocorreu um erro',
          variant: 'destructive',
        });
      }
      
      options?.onError?.(error);
      return null;
    }
  }, [handleLimitError, toast]);
  
  return { apiCall };
}

import { Button } from '@/components/ui/button';