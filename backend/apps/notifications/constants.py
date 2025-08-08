"""
Constants for the notifications module
"""

# Retry configuration
MAX_NOTIFICATION_RETRIES = 3
RETRY_DELAY_MINUTES = 1
RETRY_WORKER_SLEEP_SECONDS = 60
RETRY_BATCH_SIZE = 100

# Cache configuration
UNREAD_COUNT_CACHE_TIMEOUT = 300  # 5 minutes
RECENT_NOTIFICATIONS_CACHE_TIMEOUT = 60  # 1 minute
USER_ONLINE_CACHE_TIMEOUT = 300  # 5 minutes

# Notification limits
PENDING_NOTIFICATIONS_LIMIT = 20
RECENT_NOTIFICATIONS_LIMIT = 10
MAX_NOTIFICATIONS_PER_PAGE = 50

# WebSocket configuration
WS_PENDING_NOTIFICATIONS_ON_CONNECT = 10

# Cleanup configuration
OLD_NOTIFICATIONS_CLEANUP_DAYS = 30

# Critical events list
CRITICAL_EVENTS = [
    'account_sync_failed',
    'payment_failed', 
    'low_balance',
    'security_alert'
]