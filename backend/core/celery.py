"""
Celery configuration for Caixa Digital
Handles asynchronous tasks and periodic jobs
"""
import os

from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')

app = Celery('caixa_digital')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
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
}

app.conf.timezone = 'America/Sao_Paulo'

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')