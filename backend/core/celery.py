"""
Celery configuration for CaixaHub
"""
import os
from celery import Celery
from celery.schedules import crontab
from decouple import config

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Get Redis URL from environment
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

app = Celery('caixahub')

# Explicit broker and backend configuration
app.conf.broker_url = REDIS_URL
app.conf.result_backend = REDIS_URL

# Load other configuration from Django settings with 'CELERY_' prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
# This will automatically find tasks.py in all installed Django apps
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    # Generate AI insights weekly (every Monday at 8 AM)
    'generate-weekly-ai-insights': {
        'task': 'apps.ai_insights.tasks.generate_weekly_insights',
        'schedule': crontab(day_of_week=1, hour=8, minute=0),  # Monday at 8:00 AM
    },
    # Cleanup old AI insights (every Sunday at 3 AM)
    'cleanup-old-ai-insights': {
        'task': 'apps.ai_insights.tasks.cleanup_old_insights',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Sunday at 3:00 AM
    },
}

# Timezone configuration
app.conf.timezone = 'America/Sao_Paulo'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')


# Explicitly import task modules to ensure they are registered
# This is needed because autodiscover_tasks() may not work in all deployment scenarios
@app.on_after_finalize.connect
def setup_task_imports(**_kwargs):
    """Import task modules after Celery is fully configured."""
    # Import after Django is ready
    import django
    if not django.apps.apps.ready:
        django.setup()

    # Now safe to import task modules
    # Import is intentional - registers tasks with Celery
    try:
        import apps.banking.tasks  # noqa: F401
    except ImportError:
        pass

    try:
        import apps.ai_insights.tasks  # noqa: F401
    except ImportError:
        pass
