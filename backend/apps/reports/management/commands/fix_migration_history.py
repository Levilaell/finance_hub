"""
Management command to fix inconsistent migration history in production
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder


class Command(BaseCommand):
    help = 'Fix inconsistent migration history for reports app'

    def handle(self, *args, **options):
        self.stdout.write('Checking migration history...')
        
        recorder = MigrationRecorder(connection)
        
        # Get all reports migrations
        reports_migrations = recorder.migration_qs.filter(app='reports').order_by('name')
        
        self.stdout.write(f'Found {reports_migrations.count()} migrations for reports app:')
        for migration in reports_migrations:
            self.stdout.write(f'  - {migration.name} (applied: {migration.applied})')
        
        # Check for the specific issue
        has_0003 = reports_migrations.filter(name='0003_aianalysistemplate_aianalysis').exists()
        has_0002 = reports_migrations.filter(name='0002_alter_aianalysis_options_and_more').exists()
        
        if has_0003 and not has_0002:
            self.stdout.write(self.style.WARNING('Detected inconsistent state: 0003 applied without 0002'))
            
            # Get the timestamp from 0003
            migration_0003 = reports_migrations.get(name='0003_aianalysistemplate_aianalysis')
            
            # Create 0002 with same timestamp
            self.stdout.write('Creating missing 0002 migration record...')
            recorder.record_applied('reports', '0002_alter_aianalysis_options_and_more')
            
            # Update the timestamp to match 0003
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE django_migrations 
                    SET applied = %s 
                    WHERE app = 'reports' 
                    AND name = '0002_alter_aianalysis_options_and_more'
                """, [migration_0003.applied])
            
            self.stdout.write(self.style.SUCCESS('✅ Migration history fixed!'))
        
        elif not has_0003 and not has_0002:
            self.stdout.write(self.style.WARNING('Neither 0002 nor 0003 are applied'))
            self.stdout.write('Run: python manage.py migrate reports')
        
        else:
            self.stdout.write(self.style.SUCCESS('✅ Migration history is consistent'))
        
        # Check for duplicate 0004 migrations
        migrations_0004 = reports_migrations.filter(name__startswith='0004')
        if migrations_0004.count() > 1:
            self.stdout.write(self.style.WARNING(f'Found {migrations_0004.count()} migrations starting with 0004:'))
            for migration in migrations_0004:
                self.stdout.write(f'  - {migration.name}')
            self.stdout.write('Consider consolidating these migrations')
        
        # Show current state
        self.stdout.write('\nCurrent migration state for reports app:')
        for migration in reports_migrations.order_by('name'):
            status = '✅' if migration else '❌'
            self.stdout.write(f'  {status} {migration.name}')