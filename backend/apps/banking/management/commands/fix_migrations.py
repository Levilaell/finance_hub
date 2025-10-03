"""
Management command to fix migration order issues
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix migration order issues by faking initial migrations'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🔧 Fixing migration order issues...'))

        # Check if banking_transaction table exists
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'banking_transaction'
                );
            """)
            table_exists = cursor.fetchone()[0]

        if table_exists:
            self.stdout.write(self.style.SUCCESS('✅ Table banking_transaction exists'))
            self.stdout.write(self.style.WARNING('Faking initial migrations...'))

            # Fake the initial migration
            from django.core.management import call_command
            try:
                call_command('migrate', 'banking', '0001', '--fake', verbosity=0)
                self.stdout.write(self.style.SUCCESS('✅ Faked banking.0001_initial'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed to fake migration: {e}'))

            # Run remaining migrations
            try:
                call_command('migrate', verbosity=1)
                self.stdout.write(self.style.SUCCESS('✅ All migrations applied'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed to apply migrations: {e}'))
        else:
            self.stdout.write(self.style.ERROR('❌ Table banking_transaction does not exist'))
            self.stdout.write(self.style.WARNING('Running migrations normally...'))

            from django.core.management import call_command
            try:
                call_command('migrate', verbosity=1)
                self.stdout.write(self.style.SUCCESS('✅ All migrations applied'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed: {e}'))
                self.stdout.write(self.style.WARNING('💡 Try: railway run python manage.py migrate --fake-initial'))
