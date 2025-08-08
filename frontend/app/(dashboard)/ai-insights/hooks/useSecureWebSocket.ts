import { useCallback, useEffect, useRef, useState } from 'react';
import { useAuthStore } from '@/store/auth-store';
import toast from 'react-hot-toast';

interface WebSocketOptions {
  url: string;
  onOpen?: () => void;
  onMessage?: (data: any) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (error: Event) => void;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  heartbeatInterval?: number;
  activityTimeout?: number;
}

interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  reconnectCount: number;
  lastError: string | null;
}

export function useSecureWebSocket(options: WebSocketOptions) {
  const {
    url,
    onOpen,
    onMessage,
    onClose,
    onError,
    reconnectAttempts = 5,
    reconnectDelay = 1000,
    heartbeatInterval = 30000,
    activityTimeout = 300000, // 5 minutes
  } = options;

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    reconnectCount: 0,
    lastError: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const activityTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectCountRef = useRef(0);
  const isClosingRef = useRef(false);
  
  const { user } = useAuthStore();

  // Reset activity timeout
  const resetActivityTimeout = useCallback(() => {
    if (activityTimeoutRef.current) {
      clearTimeout(activityTimeoutRef.current);
    }

    activityTimeoutRef.current = setTimeout(() => {
      // WebSocket inactive, closing connection
      disconnect(4002, 'Inactivity timeout');
    }, activityTimeout);
  }, [activityTimeout]);

  // Send heartbeat ping
  const sendHeartbeat = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ping' }));
    }
  }, []);

  // Start heartbeat interval
  const startHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }

    heartbeatIntervalRef.current = setInterval(() => {
      sendHeartbeat();
    }, heartbeatInterval);
  }, [heartbeatInterval, sendHeartbeat]);

  // Stop heartbeat interval
  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  // Get secure WebSocket URL with token
  const getSecureUrl = useCallback((): string | null => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setState(prev => ({ ...prev, lastError: 'No authentication token' }));
      return null;
    }

    // Prefer sending token in headers, but include in URL for compatibility
    const wsUrl = new URL(url);
    wsUrl.searchParams.set('token', token);
    
    return wsUrl.toString();
  }, [url]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    // Evitar múltiplas tentativas simultâneas
    if (wsRef.current?.readyState === WebSocket.OPEN || 
        wsRef.current?.readyState === WebSocket.CONNECTING ||
        isClosingRef.current ||
        state.isConnecting) {
      return;
    }

    // Não tentar conectar se não há URL válida
    if (!url || url === '') {
      return;
    }

    const wsUrl = getSecureUrl();
    if (!wsUrl) {
      setState(prev => ({ 
        ...prev, 
        lastError: 'Unable to establish secure connection. Please login again.',
        isConnecting: false 
      }));
      return;
    }

    setState(prev => ({ ...prev, isConnecting: true, lastError: null }));

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        // WebSocket connected successfully
        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          reconnectCount: 0,
          lastError: null,
        }));
        reconnectCountRef.current = 0;
        
        // Start heartbeat and activity monitoring
        startHeartbeat();
        resetActivityTimeout();
        
        onOpen?.();
      };

      ws.onmessage = (event) => {
        try {
          resetActivityTimeout();
          const data = JSON.parse(event.data);
          
          // Handle pong response
          if (data.type === 'pong') {
            return;
          }
          
          onMessage?.(data);
        } catch (err) {
          // Error parsing WebSocket message
        }
      };

      ws.onerror = (error) => {
        // WebSocket connection error occurred
        setState(prev => ({
          ...prev,
          lastError: 'Connection error',
        }));
        onError?.(error);
      };

      ws.onclose = (event) => {
        // WebSocket disconnected
        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
        }));
        
        stopHeartbeat();
        wsRef.current = null;
        
        // Handle different close codes
        switch (event.code) {
          case 1000: // Normal closure
          case 4002: // Inactivity timeout
            isClosingRef.current = true;
            break;
          case 4001: // Authentication error
            toast.error('Authentication failed. Please login again.');
            isClosingRef.current = true;
            break;
          case 4008: // Rate limit
            toast.error('Connection limit exceeded. Please try again later.');
            isClosingRef.current = true;
            break;
          default:
            // Attempt reconnection for other codes
            if (!isClosingRef.current && reconnectCountRef.current < reconnectAttempts) {
              reconnectCountRef.current++;
              
              // Backoff exponencial melhorado com jitter
              const baseDelay = Math.min(
                reconnectDelay * Math.pow(2, reconnectCountRef.current - 1),
                30000
              );
              // Adicionar jitter (0-25% do delay base) para evitar thundering herd
              const jitter = Math.random() * 0.25 * baseDelay;
              const delay = baseDelay + jitter;
              
              // Reconnecting WebSocket connection
              setState(prev => ({
                ...prev,
                reconnectCount: reconnectCountRef.current,
              }));
              
              if (process.env.NODE_ENV === 'development') {
                console.log(`WebSocket reconnection attempt ${reconnectCountRef.current}/${reconnectAttempts} in ${Math.round(delay)}ms`);
              }
              
              reconnectTimeoutRef.current = setTimeout(() => {
                if (!isClosingRef.current) {
                  connect();
                }
              }, delay);
            } else if (reconnectCountRef.current >= reconnectAttempts) {
              // Max reconnection attempts reached
              setState(prev => ({
                ...prev,
                lastError: 'Maximum reconnection attempts reached. Please refresh the page.',
              }));
              isClosingRef.current = true;
            }
        }
        
        onClose?.(event);
      };

      wsRef.current = ws;
    } catch (err) {
      // Error creating WebSocket connection
      setState(prev => ({
        ...prev,
        isConnecting: false,
        lastError: 'Failed to create connection',
      }));
    }
  }, [
    getSecureUrl,
    onOpen,
    onMessage,
    onError,
    onClose,
    reconnectAttempts,
    reconnectDelay,
    startHeartbeat,
    resetActivityTimeout,
  ]);

  // Disconnect WebSocket
  const disconnect = useCallback((code = 1000, reason = 'User disconnected') => {
    isClosingRef.current = true;
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (activityTimeoutRef.current) {
      clearTimeout(activityTimeoutRef.current);
      activityTimeoutRef.current = null;
    }
    
    stopHeartbeat();
    
    if (wsRef.current) {
      wsRef.current.close(code, reason);
      wsRef.current = null;
    }
    
    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
      reconnectCount: 0,
    }));
  }, [stopHeartbeat]);

  // Send message with safety checks
  const sendMessage = useCallback((data: any) => {
    // Check connection state
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      // Se está conectando, aguardar
      if (state.isConnecting) {
        toast.error('Aguardando conexão ser estabelecida...', {
          duration: 2000,
          id: 'ws-connecting'
        });
      } else {
        // Tentar reconectar apenas se não está já tentando
        toast.error('Conexão perdida. Reconectando...', {
          duration: 3000,
          id: 'ws-reconnecting'
        });
        if (!isClosingRef.current) {
          connect();
        }
      }
      return false;
    }

    try {
      // Reset activity on send
      resetActivityTimeout();
      
      // Validate message size (64KB limit)
      const message = JSON.stringify(data);
      if (message.length > 65536) {
        toast.error('Mensagem muito grande. Por favor, reduza o tamanho.');
        return false;
      }
      
      wsRef.current.send(message);
      return true;
    } catch (err) {
      // Error sending message
      if (process.env.NODE_ENV === 'development') {
        console.error('WebSocket send error:', err);
      }
      toast.error('Falha ao enviar mensagem. Tente novamente.');
      return false;
    }
  }, [connect, resetActivityTimeout, state.isConnecting]);

  // Connect on mount if user is authenticated
  useEffect(() => {
    // Só conectar se há user E URL válida
    if (user && url && url !== '') {
      // Pequeno delay para evitar race conditions
      const timer = setTimeout(() => {
        connect();
      }, 100);
      
      return () => {
        clearTimeout(timer);
        disconnect();
      };
    } else {
      // Se não há URL ou user, garantir desconexão
      return () => {
        disconnect();
      };
    }
  }, [url]); // Apenas url como dependência para evitar reconexões desnecessárias

  // Reconnect if connection is lost and should be connected
  useEffect(() => {
    const handleOnline = () => {
      if (!state.isConnected && !state.isConnecting && user && !isClosingRef.current) {
        // Network restored, reconnecting
        connect();
      }
    };

    const handleOffline = () => {
      // Network connection lost
      setState(prev => ({ ...prev, lastError: 'Network connection lost' }));
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [state.isConnected, state.isConnecting, user, connect]);

  return {
    isConnected: state.isConnected,
    isConnecting: state.isConnecting,
    reconnectCount: state.reconnectCount,
    lastError: state.lastError,
    connect,
    disconnect,
    sendMessage,
  };
}