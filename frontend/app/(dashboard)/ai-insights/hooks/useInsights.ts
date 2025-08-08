import { useState, useEffect, useCallback, useRef } from 'react';
import { AIInsight } from '../types/ai-insights.types';
import { aiInsightsService } from '../services/ai-insights.service';
import toast from 'react-hot-toast';

interface UseInsightsOptions {
  priority?: string;
  status?: string;
  type?: string;
}

// Configurações de retry
const MAX_RETRY_ATTEMPTS = 3;
const INITIAL_RETRY_DELAY = 1000; // 1 segundo
const MAX_RETRY_DELAY = 30000; // 30 segundos

export function useInsights(options: UseInsightsOptions = {}) {
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [retryAttempt, setRetryAttempt] = useState(0);
  const debounceTimerRef = useRef<NodeJS.Timeout>();
  const lastErrorTimeRef = useRef<number>(0);
  const retryTimeoutRef = useRef<NodeJS.Timeout>();
  const isMountedRef = useRef(true);

  const fetchInsights = useCallback(async () => {
    if (!isMountedRef.current) return;
    
    try {
      setLoading(true);
      setError(null);
      const data = await aiInsightsService.getInsights(options);
      
      if (isMountedRef.current) {
        setInsights(data);
        setRetryAttempt(0); // Reset retry count on success
      }
    } catch (err: any) {
      if (!isMountedRef.current) return;
      
      // Error fetching insights
      setError('Erro ao carregar insights');
      
      // Prevent error toast spam - only show if more than 5 seconds since last error
      const now = Date.now();
      if (now - lastErrorTimeRef.current > 5000) {
        // Check for specific errors
        if (err?.response?.data?.error_code === 'NO_COMPANY') {
          toast.error('Por favor, complete seu cadastro empresarial para ver insights', {
            duration: 8000,
            id: 'no-company-error'
          });
        } else if (err?.response?.status === 429) {
          toast.error('Muitas requisições. Por favor, aguarde um momento.');
        } else {
          toast.error('Não foi possível carregar os insights');
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
              fetchInsights();
            }
          }, delay);
        }
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [options.priority, options.status, options.type, retryAttempt]); // Use primitive values instead of object reference

  const markInsightViewed = useCallback(async (insightId: string) => {
    try {
      await aiInsightsService.markInsightViewed(insightId);
      
      // Update local state
      setInsights(prev => prev.map(insight => 
        insight.id === insightId 
          ? { ...insight, status: 'viewed', viewed_at: new Date().toISOString() }
          : insight
      ));
    } catch (err) {
      // Error marking insight as viewed
    }
  }, []);

  const takeAction = useCallback(async (insightId: string, data: {
    action_taken: boolean;
    actual_impact?: number;
    user_feedback?: string;
  }) => {
    try {
      await aiInsightsService.takeInsightAction(insightId, data);
      
      // Update local state
      setInsights(prev => prev.map(insight => 
        insight.id === insightId 
          ? { 
              ...insight, 
              status: 'completed',
              action_taken: true,
              action_taken_at: new Date().toISOString(),
              actual_impact: data.actual_impact,
              user_feedback: data.user_feedback,
            }
          : insight
      ));
      
      toast.success('O insight foi marcado como concluído.');
    } catch (err) {
      // Error taking action on insight
      toast.error('Não foi possível registrar a ação');
    }
  }, []);

  const dismissInsight = useCallback(async (insightId: string, reason?: string) => {
    try {
      await aiInsightsService.dismissInsight(insightId, reason);
      
      // Update local state
      setInsights(prev => prev.map(insight => 
        insight.id === insightId 
          ? { ...insight, status: 'dismissed' }
          : insight
      ));
      
      toast.success('O insight foi removido da lista.');
    } catch (err) {
      // Error dismissing insight
      toast.error('Não foi possível descartar o insight');
    }
  }, []);

  useEffect(() => {
    // Marcar como montado
    isMountedRef.current = true;
    
    // Only fetch on initial load
    if (isInitialLoad) {
      fetchInsights();
      setIsInitialLoad(false);
    }
    
    // Cleanup on unmount
    return () => {
      isMountedRef.current = false;
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []); // Empty dependency for initial load only
  
  // Separate effect for filter changes with debounce
  useEffect(() => {
    if (!isInitialLoad && isMountedRef.current) {
      // Clear existing timer
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      
      // Clear retry timer if filters change
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        setRetryAttempt(0);
      }
      
      // Set new timer
      debounceTimerRef.current = setTimeout(() => {
        if (isMountedRef.current) {
          fetchInsights();
        }
      }, 300); // 300ms debounce
    }
  }, [options.priority, options.status, options.type, fetchInsights]); // Include fetchInsights for completeness

  return {
    insights,
    loading,
    error,
    refetch: fetchInsights,
    markInsightViewed,
    takeAction,
    dismissInsight,
    retryAttempt,
    isRetrying: retryAttempt > 0 && loading,
  };
}