import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { notificationsService } from "@/services/notifications.service";
import { Notification } from "@/types";
import { useUIStore } from "@/store/ui-store";
import { useAuthStore } from "@/store/auth-store";

export function useNotifications() {
  const wsRef = useRef<WebSocket | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { setNotificationCount } = useUIStore();
  const { isAuthenticated } = useAuthStore();

  // Fetch notifications
  const fetchNotifications = async () => {
    if (!isAuthenticated) return;
    
    setIsLoading(true);
    try {
      const response = await notificationsService.getNotifications({
        page_size: 10,
        is_read: false,
      });
      setNotifications(response.results);
      setNotificationCount(response.count);
    } catch (error) {
      console.error("Failed to fetch notifications:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle new notification
  const handleNewNotification = (notification: Notification) => {
    setNotifications((prev) => [notification, ...prev]);
    setNotificationCount((prev) => prev + 1);

    // Show toast notification
    switch (notification.type) {
      case "success":
        toast.success(notification.title, {
          description: notification.message,
        });
        break;
      case "error":
        toast.error(notification.title, {
          description: notification.message,
        });
        break;
      case "warning":
        toast.warning(notification.title, {
          description: notification.message,
        });
        break;
      default:
        toast(notification.title, {
          description: notification.message,
        });
    }
  };

  // Mark notification as read
  const markAsRead = async (id: string) => {
    try {
      await notificationsService.markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setNotificationCount((prev) => Math.max(0, prev - 1));
    } catch (error) {
      console.error("Failed to mark notification as read:", error);
    }
  };

  // Mark all as read
  const markAllAsRead = async () => {
    try {
      await notificationsService.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setNotificationCount(0);
    } catch (error) {
      console.error("Failed to mark all notifications as read:", error);
    }
  };

  // Setup WebSocket connection
  useEffect(() => {
    if (!isAuthenticated) return;

    // Fetch initial notifications
    fetchNotifications();

    // Connect WebSocket
    wsRef.current = notificationsService.connectWebSocket(handleNewNotification);

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [isAuthenticated]);

  return {
    notifications,
    isLoading,
    markAsRead,
    markAllAsRead,
    refetch: fetchNotifications,
  };
}