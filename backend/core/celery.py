"""
Celery configuration for CaixaHub
Handles asynchronous tasks and periodic jobs
"""
import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('caixahub')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    # Banking tasks
    'sync-all-accounts': {
        'task': 'apps.banking.tasks.periodic_account_sync',
        'schedule': 60.0 * 60.0 * 4,  # Every 4 hours
    },
    'cleanup-old-logs': {
        'task': 'apps.banking.tasks.cleanup_old_sync_logs',
        'schedule': 60.0 * 60.0 * 24,  # Every 24 hours
    },
    'send-balance-alerts': {
        'task': 'apps.banking.tasks.send_low_balance_alerts',
        'schedule': 60.0 * 60.0 * 12,  # Every 12 hours
    },
    
    # Subscription and billing tasks
    'check-trial-expirations': {
        'task': 'apps.companies.tasks.check_trial_expirations',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
        'options': {
            'expires': 60 * 60 * 2,  # Expire after 2 hours if not executed
        }
    },
    'reset-monthly-usage': {
        'task': 'apps.companies.tasks.reset_monthly_usage_counters',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),  # 1st of each month at midnight
        'options': {
            'expires': 60 * 60 * 6,  # Expire after 6 hours if not executed
        }
    },
    'process-subscription-renewals': {
        'task': 'apps.companies.tasks.process_subscription_renewals',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'options': {
            'expires': 60 * 60 * 4,  # Expire after 4 hours if not executed
        }
    },
    'check-usage-limits': {
        'task': 'apps.companies.tasks.check_usage_limits',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
        'options': {
            'expires': 60 * 60 * 2,  # Expire after 2 hours if not executed
        }
    },
    'cleanup-expired-subscriptions': {
        'task': 'apps.companies.tasks.cleanup_expired_subscriptions',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Weekly on Sunday at 3 AM
        'options': {
            'expires': 60 * 60 * 12,  # Expire after 12 hours if not executed
        }
    },
    
    # Optional: Daily summary reports
    'send-daily-summaries': {
        'task': 'apps.reports.tasks.send_daily_summary_emails',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
        'options': {
            'expires': 60 * 60 * 4,  # Expire after 4 hours if not executed
        }
    },
    
    # Optional: Weekly usage reports for active companies
    'send-weekly-usage-reports': {
        'task': 'apps.reports.tasks.send_weekly_usage_reports',
        'schedule': crontab(day_of_week=1, hour=9, minute=0),  # Monday at 9 AM
        'options': {
            'expires': 60 * 60 * 6,  # Expire after 6 hours if not executed
        }
    },
}

# Timezone configuration
app.conf.timezone = 'America/Sao_Paulo'

# Task execution options
app.conf.task_routes = {
    'apps.banking.tasks.*': {'queue': 'banking'},
    'apps.companies.tasks.*': {'queue': 'billing'},
    'apps.reports.tasks.*': {'queue': 'reports'},
    'apps.notifications.tasks.*': {'queue': 'notifications'},
}

# Task result backend configuration
app.conf.task_track_started = True
app.conf.task_time_limit = 30 * 60  # 30 minutes
app.conf.task_soft_time_limit = 25 * 60  # 25 minutes

# Worker configuration
app.conf.worker_prefetch_multiplier = 4
app.conf.worker_max_tasks_per_child = 1000

# Error handling
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')