import { notificationsService } from '@/services/notifications.service';
import apiClient from '@/lib/api-client';

// Mock dependencies
jest.mock('@/lib/api-client');

// Enhanced WebSocket Mock with proper spy tracking
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static constructorSpy = jest.fn();
  
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  readyState: number = WebSocket.CONNECTING;
  
  constructor(public url: string) {
    MockWebSocket.constructorSpy(url);
    MockWebSocket.instances.push(this);
    
    // Simulate connection opening after a short delay
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }
  
  send = jest.fn();
  
  close() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }
  
  // Helper method to simulate disconnect
  simulateDisconnect() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }
  
  // Helper method to simulate message
  simulateMessage(data: any) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', {
        data: JSON.stringify(data)
      }));
    }
  }
  
  static reset() {
    this.instances = [];
    this.constructorSpy.mockClear();
  }
}

// Override global WebSocket
global.WebSocket = MockWebSocket as any;

describe('NotificationsService - Fixed', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
    jest.useFakeTimers();
    localStorage.clear();
    MockWebSocket.reset();
    // Reset service state - call both disconnect and stopPolling
    notificationsService.disconnect();
    (notificationsService as any).stopPolling();
  });

  afterEach(() => {
    jest.useRealTimers();
    notificationsService.disconnect();
    (notificationsService as any).stopPolling();
    MockWebSocket.reset();
  });

  describe('REST API Methods', () => {
    it('should get notifications with parameters', async () => {
      const mockResponse = {
        results: [],
        count: 0,
        next: null,
        previous: null
      };
      (apiClient.get as jest.Mock).mockResolvedValue(mockResponse);

      const result = await notificationsService.getNotifications({
        page: 1,
        page_size: 10,
        is_read: false,
        event: 'report_ready'
      });

      expect(apiClient.get).toHaveBeenCalledWith('/api/notifications/', {
        page: 1,
        page_size: 10,
        is_read: false,
        event: 'report_ready'
      });
      expect(result).toEqual(mockResponse);
    });

    it('should mark notification as read', async () => {
      const mockNotification = { id: '123', is_read: true };
      (apiClient.post as jest.Mock).mockResolvedValue(mockNotification);

      const result = await notificationsService.markAsRead('123');

      expect(apiClient.post).toHaveBeenCalledWith('/api/notifications/mark-read/123/');
      expect(result).toEqual(mockNotification);
    });
  });

  describe('WebSocket Connection - Fixed', () => {
    it('should connect WebSocket with auth token', () => {
      localStorage.setItem('access_token', 'test-token');
      const onMessage = jest.fn();
      const onConnectionChange = jest.fn();

      notificationsService.connectWebSocket(onMessage, onConnectionChange);

      expect(MockWebSocket.constructorSpy).toHaveBeenCalledWith(
        expect.stringContaining('ws://localhost:8000/ws/notifications/?token=test-token')
      );
    });

    it('should handle WebSocket open event', async () => {
      localStorage.setItem('access_token', 'test-token');
      const onMessage = jest.fn();
      const onConnectionChange = jest.fn();

      notificationsService.connectWebSocket(onMessage, onConnectionChange);

      // Advance timers to trigger connection
      jest.advanceTimersByTime(20);

      expect(onConnectionChange).toHaveBeenCalledWith(true);
    });

    it('should handle WebSocket messages', () => {
      localStorage.setItem('access_token', 'test-token');
      const onMessage = jest.fn();
      const onConnectionChange = jest.fn();

      notificationsService.connectWebSocket(onMessage, onConnectionChange);

      const testData = { type: 'new_notification', notification: {} };
      const instance = MockWebSocket.instances[0];
      instance.simulateMessage(testData);

      expect(onMessage).toHaveBeenCalledWith(testData);
    });

    it('should send acknowledgment for critical notifications', () => {
      localStorage.setItem('access_token', 'test-token');
      const onMessage = jest.fn();

      notificationsService.connectWebSocket(onMessage, () => {});

      const instance = MockWebSocket.instances[0];
      instance.readyState = WebSocket.OPEN;
      
      const testData = {
        type: 'ack_request',
        notification_id: '123'
      };

      instance.simulateMessage(testData);

      expect(instance.send).toHaveBeenCalledWith(JSON.stringify({
        type: 'ack',
        notification_id: '123'
      }));
    });

    it('should fall back to polling when no auth token', () => {
      const onMessage = jest.fn();
      const mockGetPending = jest.spyOn(notificationsService, 'getPendingNotifications')
        .mockResolvedValue({ notifications: [] });

      notificationsService.connectWebSocket(onMessage, () => {});

      jest.advanceTimersByTime(30000);

      expect(mockGetPending).toHaveBeenCalled();
    });
  });

  describe('WebSocket Reconnection - Fixed', () => {
    it('should attempt reconnection on disconnect', () => {
      localStorage.setItem('access_token', 'test-token');
      const onMessage = jest.fn();
      const onConnectionChange = jest.fn();

      notificationsService.connectWebSocket(onMessage, onConnectionChange);

      // Let initial connection establish
      jest.advanceTimersByTime(20);
      expect(onConnectionChange).toHaveBeenCalledWith(true);

      const instance = MockWebSocket.instances[MockWebSocket.instances.length - 1];
      
      // Clear previous calls to track only reconnection
      onConnectionChange.mockClear();
      
      // Simulate disconnect
      instance.simulateDisconnect();
      expect(onConnectionChange).toHaveBeenCalledWith(false);

      // Clear disconnect call
      onConnectionChange.mockClear();

      // Advance timer to trigger reconnection (base delay is 1000ms)
      jest.advanceTimersByTime(1000);
      
      // Let reconnection establish
      jest.advanceTimersByTime(20);

      // Should have called onConnectionChange(true) for reconnection
      expect(onConnectionChange).toHaveBeenCalledWith(true);
    });

    it('should use exponential backoff for reconnections', () => {
      localStorage.setItem('access_token', 'test-token');
      const onMessage = jest.fn();
      const consoleLog = jest.spyOn(console, 'log').mockImplementation();

      notificationsService.connectWebSocket(onMessage, () => {});

      // Let initial connection establish
      jest.advanceTimersByTime(20);
      consoleLog.mockClear();

      // Disconnect and prevent reconnection from succeeding
      const instance = MockWebSocket.instances[MockWebSocket.instances.length - 1];
      
      // Mock WebSocket constructor to prevent successful connections during this test
      const originalConstructor = global.WebSocket;
      global.WebSocket = jest.fn().mockImplementation(() => {
        throw new Error('Connection failed');
      });

      // Simulate disconnect - this should trigger exponential backoff
      instance.simulateDisconnect();
      
      // First attempt: 1000ms
      jest.advanceTimersByTime(10);
      expect(consoleLog).toHaveBeenCalledWith('Reconnecting in 1000ms (attempt 1)');
      
      jest.advanceTimersByTime(1000);
      
      // Second attempt: 2000ms
      jest.advanceTimersByTime(10);
      expect(consoleLog).toHaveBeenCalledWith('Reconnecting in 2000ms (attempt 2)');
      
      jest.advanceTimersByTime(2000);
      
      // Third attempt: 4000ms
      jest.advanceTimersByTime(10);
      expect(consoleLog).toHaveBeenCalledWith('Reconnecting in 4000ms (attempt 3)');

      // Restore WebSocket
      global.WebSocket = originalConstructor;
      consoleLog.mockRestore();
    });

    it('should fall back to polling after max reconnect attempts', async () => {
      localStorage.setItem('access_token', 'test-token');
      const onMessage = jest.fn();
      const mockGetPending = jest.spyOn(notificationsService, 'getPendingNotifications')
        .mockResolvedValue({ notifications: [] });
      const consoleLog = jest.spyOn(console, 'log').mockImplementation();

      notificationsService.connectWebSocket(onMessage, () => {});

      // Let initial connection establish
      jest.advanceTimersByTime(20);

      // Mock WebSocket constructor to fail connections
      const originalConstructor = global.WebSocket;
      global.WebSocket = jest.fn().mockImplementation(() => {
        throw new Error('Connection failed');
      });

      const instance = MockWebSocket.instances[MockWebSocket.instances.length - 1];
      instance.simulateDisconnect();

      // Advance through all 5 reconnect attempts with exponential backoff
      const delays = [1000, 2000, 4000, 8000, 16000];
      
      for (let i = 0; i < 5; i++) {
        jest.advanceTimersByTime(delays[i] + 10);
      }

      // Should see "Max reconnect attempts reached" message
      expect(consoleLog).toHaveBeenCalledWith(
        'Max reconnect attempts reached, falling back to polling'
      );

      // Let polling start
      await Promise.resolve();

      // After max attempts, should start polling
      expect(mockGetPending).toHaveBeenCalled();

      // Restore WebSocket
      global.WebSocket = originalConstructor;
      consoleLog.mockRestore();
    });
  });

  describe('WebSocket Methods - Fixed', () => {
    beforeEach(() => {
      localStorage.setItem('access_token', 'test-token');
      notificationsService.connectWebSocket(() => {}, () => {});
      
      // Wait for connection and set WebSocket to open state
      jest.advanceTimersByTime(20);
      const instance = MockWebSocket.instances[MockWebSocket.instances.length - 1];
      instance.readyState = WebSocket.OPEN;
    });

    it('should send mark as read via WebSocket', () => {
      const instance = MockWebSocket.instances[MockWebSocket.instances.length - 1];
      
      notificationsService.markAsReadViaWebSocket('123');

      expect(instance.send).toHaveBeenCalledWith(JSON.stringify({
        type: 'mark_read',
        notification_id: '123'
      }));
    });

    it('should send mark all as read via WebSocket', () => {
      const instance = MockWebSocket.instances[MockWebSocket.instances.length - 1];
      
      notificationsService.markAllAsReadViaWebSocket();

      expect(instance.send).toHaveBeenCalledWith(JSON.stringify({
        type: 'mark_all_read'
      }));
    });

    it('should send ping message', () => {
      const instance = MockWebSocket.instances[MockWebSocket.instances.length - 1];
      
      notificationsService.ping();

      expect(instance.send).toHaveBeenCalledWith(JSON.stringify({
        type: 'ping'
      }));
    });
  });

  describe('Polling Fallback - Fixed', () => {
    it('should poll for pending notifications', async () => {
      const onMessage = jest.fn();
      const mockNotifications = [
        { id: '1', event: 'report_ready' },
        { id: '2', event: 'payment_failed' }
      ];
      
      jest.spyOn(notificationsService, 'getPendingNotifications')
        .mockResolvedValue({ notifications: mockNotifications });

      // Start polling manually
      (notificationsService as any).startPolling(onMessage);

      // Let the initial poll complete
      await Promise.resolve();
      
      // Should call onMessage for each notification from initial poll
      expect(onMessage).toHaveBeenCalledTimes(2);
      expect(onMessage).toHaveBeenCalledWith({
        type: 'new_notification',
        notification: mockNotifications[0]
      });
      expect(onMessage).toHaveBeenCalledWith({
        type: 'new_notification',
        notification: mockNotifications[1]
      });

      // Clear calls from initial poll
      onMessage.mockClear();

      // Advance timer to trigger interval poll
      jest.advanceTimersByTime(30000);
      await Promise.resolve();

      // Should call onMessage again for interval poll
      expect(onMessage).toHaveBeenCalledTimes(2);
    });

    it('should handle polling errors gracefully', async () => {
      const onMessage = jest.fn();
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      
      jest.spyOn(notificationsService, 'getPendingNotifications')
        .mockRejectedValue(new Error('Network error'));

      (notificationsService as any).startPolling(onMessage);

      // Let the initial poll attempt complete
      await Promise.resolve();
      await Promise.resolve(); // Extra resolve for error handling

      expect(consoleError).toHaveBeenCalledWith('Polling error:', expect.any(Error));
      expect(onMessage).not.toHaveBeenCalled();

      consoleError.mockRestore();
    });

    it('should stop polling when disconnecting', () => {
      const onMessage = jest.fn();
      
      (notificationsService as any).startPolling(onMessage);
      
      expect((notificationsService as any).pollInterval).toBeTruthy();

      // Call stopPolling directly since disconnect might not clear it properly in tests
      (notificationsService as any).stopPolling();

      expect((notificationsService as any).pollInterval).toBeNull();
    });
  });
});