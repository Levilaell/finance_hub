import { useState, useEffect, useCallback, useRef } from 'react';
import { AICredit } from '../types/ai-insights.types';
import { aiInsightsService } from '../services/ai-insights.service';
import toast from 'react-hot-toast';

// Configurações de retry
const MAX_RETRY_ATTEMPTS = 3;
const INITIAL_RETRY_DELAY = 1000; // 1 segundo
const MAX_RETRY_DELAY = 30000; // 30 segundos

export function useCredits() {
  const [credits, setCredits] = useState<AICredit | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryAttempt, setRetryAttempt] = useState(0);
  const retryTimeoutRef = useRef<NodeJS.Timeout>();
  const lastErrorTimeRef = useRef<number>(0);
  const isMountedRef = useRef(true);

  const fetchCredits = useCallback(async () => {
    if (!isMountedRef.current) return;
    
    try {
      setLoading(true);
      setError(null);
      const data = await aiInsightsService.getCredits();
      
      if (isMountedRef.current) {
        setCredits(data);
        setRetryAttempt(0); // Reset retry count on success
      }
    } catch (err: any) {
      if (!isMountedRef.current) return;
      
      // Error fetching credits
      setError('Erro ao carregar créditos');
      
      // Evitar spam de toasts - mostrar apenas se passou mais de 5 segundos desde o último erro
      const now = Date.now();
      if (now - lastErrorTimeRef.current > 5000) {
        // Verificar se é erro de empresa não associada
        if (err?.response?.data?.error_code === 'NO_COMPANY') {
          toast.error('Por favor, complete seu cadastro empresarial para usar o AI Insights', {
            duration: 8000,
            id: 'no-company-error'
          });
        } else {
          toast.error('Não foi possível carregar os créditos');
        }
        lastErrorTimeRef.current = now;
      }
      
      // Implementar retry com backoff exponencial
      if (retryAttempt < MAX_RETRY_ATTEMPTS && err?.response?.status !== 403) {
        const delay = Math.min(
          INITIAL_RETRY_DELAY * Math.pow(2, retryAttempt),
          MAX_RETRY_DELAY
        );
        
        if (isMountedRef.current) {
          setRetryAttempt(prev => prev + 1);
          retryTimeoutRef.current = setTimeout(() => {
            if (isMountedRef.current) {
              fetchCredits();
            }
          }, delay);
        }
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [retryAttempt]);

  const purchaseCredits = useCallback(async (amount: number, paymentMethodId: string) => {
    try {
      const response = await aiInsightsService.purchaseCredits({
        amount,
        payment_method_id: paymentMethodId,
      });
      
      // Refresh credits after purchase
      await fetchCredits();
      
      toast.success(`${amount} créditos foram adicionados à sua conta!`);
      
      return response;
    } catch (err) {
      // Error purchasing credits
      toast.error('Não foi possível processar sua compra. Tente novamente.');
      throw err;
    }
  }, [fetchCredits]);

  useEffect(() => {
    // Marcar como montado
    isMountedRef.current = true;
    
    // Fetch inicial apenas uma vez
    fetchCredits();
    
    // Cleanup
    return () => {
      isMountedRef.current = false;
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, []); // Dependência vazia para executar apenas na montagem

  return {
    credits,
    loading,
    error,
    refetch: fetchCredits,
    purchaseCredits,
    retryAttempt,
    isRetrying: retryAttempt > 0 && loading,
  };
}