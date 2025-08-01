import { useState, useEffect, useCallback } from 'react';
import { AICredit } from '../types/ai-insights.types';
import { aiInsightsService } from '../services/ai-insights.service';
import toast from 'react-hot-toast';

export function useCredits() {
  const [credits, setCredits] = useState<AICredit | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCredits = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await aiInsightsService.getCredits();
      setCredits(data);
    } catch (err) {
      // Error fetching credits
      setError('Erro ao carregar créditos');
      toast.error('Não foi possível carregar os créditos');
    } finally {
      setLoading(false);
    }
  }, []);

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
    fetchCredits();
  }, [fetchCredits]);

  return {
    credits,
    loading,
    error,
    refetch: fetchCredits,
    purchaseCredits,
  };
}