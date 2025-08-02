/**
 * Constants for the notifications module
 */

// WebSocket configuration
export const WS_RECONNECT_MAX_ATTEMPTS = 5;
export const WS_RECONNECT_BASE_DELAY = 1000; // 1 second
export const WS_RECONNECT_MAX_DELAY = 30000; // 30 seconds
export const WS_POLL_INTERVAL = 30000; // 30 seconds

// Notification limits
export const NOTIFICATIONS_PAGE_SIZE = 20;
export const NOTIFICATIONS_MAX_PAGE_SIZE = 50;

// Toast durations
export const TOAST_DURATION_CRITICAL = 10000; // 10 seconds
export const TOAST_DURATION_NORMAL = 5000; // 5 seconds

// Recent notification threshold
export const RECENT_NOTIFICATION_THRESHOLD = 60000; // 1 minute

// Event icons mapping
export const NOTIFICATION_ICONS: Record<string, string> = {
  'account_sync_failed': '🔄❌',
  'payment_failed': '💳❌',
  'low_balance': '💰⚠️',
  'security_alert': '🔒⚠️',
  'account_connected': '🏦✅',
  'large_transaction': '💰🔍',
  'report_ready': '📊✅',
  'payment_success': '💳✅',
  'sync_completed': '🔄✅',
};