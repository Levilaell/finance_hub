/**
 * Tests for usePaymentWebSocket hook
 */
import { renderHook, act } from '@testing-library/react';
import { usePaymentWebSocket } from '../../../hooks/usePaymentWebSocket';

// Mock WebSocket
const mockWebSocket = {
  send: jest.fn(),
  close: jest.fn(),
  readyState: WebSocket.OPEN,
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
};

// Mock WebSocket constructor
(global as any).WebSocket = jest.fn(() => mockWebSocket);

// Mock toast notifications
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
}));

// Mock environment variables
Object.defineProperty(process.env, 'NEXT_PUBLIC_WS_URL', {
  value: 'ws://localhost:8000',
  writable: false,
});

describe('usePaymentWebSocket', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockWebSocket.readyState = WebSocket.OPEN;
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('initializes with default state', () => {
    const { result } = renderHook(() => usePaymentWebSocket());

    expect(result.current.isConnected).toBe(false);
    expect(result.current.paymentStatus).toBe(null);
    expect(result.current.lastMessage).toBe(null);
    expect(result.current.error).toBe(null);
  });

  it('connects to WebSocket on mount', () => {
    renderHook(() => usePaymentWebSocket());

    expect(WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws/payments/');
  });

  it('sets connected state when WebSocket opens', () => {
    const { result } = renderHook(() => usePaymentWebSocket());

    // Simulate WebSocket open event
    const openListener = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'open'
    )[1];

    act(() => {
      openListener();
    });

    expect(result.current.isConnected).toBe(true);
    expect(result.current.error).toBe(null);
  });

  it('handles payment status updates', () => {
    const { result } = renderHook(() => usePaymentWebSocket());

    // Get the message event listener
    const messageListener = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'message'
    )[1];

    // Simulate payment status message
    act(() => {
      messageListener({
        data: JSON.stringify({
          type: 'payment_status',
          status: 'succeeded',
          payment_intent_id: 'pi_1234567890',
          amount: 2999,
          currency: 'usd',
        }),
      });
    });

    expect(result.current.paymentStatus).toEqual({
      type: 'payment_status',
      status: 'succeeded',
      payment_intent_id: 'pi_1234567890',
      amount: 2999,
      currency: 'usd',
    });
    expect(result.current.lastMessage).toEqual({
      type: 'payment_status',
      status: 'succeeded',
      payment_intent_id: 'pi_1234567890',
      amount: 2999,
      currency: 'usd',
    });
  });

  it('handles subscription updates', () => {
    const { result } = renderHook(() => usePaymentWebSocket());

    const messageListener = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'message'
    )[1];

    act(() => {
      messageListener({
        data: JSON.stringify({
          type: 'subscription_update',
          subscription_id: 'sub_1234567890',
          status: 'active',
          plan: {
            id: 'premium',
            name: 'Premium Plan',
          },
        }),
      });
    });

    expect(result.current.lastMessage?.type).toBe('subscription_update');
    expect(result.current.lastMessage?.subscription_id).toBe('sub_1234567890');
  });

  it('handles payment failure notifications', () => {
    const { result } = renderHook(() => usePaymentWebSocket());

    const messageListener = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'message'
    )[1];

    act(() => {
      messageListener({
        data: JSON.stringify({
          type: 'payment_failed',
          payment_intent_id: 'pi_1234567890',
          error: {
            type: 'card_error',
            code: 'card_declined',
            message: 'Your card was declined.',
          },
        }),
      });
    });

    expect(result.current.paymentStatus?.status).toBe('failed');
    expect(result.current.lastMessage?.type).toBe('payment_failed');
    const { toast } = require('sonner');
    expect(toast.error).toHaveBeenCalledWith(
      'Payment failed: Your card was declined.'
    );
  });

  it('handles usage limit warnings', () => {
    const { result } = renderHook(() => usePaymentWebSocket());

    const messageListener = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'message'
    )[1];

    act(() => {
      messageListener({
        data: JSON.stringify({
          type: 'usage_warning',
          resource: 'transactions',
          current: 900,
          limit: 1000,
          percentage: 90,
          message: 'You have used 90% of your transaction limit',
        }),
      });
    });

    expect(result.current.lastMessage?.type).toBe('usage_warning');
    const { toast } = require('sonner');
    expect(toast.info).toHaveBeenCalledWith(
      'Usage Alert: You have used 90% of your transaction limit'
    );
  });

  it('handles connection errors', () => {
    const { result } = renderHook(() => usePaymentWebSocket());

    const errorListener = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'error'
    )[1];

    act(() => {
      errorListener({ error: 'Connection failed' });
    });

    expect(result.current.error).toBe('WebSocket connection error');
    expect(result.current.isConnected).toBe(false);
  });

  it('handles connection close', () => {
    const { result } = renderHook(() => usePaymentWebSocket());

    // First set connected state
    const openListener = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'open'
    )[1];

    act(() => {
      openListener();
    });

    expect(result.current.isConnected).toBe(true);

    // Then simulate close
    const closeListener = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'close'
    )[1];

    act(() => {
      closeListener({ wasClean: false, code: 1006 });
    });

    expect(result.current.isConnected).toBe(false);
  });

  it('attempts to reconnect on abnormal close', async () => {
    const { result } = renderHook(() => usePaymentWebSocket());

    const closeListener = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'close'
    )[1];

    // Mock setTimeout to avoid actual delays
    jest.useFakeTimers();

    act(() => {
      closeListener({ wasClean: false, code: 1006 });
    });

    // Fast-forward timers to trigger reconnection
    act(() => {
      jest.advanceTimersByTime(3000);
    });

    // Should attempt to create a new WebSocket connection
    expect(WebSocket).toHaveBeenCalledTimes(2);

    jest.useRealTimers();
  });

  it('sends subscription to payment updates', () => {
    const { result } = renderHook(() => usePaymentWebSocket());

    // Simulate connected state
    const openListener = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'open'
    )[1];

    act(() => {
      openListener();
    });

    // Subscribe to payment updates
    act(() => {
      result.current.subscribeToPayment('pi_1234567890');
    });

    expect(mockWebSocket.send).toHaveBeenCalledWith(
      JSON.stringify({
        type: 'subscribe_payment',
        payment_intent_id: 'pi_1234567890',
      })
    );
  });

  it('sends unsubscription from payment updates', () => {
    const { result } = renderHook(() => usePaymentWebSocket());

    // Simulate connected state
    const openListener = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'open'
    )[1];

    act(() => {
      openListener();
    });

    // Unsubscribe from payment updates
    act(() => {
      result.current.unsubscribeFromPayment('pi_1234567890');
    });

    expect(mockWebSocket.send).toHaveBeenCalledWith(
      JSON.stringify({
        type: 'unsubscribe_payment',
        payment_intent_id: 'pi_1234567890',
      })
    );
  });

  it('handles invalid JSON messages gracefully', () => {
    const { result } = renderHook(() => usePaymentWebSocket());

    const messageListener = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'message'
    )[1];

    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    act(() => {
      messageListener({
        data: 'invalid json {',
      });
    });

    expect(consoleSpy).toHaveBeenCalledWith(
      'Failed to parse WebSocket message:',
      expect.any(Error)
    );
    expect(result.current.error).toBe('Failed to parse message');

    consoleSpy.mockRestore();
  });

  it('queues messages when not connected', () => {
    mockWebSocket.readyState = WebSocket.CONNECTING;
    const { result } = renderHook(() => usePaymentWebSocket());

    // Try to send message while not connected
    act(() => {
      result.current.subscribeToPayment('pi_1234567890');
    });

    // Should not send immediately
    expect(mockWebSocket.send).not.toHaveBeenCalled();

    // Simulate connection opened
    mockWebSocket.readyState = WebSocket.OPEN;
    const openListener = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'open'
    )[1];

    act(() => {
      openListener();
    });

    // Should now send queued message
    expect(mockWebSocket.send).toHaveBeenCalledWith(
      JSON.stringify({
        type: 'subscribe_payment',
        payment_intent_id: 'pi_1234567890',
      })
    );
  });

  it('cleans up WebSocket on unmount', () => {
    const { unmount } = renderHook(() => usePaymentWebSocket());

    unmount();

    expect(mockWebSocket.close).toHaveBeenCalled();
  });

  it('handles heartbeat messages', () => {
    const { result } = renderHook(() => usePaymentWebSocket());

    const messageListener = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'message'
    )[1];

    act(() => {
      messageListener({
        data: JSON.stringify({
          type: 'heartbeat',
          timestamp: Date.now(),
        }),
      });
    });

    // Should respond with pong
    expect(mockWebSocket.send).toHaveBeenCalledWith(
      JSON.stringify({
        type: 'pong',
        timestamp: expect.any(Number),
      })
    );
  });

  it('handles rate limit messages', () => {
    const { result } = renderHook(() => usePaymentWebSocket());

    const messageListener = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'message'
    )[1];

    act(() => {
      messageListener({
        data: JSON.stringify({
          type: 'rate_limit',
          message: 'Too many requests. Please wait.',
          retry_after: 30,
        }),
      });
    });

    expect(result.current.error).toBe('Rate limited. Please wait 30 seconds.');
    const { toast } = require('sonner');
    expect(toast.error).toHaveBeenCalledWith(
      'Rate limited. Please wait 30 seconds.'
    );
  });
});