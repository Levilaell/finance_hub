import { useState, useEffect, useCallback } from 'react';
import { AIInsight } from '../types/ai-insights.types';
import { aiInsightsService } from '../services/ai-insights.service';
import toast from 'react-hot-toast';

interface UseInsightsOptions {
  priority?: string;
  status?: string;
  type?: string;
}

export function useInsights(options: UseInsightsOptions = {}) {
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInsights = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await aiInsightsService.getInsights(options);
      setInsights(data);
    } catch (err) {
      // Error fetching insights
      setError('Erro ao carregar insights');
      toast.error('Não foi possível carregar os insights');
    } finally {
      setLoading(false);
    }
  }, [options]);

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
    fetchInsights();
  }, [fetchInsights]);

  return {
    insights,
    loading,
    error,
    refetch: fetchInsights,
    markInsightViewed,
    takeAction,
    dismissInsight,
  };
}