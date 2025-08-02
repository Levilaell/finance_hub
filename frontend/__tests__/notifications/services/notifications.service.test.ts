import { notificationsService } from '@/services/notifications.service';
import apiClient from '@/lib/api-client';

// Mock dependencies
jest.mock('@/lib/api-client');

// Mock WebSocket
class MockWebSocket {
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  readyState: number = WebSocket.CONNECTING;
  
  constructor(public url: string) {
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }
  
  send(data: string) {
    // Mock send
  }
  
  close() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }
}

global.WebSocket = MockWebSocket as any;

describe('NotificationsService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
    jest.useFakeTimers();
    localStorage.clear();
  });

  afterEach(() => {
    jest.useRealTimers();
    notificationsService.disconnect();
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

    it('should get single notification', async () => {
      const mockNotification = { id: '123', title: 'Test' };
      (apiClient.get as jest.Mock).mockResolvedValue(mockNotification);

      const result = await notificationsService.getNotification('123');

      expect(apiClient.get).toHaveBeenCalledWith('/api/notifications/123/');
      expect(result).toEqual(mockNotification);
    });

    it('should mark notification as read', async () => {
      const mockNotification = { id: '123', is_read: true };
      (apiClient.post as jest.Mock).mockResolvedValue(mockNotification);

      const result = await notificationsService.markAsRead('123');

      expect(apiClient.post).toHaveBeenCalledWith('/api/notifications/mark-read/123/');
      expect(result).toEqual(mockNotification);
    });

    it('should mark all notifications as read', async () => {
      const mockResponse = { message: 'Success', count: 5 };
      (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

      const result = await notificationsService.markAllAsRead();

      expect(apiClient.post).toHaveBeenCalledWith('/api/notifications/mark-read/');
      expect(result).toEqual(mockResponse);
    });

    it('should get unread count', async () => {
      const mockResponse = { count: 3 };
      (apiClient.get as jest.Mock).mockResolvedValue(mockResponse);

      const result = await notificationsService.getUnreadCount();

      expect(apiClient.get).toHaveBeenCalledWith('/api/notifications/unread-count/');
      expect(result).toEqual(mockResponse);
    });

    it('should delete notification', async () => {
      (apiClient.delete as jest.Mock).mockResolvedValue(undefined);

      await notificationsService.deleteNotification('123');

      expect(apiClient.delete).toHaveBeenCalledWith('/api/notifications/123/');
    });
  });

  describe('WebSocket Connection', () => {
    it('should connect WebSocket with auth token', () => {
      localStorage.setItem('access_token', 'test-token');
      const onMessage = jest.fn();
      const onConnectionChange = jest.fn();

      notificationsService.connectWebSocket(onMessage, onConnectionChange);

      expect(MockWebSocket.prototype.constructor).toHaveBeenCalledWith(
        expect.stringContaining('ws://localhost:8000/ws/notifications/?token=test-token')
      );
    });

    it('should handle WebSocket open event', async () => {
      localStorage.setItem('access_token', 'test-token');
      const onMessage = jest.fn();
      const onConnectionChange = jest.fn();

      notificationsService.connectWebSocket(onMessage, onConnectionChange);

      // Wait for connection to open
      await new Promise(resolve => setTimeout(resolve, 20));
      jest.runAllTimers();

      expect(onConnectionChange).toHaveBeenCalledWith(true);
    });

    it('should handle WebSocket messages', () => {
      localStorage.setItem('access_token', 'test-token');
      const onMessage = jest.fn();
      const onConnectionChange = jest.fn();

      notificationsService.connectWebSocket(onMessage, onConnectionChange);

      const ws = (notificationsService as any).ws;
      const testData = { type: 'new_notification', notification: {} };

      if (ws && ws.onmessage) {
        ws.onmessage(new MessageEvent('message', {
          data: JSON.stringify(testData)
        }));
      }

      expect(onMessage).toHaveBeenCalledWith(testData);
    });

    it('should send acknowledgment for critical notifications', () => {
      localStorage.setItem('access_token', 'test-token');
      const onMessage = jest.fn();
      const sendSpy = jest.spyOn(MockWebSocket.prototype, 'send');

      notificationsService.connectWebSocket(onMessage, () => {});

      const ws = (notificationsService as any).ws;
      const testData = {
        type: 'ack_request',
        notification_id: '123'
      };

      if (ws && ws.onmessage) {
        ws.onmessage(new MessageEvent('message', {
          data: JSON.stringify(testData)
        }));
      }

      expect(sendSpy).toHaveBeenCalledWith(JSON.stringify({
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

  describe('WebSocket Reconnection', () => {
    it('should attempt reconnection on disconnect', () => {
      localStorage.setItem('access_token', 'test-token');
      const onMessage = jest.fn();
      const onConnectionChange = jest.fn();

      notificationsService.connectWebSocket(onMessage, onConnectionChange);

      const ws = (notificationsService as any).ws;
      
      // Simulate disconnect
      if (ws && ws.onclose) {
        ws.onclose(new CloseEvent('close'));
      }

      expect(onConnectionChange).toHaveBeenCalledWith(false);

      // Advance timer to trigger reconnection
      jest.advanceTimersByTime(1000);

      // Should create new WebSocket
      expect((notificationsService as any).reconnectAttempts).toBe(1);
    });

    it('should use exponential backoff for reconnections', () => {
      localStorage.setItem('access_token', 'test-token');
      const onMessage = jest.fn();

      notificationsService.connectWebSocket(onMessage, () => {});

      const ws = (notificationsService as any).ws;

      // First disconnect
      if (ws && ws.onclose) {
        ws.onclose(new CloseEvent('close'));
      }
      expect((notificationsService as any).reconnectAttempts).toBe(0);

      // First reconnect attempt (1s)
      jest.advanceTimersByTime(1000);
      expect((notificationsService as any).reconnectAttempts).toBe(1);

      // Second disconnect
      const ws2 = (notificationsService as any).ws;
      if (ws2 && ws2.onclose) {
        ws2.onclose(new CloseEvent('close'));
      }

      // Second reconnect attempt (2s)
      jest.advanceTimersByTime(2000);
      expect((notificationsService as any).reconnectAttempts).toBe(2);
    });

    it('should fall back to polling after max reconnect attempts', () => {
      localStorage.setItem('access_token', 'test-token');
      const onMessage = jest.fn();
      const mockGetPending = jest.spyOn(notificationsService, 'getPendingNotifications')
        .mockResolvedValue({ notifications: [] });

      notificationsService.connectWebSocket(onMessage, () => {});

      // Simulate multiple reconnect failures
      for (let i = 0; i < 5; i++) {
        const ws = (notificationsService as any).ws;
        if (ws && ws.onclose) {
          ws.onclose(new CloseEvent('close'));
        }
        jest.advanceTimersByTime(Math.pow(2, i) * 1000);
      }

      // Should start polling
      jest.advanceTimersByTime(30000);
      expect(mockGetPending).toHaveBeenCalled();
    });
  });

  describe('WebSocket Methods', () => {
    it('should send mark as read via WebSocket', () => {
      localStorage.setItem('access_token', 'test-token');
      const sendSpy = jest.spyOn(MockWebSocket.prototype, 'send');
      
      notificationsService.connectWebSocket(() => {}, () => {});
      
      // Set WebSocket to open state
      (notificationsService as any).ws.readyState = WebSocket.OPEN;
      
      notificationsService.markAsReadViaWebSocket('123');

      expect(sendSpy).toHaveBeenCalledWith(JSON.stringify({
        type: 'mark_read',
        notification_id: '123'
      }));
    });

    it('should send mark all as read via WebSocket', () => {
      localStorage.setItem('access_token', 'test-token');
      const sendSpy = jest.spyOn(MockWebSocket.prototype, 'send');
      
      notificationsService.connectWebSocket(() => {}, () => {});
      
      // Set WebSocket to open state
      (notificationsService as any).ws.readyState = WebSocket.OPEN;
      
      notificationsService.markAllAsReadViaWebSocket();

      expect(sendSpy).toHaveBeenCalledWith(JSON.stringify({
        type: 'mark_all_read'
      }));
    });

    it('should send ping message', () => {
      localStorage.setItem('access_token', 'test-token');
      const sendSpy = jest.spyOn(MockWebSocket.prototype, 'send');
      
      notificationsService.connectWebSocket(() => {}, () => {});
      
      // Set WebSocket to open state
      (notificationsService as any).ws.readyState = WebSocket.OPEN;
      
      notificationsService.ping();

      expect(sendSpy).toHaveBeenCalledWith(JSON.stringify({
        type: 'ping'
      }));
    });
  });

  describe('Polling Fallback', () => {
    it('should poll for pending notifications', async () => {
      const onMessage = jest.fn();
      const mockNotifications = [
        { id: '1', event: 'report_ready' },
        { id: '2', event: 'payment_failed' }
      ];
      
      jest.spyOn(notificationsService, 'getPendingNotifications')
        .mockResolvedValue({ notifications: mockNotifications });

      // Start polling
      (notificationsService as any).startPolling(onMessage);

      // Advance timer to trigger poll
      jest.advanceTimersByTime(30000);

      await Promise.resolve(); // Let promises resolve

      expect(onMessage).toHaveBeenCalledTimes(2);
      expect(onMessage).toHaveBeenCalledWith({
        type: 'new_notification',
        notification: mockNotifications[0]
      });
      expect(onMessage).toHaveBeenCalledWith({
        type: 'new_notification',
        notification: mockNotifications[1]
      });
    });

    it('should handle polling errors gracefully', async () => {
      const onMessage = jest.fn();
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      
      jest.spyOn(notificationsService, 'getPendingNotifications')
        .mockRejectedValue(new Error('Network error'));

      (notificationsService as any).startPolling(onMessage);

      jest.advanceTimersByTime(30000);

      await Promise.resolve();

      expect(consoleError).toHaveBeenCalledWith('Polling error:', expect.any(Error));
      expect(onMessage).not.toHaveBeenCalled();

      consoleError.mockRestore();
    });

    it('should stop polling when disconnecting', () => {
      const onMessage = jest.fn();
      
      (notificationsService as any).startPolling(onMessage);
      
      expect((notificationsService as any).pollInterval).toBeTruthy();

      notificationsService.disconnect();

      expect((notificationsService as any).pollInterval).toBeNull();
    });
  });
});