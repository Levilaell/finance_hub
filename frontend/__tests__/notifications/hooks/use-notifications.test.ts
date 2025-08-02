import { renderHook, act, waitFor } from '@testing-library/react';
import { useNotifications } from '@/hooks/use-notifications';
import { notificationsService } from '@/services/notifications.service';
import { useUIStore } from '@/store/ui-store';
import { useAuthStore } from '@/store/auth-store';
import { toast } from 'sonner';

// Mock dependencies
jest.mock('@/services/notifications.service');
jest.mock('@/store/ui-store');
jest.mock('@/store/auth-store');
jest.mock('sonner');

describe('useNotifications', () => {
  const mockNotifications = [
    {
      id: '1',
      event: 'report_ready',
      title: 'Report Ready',
      message: 'Your monthly report is ready',
      is_read: false,
      is_critical: false,
      created_at: new Date().toISOString(),
      metadata: {},
      action_url: '/reports/123'
    },
    {
      id: '2',
      event: 'payment_failed',
      title: 'Payment Failed',
      message: 'Your payment could not be processed',
      is_read: false,
      is_critical: true,
      created_at: new Date().toISOString(),
      metadata: {},
      action_url: '/subscription'
    }
  ];

  const mockSetNotificationCount = jest.fn();
  const mockIncrementNotificationCount = jest.fn();
  const mockDecrementNotificationCount = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup UI store mock
    (useUIStore as unknown as jest.Mock).mockReturnValue({
      setNotificationCount: mockSetNotificationCount,
      incrementNotificationCount: mockIncrementNotificationCount,
      decrementNotificationCount: mockDecrementNotificationCount
    });

    // Setup auth store mock
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      isAuthenticated: true
    });

    // Setup notifications service mock
    (notificationsService.getNotifications as jest.Mock).mockResolvedValue({
      results: mockNotifications
    });
    (notificationsService.getUnreadCount as jest.Mock).mockResolvedValue({
      count: 2
    });
    (notificationsService.connectWebSocket as jest.Mock).mockReturnValue(() => {});
    (notificationsService.markAsRead as jest.Mock).mockResolvedValue({});
    (notificationsService.markAllAsRead as jest.Mock).mockResolvedValue({
      count: 2
    });
    (notificationsService.deleteNotification as jest.Mock).mockResolvedValue({});
  });

  describe('Initialization', () => {
    it('should fetch notifications on mount when authenticated', async () => {
      const { result } = renderHook(() => useNotifications());

      await waitFor(() => {
        expect(notificationsService.getNotifications).toHaveBeenCalledWith({
          page_size: 20,
          is_read: false
        });
        expect(result.current.notifications).toEqual(mockNotifications);
      });
    });

    it('should not fetch notifications when not authenticated', () => {
      (useAuthStore as unknown as jest.Mock).mockReturnValue({
        isAuthenticated: false
      });

      renderHook(() => useNotifications());

      expect(notificationsService.getNotifications).not.toHaveBeenCalled();
    });

    it('should establish WebSocket connection when authenticated', () => {
      renderHook(() => useNotifications());

      expect(notificationsService.connectWebSocket).toHaveBeenCalled();
    });
  });

  describe('WebSocket Message Handling', () => {
    it('should handle new notification message', async () => {
      const { result } = renderHook(() => useNotifications());
      
      // Get the WebSocket message handler
      const wsHandler = (notificationsService.connectWebSocket as jest.Mock).mock.calls[0][0];
      
      const newNotification = {
        id: '3',
        event: 'account_connected',
        title: 'Account Connected',
        message: 'Your bank account has been connected',
        is_read: false,
        is_critical: false,
        created_at: new Date().toISOString()
      };

      act(() => {
        wsHandler({
          type: 'new_notification',
          notification: newNotification
        });
      });

      expect(result.current.notifications).toContainEqual(newNotification);
      expect(mockIncrementNotificationCount).toHaveBeenCalled();
    });

    it('should show toast for critical notifications', () => {
      renderHook(() => useNotifications());
      
      const wsHandler = (notificationsService.connectWebSocket as jest.Mock).mock.calls[0][0];
      
      const criticalNotification = {
        id: '4',
        event: 'payment_failed',
        title: 'Payment Failed',
        message: 'Critical payment issue',
        is_read: false,
        is_critical: true,
        created_at: new Date().toISOString()
      };

      act(() => {
        wsHandler({
          type: 'new_notification',
          notification: criticalNotification
        });
      });

      expect(toast.error).toHaveBeenCalledWith(
        'Payment Failed',
        expect.objectContaining({
          description: 'Critical payment issue'
        })
      );
    });

    it('should handle unread count update', () => {
      renderHook(() => useNotifications());
      
      const wsHandler = (notificationsService.connectWebSocket as jest.Mock).mock.calls[0][0];
      
      act(() => {
        wsHandler({
          type: 'unread_count',
          count: 5
        });
      });

      expect(mockSetNotificationCount).toHaveBeenCalledWith(5);
    });
  });

  describe('Notification Actions', () => {
    it('should mark notification as read', async () => {
      const { result } = renderHook(() => useNotifications());

      await waitFor(() => {
        expect(result.current.notifications.length).toBeGreaterThan(0);
      });

      await act(async () => {
        await result.current.markAsRead('1');
      });

      expect(notificationsService.markAsRead).toHaveBeenCalledWith('1');
      expect(mockDecrementNotificationCount).toHaveBeenCalled();
      
      const notification = result.current.notifications.find(n => n.id === '1');
      expect(notification?.is_read).toBe(true);
    });

    it('should mark all notifications as read', async () => {
      const { result } = renderHook(() => useNotifications());

      await waitFor(() => {
        expect(result.current.notifications.length).toBeGreaterThan(0);
      });

      await act(async () => {
        await result.current.markAllAsRead();
      });

      expect(notificationsService.markAllAsRead).toHaveBeenCalled();
      expect(mockSetNotificationCount).toHaveBeenCalledWith(0);
      expect(toast.success).toHaveBeenCalledWith('Marked 2 notifications as read');
      
      result.current.notifications.forEach(notification => {
        expect(notification.is_read).toBe(true);
      });
    });

    it('should delete notification', async () => {
      const { result } = renderHook(() => useNotifications());

      await waitFor(() => {
        expect(result.current.notifications.length).toBe(2);
      });

      await act(async () => {
        await result.current.deleteNotification('1');
      });

      expect(notificationsService.deleteNotification).toHaveBeenCalledWith('1');
      expect(result.current.notifications).toHaveLength(1);
      expect(result.current.notifications.find(n => n.id === '1')).toBeUndefined();
    });
  });

  describe('Connection State', () => {
    it('should track WebSocket connection state', () => {
      const { result } = renderHook(() => useNotifications());
      
      const connectionHandler = (notificationsService.connectWebSocket as jest.Mock).mock.calls[0][1];
      
      expect(result.current.isConnected).toBe(false);

      act(() => {
        connectionHandler(true);
      });

      expect(result.current.isConnected).toBe(true);

      act(() => {
        connectionHandler(false);
      });

      expect(result.current.isConnected).toBe(false);
    });
  });

  describe('Error Handling', () => {
    it('should handle fetch notifications error', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      (notificationsService.getNotifications as jest.Mock).mockRejectedValue(
        new Error('Network error')
      );

      const { result } = renderHook(() => useNotifications());

      await waitFor(() => {
        expect(consoleError).toHaveBeenCalledWith(
          'Failed to fetch notifications:',
          expect.any(Error)
        );
        expect(result.current.notifications).toEqual([]);
      });

      consoleError.mockRestore();
    });

    it('should revert optimistic update on markAsRead error', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      (notificationsService.markAsRead as jest.Mock).mockRejectedValue(
        new Error('API error')
      );

      const { result } = renderHook(() => useNotifications());

      await waitFor(() => {
        expect(result.current.notifications.length).toBeGreaterThan(0);
      });

      const originalNotification = result.current.notifications[0];

      await act(async () => {
        await result.current.markAsRead('1');
      });

      await waitFor(() => {
        expect(consoleError).toHaveBeenCalled();
        expect(notificationsService.getNotifications).toHaveBeenCalledTimes(2);
      });

      consoleError.mockRestore();
    });
  });
});