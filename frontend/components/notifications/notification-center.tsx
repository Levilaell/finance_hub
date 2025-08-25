"use client";

import { Bell, BellOff, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useNotifications } from "@/hooks/use-notifications";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import { Notification } from "@/types";
import { NOTIFICATION_ICONS } from "@/constants/notifications";

export function NotificationCenter() {
  const {
    notifications,
    isLoading,
    isConnected,
    markAsRead,
    markAllAsRead,
  } = useNotifications();

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          {isConnected ? (
            <Bell className="h-5 w-5" />
          ) : (
            <BellOff className="h-5 w-5 text-muted-foreground" />
          )}
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
            >
              {unreadCount > 9 ? "9+" : unreadCount}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[350px] sm:w-[380px] max-w-[90vw]">
        <div className="flex items-center justify-between p-2 pb-0">
          <div className="font-semibold">Notifications</div>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={markAllAsRead}
              className="text-xs"
            >
              <Check className="h-3 w-3 mr-1" />
              Mark all read
            </Button>
          )}
        </div>
        <DropdownMenuSeparator />
        <ScrollArea className="h-[400px]">
          {isLoading ? (
            <div className="p-4 text-center text-muted-foreground">
              Loading notifications...
            </div>
          ) : notifications.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground">
              No notifications
            </div>
          ) : (
            <div className="space-y-1">
              {notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onMarkAsRead={markAsRead}
                />
              ))}
            </div>
          )}
        </ScrollArea>
        {!isConnected && (
          <div className="p-2 text-xs text-center text-muted-foreground border-t">
            Real-time updates unavailable
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead: (id: string) => void;
}

function NotificationItem({
  notification,
  onMarkAsRead,
}: NotificationItemProps) {
  const handleClick = () => {
    if (!notification.is_read) {
      onMarkAsRead(notification.id);
    }
    if (notification.action_url) {
      window.location.href = notification.action_url;
    }
  };

  return (
    <div
      className={cn(
        // Mobile-optimized padding and spacing
        'group relative flex gap-2 sm:gap-3 p-2 sm:p-3 hover:bg-accent cursor-pointer transition-colors',
        !notification.is_read && 'bg-accent/50'
      )}
      onClick={handleClick}
    >
      <div className="flex-1 space-y-1 min-w-0">
        <div className={cn(
          // Mobile: Stack title and badge, Desktop: Side by side
          'flex flex-col space-y-1',
          'sm:flex-row sm:items-start sm:justify-between sm:space-y-0 sm:gap-2'
        )}>
          <p className="text-sm font-medium leading-none truncate">
            {notification.title}
          </p>
          {notification.is_critical && (
            <Badge variant="destructive" className="text-xs px-1 py-0 w-fit">
              Critical
            </Badge>
          )}
        </div>
        
        <p className={cn(
          // Mobile: More compact, Desktop: Standard
          'text-xs sm:text-sm text-muted-foreground',
          // Mobile: Single line, Desktop: Two lines
          'line-clamp-1 sm:line-clamp-2'
        )}>
          {notification.message}
        </p>
        
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <NotificationIcon event={notification.event} />
          <span className="truncate">
            {formatDistanceToNow(new Date(notification.created_at), {
              addSuffix: true,
            })}
          </span>
        </div>
      </div>
      
      {!notification.is_read && (
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 sm:h-8 bg-primary rounded-r" />
      )}
    </div>
  );
}

function NotificationIcon({ event }: { event: Notification["event"] }) {
  return <span>{NOTIFICATION_ICONS[event] || 'ℹ️'}</span>;
}