#!/usr/bin/env python3
"""
RAILWAY-SPECIFIC CELERY BEAT FIX
===============================

Alternative fix that doesn't rely on /tmp marker files.
Directly checks database state and applies appropriate migration strategy.
"""

import os
import sys
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

def railway_celery_beat_fix():
    """Railway-specific Celery Beat fix without /tmp dependency"""
    
    with connection.cursor() as cursor:
        # Check if crontabschedule table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'django_celery_beat_crontabschedule'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        # Check if initial migration is recorded
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM django_migrations 
                WHERE app = 'django_celery_beat' AND name = '0001_initial'
            );
        """)
        migration_recorded = cursor.fetchone()[0]
        
        if table_exists and migration_recorded:
            return "NEED_FAKE"
        elif table_exists and not migration_recorded:
            return "NEED_FAKE_INITIAL"
        elif not table_exists and migration_recorded:
            return "NEED_MIGRATION"
        else:
            return "NORMAL"

if __name__ == '__main__':
    result = railway_celery_beat_fix()
    print(result)
