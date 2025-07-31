import { useState, useEffect, useCallback, useRef } from 'react';
import { AIMessage, AIConversation, WSMessage, WSAIResponse, WSError, WSTypingIndicator } from '../types/ai-insights.types';
import { aiInsightsService } from '../services/ai-insights.service';
import { useAuthStore } from '@/store/auth-store';
import toast from 'react-hot-toast';

export function useChat(conversationId: string | null) {
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  
  const { user } = useAuthStore();

  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    if (!conversationId || !user || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }
    
    const token = localStorage.getItem('access_token');
    if (!token) {
      return;
    }

    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/ai-chat/${conversationId}/?token=${token}`;
    
    try {
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data: WSMessage = JSON.parse(event.data);
          
          switch (data.type) {
            case 'connection_established':
              console.log('Connection established:', data.message);
              break;
              
            case 'ai_response':
              const response = data as WSAIResponse;
              const aiMessage: AIMessage = {
                id: response.message_id,
                role: 'assistant',
                content: response.message,
                credits_used: response.credits_used,
                structured_data: response.structured_data,
                insights: response.insights,
                created_at: response.created_at,
              };
              setMessages(prev => [...prev, aiMessage]);
              setIsTyping(false);
              
              // Update credits in global store if needed
              if (response.credits_remaining !== undefined) {
                // TODO: Update credits in store
              }
              break;
              
            case 'assistant_typing':
              const typingData = data as WSTypingIndicator;
              setIsTyping(typingData.typing);
              break;
              
            case 'error':
              const errorData = data as WSError;
              setError(errorData.message);
              setIsTyping(false);
              
              if (errorData.error === 'insufficient_credits') {
                toast.error(`Créditos insuficientes: ${errorData.message}`);
              }
              break;
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Erro de conexão');
        setConnected(false);
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setConnected(false);
        wsRef.current = null;
        
        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && reconnectAttemptsRef.current < 5) {
          reconnectAttemptsRef.current++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`);
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, delay);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Error creating WebSocket:', err);
      setError('Falha ao conectar');
      setConnected(false);
    }
  }, [conversationId, user]);

  // Disconnect WebSocket
  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }
    
    setConnected(false);
    reconnectAttemptsRef.current = 0;
  }, []);

  // Load existing messages
  const loadMessages = useCallback(async () => {
    if (!conversationId) return;

    setLoading(true);
    setError(null);
    
    try {
      const data = await aiInsightsService.getConversationMessages(conversationId);
      setMessages(data);
    } catch (err) {
      console.error('Error loading messages:', err);
      setError('Erro ao carregar mensagens');
      toast.error('Não foi possível carregar as mensagens');
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  // Send message
  const sendMessage = useCallback(async (content: string, convId?: string) => {
    const targetConvId = convId || conversationId;
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN || !targetConvId) {
      toast.error('Conexão não estabelecida. Tentando reconectar...');
      connectWebSocket();
      return;
    }

    // Add user message optimistically
    const userMessage: AIMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setError(null);
    
    // Send via WebSocket
    wsRef.current.send(JSON.stringify({
      type: 'message',
      message: content,
    }));
  }, [conversationId, connectWebSocket]);

  // Create new conversation
  const createConversation = useCallback(async () => {
    try {
      const conversation = await aiInsightsService.createConversation({
        title: 'Nova Conversa',
      });
      return conversation;
    } catch (err) {
      console.error('Error creating conversation:', err);
      toast.error('Não foi possível criar a conversa');
      return null;
    }
  }, []);

  // Send typing indicator
  const sendTypingIndicator = useCallback((typing: boolean) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'typing',
        typing,
      }));
    }
  }, []);

  // Effects
  useEffect(() => {
    if (conversationId) {
      loadMessages();
      connectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [conversationId, loadMessages, connectWebSocket, disconnectWebSocket]);

  return {
    messages,
    loading,
    isTyping,
    error,
    connected,
    sendMessage,
    createConversation,
    sendTypingIndicator,
  };
}