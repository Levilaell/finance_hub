"""
Command to fix inconsistent migration history
"""
from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix inconsistent migration history'

    def handle(self, *args, **options):
        self.stdout.write("Checking migration consistency...")
        
        with connection.cursor() as cursor:
            try:
                # Check if django_migrations table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'django_migrations'
                    );
                """)
                
                if not cursor.fetchone()[0]:
                    self.stdout.write(self.style.WARNING("django_migrations table doesn't exist"))
                    return
                
                # Find inconsistent migrations in reports app
                cursor.execute("""
                    SELECT name FROM django_migrations 
                    WHERE app = 'reports' 
                    ORDER BY id;
                """)
                
                migrations = [row[0] for row in cursor.fetchall()]
                self.stdout.write(f"Found {len(migrations)} migrations in reports app")
                
                # Check for the specific problem
                if '0003_aianalysistemplate_aianalysis' in migrations and \
                   '0002_alter_aianalysis_options_and_more' not in migrations:
                    
                    self.stdout.write(self.style.WARNING(
                        "Found inconsistency: 0003 applied without 0002"
                    ))
                    
                    # Option 1: Mark 0002 as already applied (fake it)
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied)
                        VALUES ('reports', '0002_alter_aianalysis_options_and_more', NOW())
                        ON CONFLICT DO NOTHING;
                    """)
                    
                    self.stdout.write(self.style.SUCCESS(
                        "✓ Marked migration 0002 as applied to fix dependency"
                    ))
                else:
                    self.stdout.write(self.style.SUCCESS("No inconsistencies found"))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
                
                # Last resort - try to remove problematic migration record
                try:
                    cursor.execute("""
                        DELETE FROM django_migrations 
                        WHERE app = 'reports' 
                        AND name = '0003_aianalysistemplate_aianalysis';
                    """)
                    self.stdout.write(self.style.SUCCESS(
                        "Removed problematic migration record. Run migrate again."
                    ))
                except Exception as inner_e:
                    self.stdout.write(self.style.ERROR(f"Could not fix: {inner_e}"))