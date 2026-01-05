#!/usr/bin/env python
"""
Script to check Celery configuration and worker status.
Run this to verify that Celery is properly configured.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from celery import Celery
from core.celery import app as celery_app
from decouple import config

def check_redis_connection():
    """Check if Redis is accessible."""
    print("=" * 60)
    print("Checking Redis Connection...")
    print("=" * 60)

    redis_url = config('REDIS_URL', default='redis://localhost:6379/0')
    print(f"Redis URL: {redis_url}")

    try:
        import redis
        r = redis.from_url(redis_url)
        r.ping()
        print("✓ Redis connection successful!")
        return True
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        return False


def check_celery_config():
    """Check Celery configuration."""
    print("\n" + "=" * 60)
    print("Checking Celery Configuration...")
    print("=" * 60)

    print(f"Celery App Name: {celery_app.main}")
    print(f"Broker URL: {celery_app.conf.broker_url}")
    print(f"Result Backend: {celery_app.conf.result_backend}")
    print(f"Timezone: {celery_app.conf.timezone}")

    return True


def check_registered_tasks():
    """Check registered tasks."""
    print("\n" + "=" * 60)
    print("Registered Celery Tasks...")
    print("=" * 60)

    tasks = sorted(celery_app.tasks.keys())

    banking_tasks = [t for t in tasks if 'banking' in t]

    if banking_tasks:
        print("\n✓ Banking webhook tasks registered:")
        for task in banking_tasks:
            print(f"  - {task}")
    else:
        print("\n✗ No banking tasks found!")

    print(f"\nTotal tasks: {len(tasks)}")

    return len(banking_tasks) > 0


def check_worker_status():
    """Try to check if workers are running."""
    print("\n" + "=" * 60)
    print("Checking Worker Status...")
    print("=" * 60)

    try:
        inspect = celery_app.control.inspect()
        active = inspect.active()

        if active:
            print("✓ Workers are running:")
            for worker, tasks in active.items():
                print(f"  - {worker}: {len(tasks)} active tasks")
            return True
        else:
            print("✗ No workers found or workers are idle")
            print("\nTo start a worker, run:")
            print("  celery -A core worker --loglevel=info")
            return False
    except Exception as e:
        print(f"✗ Could not connect to workers: {e}")
        print("\nMake sure:")
        print("  1. Redis is running")
        print("  2. Celery worker is started")
        return False


def main():
    """Run all checks."""
    print("\n" + "=" * 60)
    print("CELERY CONFIGURATION CHECKER")
    print("=" * 60)

    checks = [
        ("Redis Connection", check_redis_connection),
        ("Celery Configuration", check_celery_config),
        ("Registered Tasks", check_registered_tasks),
        ("Worker Status", check_worker_status),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Error during {name}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n✓ All checks passed! Celery is properly configured.")
        return 0
    else:
        print("\n✗ Some checks failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
