import { useState, useEffect, useCallback, useRef } from 'react';
import { AIConversation } from '../types/ai-insights.types';
import { aiInsightsService } from '../services/ai-insights.service';
import toast from 'react-hot-toast';

// Configurações de retry
const MAX_RETRY_ATTEMPTS = 3;
const INITIAL_RETRY_DELAY = 1000; // 1 segundo
const MAX_RETRY_DELAY = 30000; // 30 segundos

interface UseConversationsOptions {
  status?: string;
  search?: string;
}

export function useConversations(options: UseConversationsOptions = {}) {
  const [conversations, setConversations] = useState<AIConversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryAttempt, setRetryAttempt] = useState(0);
  const retryTimeoutRef = useRef<NodeJS.Timeout>();
  const lastErrorTimeRef = useRef<number>(0);
  const isMountedRef = useRef(true);

  const fetchConversations = useCallback(async () => {
    if (!isMountedRef.current) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await aiInsightsService.getConversations({
        status: options.status,
        search: options.search,
        page_size: 50, // Buscar até 50 conversas
      });
      
      if (isMountedRef.current) {
        setConversations(response.results || []);
        setRetryAttempt(0); // Reset retry count on success
      }
    } catch (err: any) {
      if (!isMountedRef.current) return;
      
      // Error fetching conversations
      setError('Erro ao carregar conversas');
      
      // Evitar spam de toasts
      const now = Date.now();
      if (now - lastErrorTimeRef.current > 5000) {
        // Verificar se é erro de empresa não associada
        if (err?.response?.data?.error_code === 'NO_COMPANY') {
          toast.error('Por favor, complete seu cadastro empresarial para usar o AI Insights', {
            duration: 8000,
            id: 'no-company-error'
          });
        } else {
          toast.error('Não foi possível carregar as conversas');
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
              fetchConversations();
            }
          }, delay);
        }
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [options.status, options.search, retryAttempt]);

  const createConversation = useCallback(async (title: string = 'Nova Conversa') => {
    try {
      const conversation = await aiInsightsService.createConversation({ title });
      
      // Adicionar nova conversa à lista
      if (isMountedRef.current) {
        setConversations(prev => [conversation, ...prev]);
      }
      
      return conversation;
    } catch (err) {
      toast.error('Não foi possível criar a conversa');
      return null;
    }
  }, []);

  const archiveConversation = useCallback(async (id: string) => {
    try {
      const updated = await aiInsightsService.archiveConversation(id);
      
      // Atualizar conversa na lista
      if (isMountedRef.current) {
        setConversations(prev => prev.map(conv => 
          conv.id === id ? updated : conv
        ));
      }
      
      toast.success('Conversa arquivada');
      return updated;
    } catch (err) {
      toast.error('Não foi possível arquivar a conversa');
      return null;
    }
  }, []);

  const deleteConversation = useCallback(async (id: string) => {
    try {
      await aiInsightsService.deleteConversation(id);
      
      // Remover conversa da lista
      if (isMountedRef.current) {
        setConversations(prev => prev.filter(conv => conv.id !== id));
      }
      
      toast.success('Conversa excluída');
      return true;
    } catch (err) {
      toast.error('Não foi possível excluir a conversa');
      return false;
    }
  }, []);

  useEffect(() => {
    // Marcar como montado
    isMountedRef.current = true;
    
    // Fetch inicial
    fetchConversations();
    
    // Cleanup
    return () => {
      isMountedRef.current = false;
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, []); // Apenas na montagem

  // Effect para mudanças nas opções
  useEffect(() => {
    if (isMountedRef.current) {
      // Limpar retry timer quando as opções mudam
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        setRetryAttempt(0);
      }
      
      fetchConversations();
    }
  }, [options.status, options.search]); // Não incluir fetchConversations para evitar loop

  return {
    conversations,
    loading,
    error,
    refetch: fetchConversations,
    createConversation,
    archiveConversation,
    deleteConversation,
    retryAttempt,
    isRetrying: retryAttempt > 0 && loading,
  };
}