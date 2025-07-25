# backend/celerybeat-schedule.py
"""
Celery Beat Schedule Configuration
Defines periodic tasks for the banking app
"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Sync all accounts every 4 hours
    'sync-all-accounts': {
        'task': 'banking.sync_all_accounts',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
        'options': {
            'expires': 3600,  # Expire after 1 hour if not executed
        }
    },
    
    # Health check every hour
    'check-account-health': {
        'task': 'banking.check_account_health',
        'schedule': crontab(minute=30),  # Every hour at :30
        'options': {
            'expires': 1800,
        }
    },
    
    # Check connector status twice daily
    'check-connector-status': {
        'task': 'banking.check_connector_status',
        'schedule': crontab(minute=0, hour='9,21'),  # 9 AM and 9 PM
        'options': {
            'expires': 3600,
        }
    },
    
    # Cleanup old sync logs weekly
    'cleanup-sync-logs': {
        'task': 'banking.cleanup_old_sync_logs',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3 AM
        'options': {
            'expires': 7200,
        }
    },
    
    # Process pending consent expirations daily
    'check-consent-expirations': {
        'task': 'banking.check_consent_expirations',
        'schedule': crontab(hour=10, minute=0),  # Daily at 10 AM
        'options': {
            'expires': 3600,
        }
    },
    
    # Retry failed syncs every 2 hours
    'retry-failed-syncs': {
        'task': 'banking.retry_failed_syncs',
        'schedule': crontab(minute=15, hour='*/2'),  # Every 2 hours at :15
        'options': {
            'expires': 3600,
        }
    },
}

# Additional Celery configuration
CELERY_TASK_ROUTES = {
    'banking.sync_*': {'queue': 'sync'},
    'banking.process_transaction_*': {'queue': 'transactions'},
    'banking.notify_*': {'queue': 'notifications'},
    'banking.check_*': {'queue': 'monitoring'},
    'banking.cleanup_*': {'queue': 'maintenance'},
}

CELERY_TASK_TIME_LIMIT = 300  # 5 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes soft limit

CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # Restart worker after 1000 tasks