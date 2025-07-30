"""
Check Celery and Redis connectivity
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import redis
from celery import Celery
from apps.banking.tasks import sync_bank_account


class Command(BaseCommand):
    help = 'Check Celery and Redis status'

    def handle(self, *args, **options):
        self.check_redis()
        self.check_celery()
        self.test_simple_task()

    def check_redis(self):
        """Check Redis connection"""
        self.stdout.write("\n=== Redis Check ===")
        self.stdout.write(f"Redis URL: {settings.REDIS_URL}")
        
        try:
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            self.stdout.write(self.style.SUCCESS("✓ Redis is connected"))
            
            # Check if there are any queued tasks
            queues = ['celery', 'banking', 'billing', 'reports', 'notifications']
            for queue in queues:
                queue_key = f"celery:{queue}"
                queue_size = r.llen(queue_key)
                if queue_size > 0:
                    self.stdout.write(f"  Queue '{queue}': {queue_size} tasks")
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Redis connection failed: {e}"))

    def check_celery(self):
        """Check Celery configuration"""
        self.stdout.write("\n=== Celery Check ===")
        self.stdout.write(f"Broker URL: {settings.CELERY_BROKER_URL}")
        self.stdout.write(f"Result Backend: {settings.CELERY_RESULT_BACKEND}")
        
        if hasattr(settings, 'CELERY_TASK_ALWAYS_EAGER'):
            if settings.CELERY_TASK_ALWAYS_EAGER:
                self.stdout.write(self.style.WARNING(
                    "⚠️  CELERY_TASK_ALWAYS_EAGER is True - tasks will run synchronously!"
                ))
            else:
                self.stdout.write("✓ CELERY_TASK_ALWAYS_EAGER is False")
        else:
            self.stdout.write("✓ CELERY_TASK_ALWAYS_EAGER not set (defaults to False)")

    def test_simple_task(self):
        """Test a simple Celery task"""
        self.stdout.write("\n=== Task Test ===")
        
        try:
            # Try to send a task
            from celery import current_app
            result = current_app.send_task('celery.ping')
            self.stdout.write("✓ Task sent successfully")
            self.stdout.write(f"  Task ID: {result.id}")
            
            # Check if task is being processed
            self.stdout.write("\nTo start Celery worker, run:")
            self.stdout.write(self.style.SUCCESS("celery -A core worker -l info"))
            self.stdout.write("\nFor specific queues:")
            self.stdout.write(self.style.SUCCESS("celery -A core worker -l info -Q banking"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Failed to send task: {e}"))
            
        self.stdout.write("\n=== Instructions ===")
        self.stdout.write("1. Make sure Redis is running:")
        self.stdout.write("   redis-server")
        self.stdout.write("\n2. Start Celery worker:")
        self.stdout.write("   celery -A core worker -l info")
        self.stdout.write("\n3. For development with all queues:")
        self.stdout.write("   celery -A core worker -l info -Q celery,banking,billing,reports,notifications")
        self.stdout.write("\n4. Optional: Start Celery Beat for periodic tasks:")
        self.stdout.write("   celery -A core beat -l info")