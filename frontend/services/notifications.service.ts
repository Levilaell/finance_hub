import apiClient from "@/lib/api-client";
import { Notification, PaginatedResponse } from "@/types";
import {
  WS_RECONNECT_MAX_ATTEMPTS,
  WS_RECONNECT_BASE_DELAY,
  WS_RECONNECT_MAX_DELAY,
  WS_POLL_INTERVAL,
} from "@/constants/notifications";

class NotificationsService {
  private ws: WebSocket | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = WS_RECONNECT_MAX_ATTEMPTS;
  private pollInterval: NodeJS.Timeout | null = null;

  // REST API Methods
  async getNotifications(params?: {
    page?: number;
    page_size?: number;
    is_read?: boolean;
    event?: Notification["event"];
    is_critical?: boolean;
  }): Promise<PaginatedResponse<Notification>> {
    return apiClient.get<PaginatedResponse<Notification>>("/api/notifications/", params);
  }

  async getNotification(id: string): Promise<Notification> {
    return apiClient.get<Notification>(`/api/notifications/${id}/`);
  }

  async markAsRead(id: string): Promise<Notification> {
    return apiClient.post<Notification>(`/api/notifications/mark-read/${id}/`);
  }

  async markAllAsRead(): Promise<{ message: string; count: number }> {
    return apiClient.post("/api/notifications/mark-read/");
  }

  async getUnreadCount(): Promise<{ count: number }> {
    return apiClient.get("/api/notifications/unread-count/");
  }

  async getPendingNotifications(): Promise<{ notifications: Notification[] }> {
    return apiClient.get("/api/notifications/pending/");
  }

  async deleteNotification(id: string): Promise<void> {
    return apiClient.delete(`/api/notifications/${id}/`);
  }

  // WebSocket Connection Management
  connectWebSocket(
    onMessage: (data: any) => void,
    onConnectionChange?: (connected: boolean) => void
  ): () => void {
    if (typeof window === "undefined") {
      return () => {};
    }

    const connect = () => {
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
      const token = localStorage.getItem("access_token");
      
      if (!token) {
        console.warn("No auth token for WebSocket");
        // Fall back to polling
        this.startPolling(onMessage);
        return;
      }

      try {
        this.ws = new WebSocket(`${wsUrl}/notifications/?token=${token}`);

        this.ws.onopen = () => {
          console.log("Notifications WebSocket connected");
          this.reconnectAttempts = 0;
          onConnectionChange?.(true);
          
          // Stop polling if running
          this.stopPolling();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            onMessage(data);
            
            // Acknowledge critical notifications
            if (data.type === 'ack_request' && data.notification_id) {
              this.sendMessage({
                type: 'ack',
                notification_id: data.notification_id
              });
            }
          } catch (error) {
            console.error("Error parsing WebSocket message:", error);
          }
        };

        this.ws.onerror = (error) => {
          console.error("WebSocket error:", error);
        };

        this.ws.onclose = () => {
          console.log("WebSocket disconnected");
          onConnectionChange?.(false);
          this.attemptReconnect(onMessage, onConnectionChange);
        };
      } catch (error) {
        console.error("Failed to connect WebSocket:", error);
        this.startPolling(onMessage);
      }
    };

    connect();

    // Return cleanup function
    return () => {
      this.disconnect();
      this.stopPolling();
    };
  }

  private attemptReconnect(
    onMessage: (data: any) => void,
    onConnectionChange?: (connected: boolean) => void
  ) {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log("Max reconnect attempts reached, falling back to polling");
      this.startPolling(onMessage);
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(WS_RECONNECT_BASE_DELAY * Math.pow(2, this.reconnectAttempts - 1), WS_RECONNECT_MAX_DELAY);
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    this.reconnectTimeout = setTimeout(() => {
      this.connectWebSocket(onMessage, onConnectionChange);
    }, delay);
  }

  private startPolling(onMessage: (data: any) => void) {
    if (this.pollInterval) return;
    
    console.log("Starting notification polling fallback");
    
    // Poll for pending notifications every 30 seconds
    const poll = async () => {
      try {
        const response = await this.getPendingNotifications();
        if (response.notifications.length > 0) {
          response.notifications.forEach(notification => {
            onMessage({
              type: 'new_notification',
              notification
            });
          });
        }
      } catch (error) {
        console.error("Polling error:", error);
      }
    };
    
    // Initial poll
    poll();
    
    // Set up interval
    this.pollInterval = setInterval(poll, WS_POLL_INTERVAL);
  }

  private stopPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  sendMessage(message: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  markAsReadViaWebSocket(notificationId: string) {
    this.sendMessage({
      type: 'mark_read',
      notification_id: notificationId,
    });
  }

  markAllAsReadViaWebSocket() {
    this.sendMessage({
      type: 'mark_all_read',
    });
  }

  // Simple ping to keep connection alive
  ping() {
    this.sendMessage({ type: 'ping' });
  }
}

export const notificationsService = new NotificationsService();