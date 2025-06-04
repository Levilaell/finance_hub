import apiClient from "@/lib/api-client";
import { Notification, PaginatedResponse } from "@/types";

class NotificationsService {
  async getNotifications(params?: {
    page?: number;
    page_size?: number;
    is_read?: boolean;
    category?: Notification["category"];
  }): Promise<PaginatedResponse<Notification>> {
    return apiClient.get<PaginatedResponse<Notification>>("/api/notifications/", params);
  }

  async getNotification(id: string): Promise<Notification> {
    return apiClient.get<Notification>(`/api/notifications/${id}/`);
  }

  async markAsRead(id: string): Promise<Notification> {
    return apiClient.patch<Notification>(`/api/notifications/${id}/`, { is_read: true });
  }

  async markAllAsRead(): Promise<{ updated: number }> {
    return apiClient.post("/api/notifications/mark-all-read/");
  }

  async deleteNotification(id: string): Promise<void> {
    return apiClient.delete(`/api/notifications/${id}/`);
  }

  async deleteAllRead(): Promise<{ deleted: number }> {
    return apiClient.post("/api/notifications/delete-all-read/");
  }

  async getUnreadCount(): Promise<{ count: number }> {
    return apiClient.get("/api/notifications/unread-count/");
  }

  // WebSocket connection for real-time notifications
  connectWebSocket(onMessage: (notification: Notification) => void): WebSocket | null {
    if (typeof window === "undefined") return null;

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
    const token = localStorage.getItem("access_token");
    
    if (!token) return null;

    const ws = new WebSocket(`${wsUrl}/notifications/?token=${token}`);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "notification") {
          onMessage(data.notification);
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    return ws;
  }
}

export const notificationsService = new NotificationsService();