import { useEffect, useRef, useCallback, useState } from 'react';
import { useAuthStore } from '@/store/auth-store';
import { toast } from 'sonner';

export type PaymentEventType = 
  | 'payment_success'
  | 'payment_failed'
  | 'subscription_updated'
  | 'payment_method_updated'
  | 'trial_ending'
  | 'usage_limit_warning';

export interface PaymentEvent {
  type: PaymentEventType;
  timestamp: string;
  [key: string]: any;
}

interface UsePaymentWebSocketOptions {
  onPaymentSuccess?: (event: PaymentEvent) => void;
  onPaymentFailed?: (event: PaymentEvent) => void;
  onSubscriptionUpdated?: (event: PaymentEvent) => void;
  onPaymentMethodUpdated?: (event: PaymentEvent) => void;
  onTrialEnding?: (event: PaymentEvent) => void;
  onUsageLimitWarning?: (event: PaymentEvent) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
}

export function usePaymentWebSocket(options: UsePaymentWebSocketOptions = {}) {
  const { user } = useAuthStore();
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<PaymentEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const {
    onPaymentSuccess,
    onPaymentFailed,
    onSubscriptionUpdated,
    onPaymentMethodUpdated,
    onTrialEnding,
    onUsageLimitWarning,
    autoReconnect = true,
    reconnectInterval = 5000,
  } = options;

  const connect = useCallback(() => {
    if (!user || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/payments/status/`;
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('Payment WebSocket connected');
        setIsConnected(true);
        
        // Start ping interval to keep connection alive
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
        }
        
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
              type: 'ping',
              timestamp: new Date().toISOString(),
            }));
          }
        }, 30000); // Ping every 30 seconds
      };

      ws.onmessage = (event) => {
        try {
          const data: PaymentEvent = JSON.parse(event.data);
          setLastEvent(data);

          // Handle different event types
          switch (data.type) {
            case 'payment_success':
              toast.success(`Payment of ${data.currency} ${data.amount} was processed successfully.`);
              onPaymentSuccess?.(data);
              break;

            case 'payment_failed':
              toast.error(data.reason || 'Payment could not be processed.');
              onPaymentFailed?.(data);
              break;

            case 'subscription_updated':
              toast.success(`Your subscription status is now: ${data.status}`);
              onSubscriptionUpdated?.(data);
              break;

            case 'payment_method_updated':
              const action = data.action === 'added' ? 'added' : 
                           data.action === 'removed' ? 'removed' : 'updated';
              toast.success(`Payment method was ${action}.`);
              onPaymentMethodUpdated?.(data);
              break;

            case 'trial_ending':
              toast.error(`Your trial ends in ${data.days_remaining} days.`);
              onTrialEnding?.(data);
              break;

            case 'usage_limit_warning':
              toast.error(`${data.usage_type} usage at ${data.percentage}% of limit.`);
              onUsageLimitWarning?.(data);
              break;

            default:
              console.log('Unknown payment event:', data);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('Payment WebSocket error:', error);
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log('Payment WebSocket disconnected');
        setIsConnected(false);
        wsRef.current = null;

        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }

        // Auto-reconnect if enabled and user is still authenticated
        if (autoReconnect && user) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect Payment WebSocket...');
            connect();
          }, reconnectInterval);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setIsConnected(false);
    }
  }, [
    user,
    autoReconnect,
    reconnectInterval,
    onPaymentSuccess,
    onPaymentFailed,
    onSubscriptionUpdated,
    onPaymentMethodUpdated,
    onTrialEnding,
    onUsageLimitWarning,
  ]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  // Connect when component mounts and user is authenticated
  useEffect(() => {
    if (user) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [user, connect, disconnect]);

  return {
    isConnected,
    lastEvent,
    sendMessage,
    connect,
    disconnect,
  };
}

// Hook for checkout-specific WebSocket
export function useCheckoutWebSocket(sessionId: string | null) {
  const [status, setStatus] = useState<'monitoring' | 'success' | 'failed' | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/payments/checkout/${sessionId}/`;
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Checkout WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'checkout_completed') {
          setStatus('success');
        } else if (data.type === 'checkout_failed') {
          setStatus('failed');
        } else if (data.type === 'checkout_status') {
          setStatus(data.status);
        }
      } catch (error) {
        console.error('Error parsing checkout WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('Checkout WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('Checkout WebSocket disconnected');
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [sessionId]);

  return { status };
}