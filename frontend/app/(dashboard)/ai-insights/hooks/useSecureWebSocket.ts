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
    if (wsRef.current?.readyState === WebSocket.OPEN || isClosingRef.current) {
      return;
    }

    const wsUrl = getSecureUrl();
    if (!wsUrl) {
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
              const delay = Math.min(
                reconnectDelay * Math.pow(2, reconnectCountRef.current - 1),
                30000
              );
              
              // Reconnecting WebSocket connection
              setState(prev => ({
                ...prev,
                reconnectCount: reconnectCountRef.current,
              }));
              
              reconnectTimeoutRef.current = setTimeout(() => {
                connect();
              }, delay);
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
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      // WebSocket not connected
      toast.error('Connection not established. Trying to reconnect...');
      connect();
      return false;
    }

    try {
      // Reset activity on send
      resetActivityTimeout();
      
      // Validate message size (64KB limit)
      const message = JSON.stringify(data);
      if (message.length > 65536) {
        toast.error('Message too large');
        return false;
      }
      
      wsRef.current.send(message);
      return true;
    } catch (err) {
      // Error sending message
      toast.error('Failed to send message');
      return false;
    }
  }, [connect, resetActivityTimeout]);

  // Connect on mount if user is authenticated
  useEffect(() => {
    if (user) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [user, connect, disconnect]);

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