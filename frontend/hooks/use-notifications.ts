import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { notificationsService } from "@/services/notifications.service";
import { Notification } from "@/types";
import { useUIStore } from "@/store/ui-store";
import { useAuthStore } from "@/store/auth-store";
import {
  TOAST_DURATION_CRITICAL,
  TOAST_DURATION_NORMAL,
  RECENT_NOTIFICATION_THRESHOLD,
  NOTIFICATIONS_PAGE_SIZE,
} from "@/constants/notifications";

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const { setNotificationCount, incrementNotificationCount, decrementNotificationCount } = useUIStore();
  const { isAuthenticated } = useAuthStore();
  const cleanupRef = useRef<(() => void) | null>(null);

  // Fetch notifications
  const fetchNotifications = useCallback(async () => {
    if (!isAuthenticated) return;
    
    setIsLoading(true);
    try {
      // Get unread notifications first
      const response = await notificationsService.getNotifications({
        page_size: NOTIFICATIONS_PAGE_SIZE,
        is_read: false,
      });
      setNotifications(response.results);
      
      // Update unread count
      const countResponse = await notificationsService.getUnreadCount();
      setNotificationCount(countResponse.count);
    } catch (error) {
      console.error("Failed to fetch notifications:", error);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, setNotificationCount]);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'connection_established':
        // Initial connection - update state
        setNotificationCount(data.unread_count || 0);
        if (data.pending_notifications) {
          setNotifications(prev => [...data.pending_notifications, ...prev]);
        }
        break;
        
      case 'new_notification':
        const notification = data.notification;
        
        // Add to notifications list
        setNotifications((prev) => {
          // Prevent duplicates
          if (prev.some(n => n.id === notification.id)) {
            return prev;
          }
          return [notification, ...prev.slice(0, 19)];
        });
        
        // Increment unread count if not read
        if (!notification.is_read) {
          incrementNotificationCount();
        }
        
        // Show toast for critical or recent notifications
        if (notification.is_critical) {
          toast.error(notification.title, {
            description: notification.message,
            duration: TOAST_DURATION_CRITICAL,
            action: notification.action_url ? {
              label: "View",
              onClick: () => window.location.href = notification.action_url,
            } : undefined,
          });
        } else {
          // Check if notification is recent (within last minute)
          const createdAt = new Date(notification.created_at);
          const now = new Date();
          const isRecent = (now.getTime() - createdAt.getTime()) < RECENT_NOTIFICATION_THRESHOLD;
          
          if (isRecent) {
            toast(notification.title, {
              description: notification.message,
              duration: TOAST_DURATION_NORMAL,
              action: notification.action_url ? {
                label: "View",
                onClick: () => window.location.href = notification.action_url,
              } : undefined,
            });
          }
        }
        break;
        
      case 'unread_count':
        setNotificationCount(data.count || 0);
        break;
        
      case 'notification_read':
        // Update specific notification
        setNotifications((prev) =>
          prev.map((n) => n.id === data.notification_id ? { ...n, is_read: true } : n)
        );
        setNotificationCount(data.unread_count || 0);
        break;
        
      case 'all_marked_read':
        // Mark all as read
        setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
        setNotificationCount(0);
        break;
    }
  }, [setNotificationCount, incrementNotificationCount]);

  // Mark notification as read
  const markAsRead = useCallback(async (id: string) => {
    try {
      // Find notification
      const notification = notifications.find(n => n.id === id);
      if (!notification || notification.is_read) return;
      
      // Optimistic update
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      decrementNotificationCount();
      
      // Try WebSocket first for real-time update
      if (isConnected) {
        notificationsService.markAsReadViaWebSocket(id);
      }
      
      // Always call API as well for reliability
      await notificationsService.markAsRead(id);
    } catch (error) {
      console.error("Failed to mark notification as read:", error);
      // Revert optimistic update
      fetchNotifications();
    }
  }, [notifications, isConnected, decrementNotificationCount, fetchNotifications]);

  // Mark all as read
  const markAllAsRead = useCallback(async () => {
    try {
      const unreadCount = notifications.filter(n => !n.is_read).length;
      if (unreadCount === 0) return;
      
      // Optimistic update
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setNotificationCount(0);
      
      // Try WebSocket first
      if (isConnected) {
        notificationsService.markAllAsReadViaWebSocket();
      }
      
      // Always call API as well
      const response = await notificationsService.markAllAsRead();
      toast.success(`Marked ${response.count} notifications as read`);
    } catch (error) {
      console.error("Failed to mark all as read:", error);
      fetchNotifications();
    }
  }, [notifications, isConnected, setNotificationCount, fetchNotifications]);

  // Setup WebSocket connection
  useEffect(() => {
    if (!isAuthenticated) {
      setNotifications([]);
      setNotificationCount(0);
      return;
    }

    // Fetch initial notifications
    fetchNotifications();

    // Connect WebSocket with retry logic
    cleanupRef.current = notificationsService.connectWebSocket(
      handleWebSocketMessage,
      setIsConnected
    );

    return () => {
      if (cleanupRef.current) {
        cleanupRef.current();
      }
    };
  }, [isAuthenticated, fetchNotifications, handleWebSocketMessage, setNotificationCount]);

  // Delete notification
  const deleteNotification = useCallback(async (id: string) => {
    try {
      // Optimistic update
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      const notification = notifications.find(n => n.id === id);
      if (notification && !notification.is_read) {
        decrementNotificationCount();
      }
      
      // Call API
      await notificationsService.deleteNotification(id);
    } catch (error) {
      console.error("Failed to delete notification:", error);
      // Revert optimistic update
      fetchNotifications();
    }
  }, [notifications, decrementNotificationCount, fetchNotifications]);

  return {
    notifications,
    isLoading,
    isConnected,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    refetch: fetchNotifications,
  };
}