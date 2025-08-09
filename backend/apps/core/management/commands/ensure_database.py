"""
Management command to ensure database is properly initialized
This is critical for production deployment
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Ensure database tables are created and migrations are applied'

    def fix_inconsistent_migrations(self, cursor):
        """Fix inconsistent migration history in reports app"""
        try:
            # Check if the problem exists
            cursor.execute("""
                SELECT COUNT(*) FROM django_migrations 
                WHERE app = 'reports' 
                AND name IN ('0002_alter_aianalysis_options_and_more', '0003_aianalysistemplate_aianalysis')
            """)
            count = cursor.fetchone()[0]
            
            if count == 1:
                # One is applied but not the other - fix it
                self.stdout.write('🔧 Fixing inconsistent reports migrations...')
                
                # Check which one is applied
                cursor.execute("""
                    SELECT name FROM django_migrations 
                    WHERE app = 'reports' 
                    AND name IN ('0002_alter_aianalysis_options_and_more', '0003_aianalysistemplate_aianalysis')
                """)
                result = cursor.fetchone()
                if result:
                    applied = result[0]
                    
                    if applied == '0003_aianalysistemplate_aianalysis':
                        # 0003 is applied but not 0002 - fake apply 0002
                        self.stdout.write('  📝 Marking reports.0002 as applied (fake)...')
                        cursor.execute("""
                            INSERT INTO django_migrations (app, name, applied) 
                            VALUES ('reports', '0002_alter_aianalysis_options_and_more', NOW())
                            ON CONFLICT DO NOTHING
                        """)
                        self.stdout.write(self.style.SUCCESS('  ✅ Fixed migration order'))
                        
        except Exception as e:
            self.stdout.write(f'  ⚠️ Could not fix migration inconsistency: {e}')

    def handle(self, *args, **options):
        self.stdout.write('🔍 Checking database state...')
        
        with connection.cursor() as cursor:
            # Check if migrations table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'django_migrations'
                );
            """)
            has_migrations_table = cursor.fetchone()[0]
            
            if not has_migrations_table:
                self.stdout.write(self.style.WARNING('❌ django_migrations table not found'))
                self.stdout.write('🔧 Creating initial database schema...')
                
                # Run migrations for all apps
                try:
                    call_command('migrate', '--no-input', verbosity=2)
                    self.stdout.write(self.style.SUCCESS('✅ Database initialized successfully'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Failed to initialize database: {e}'))
                    raise
            else:
                self.stdout.write(self.style.SUCCESS('✅ django_migrations table exists'))
                
                # Fix any migration inconsistencies first
                self.fix_inconsistent_migrations(cursor)
                
                # Check specific critical tables
                critical_tables = {
                    'users': 'authentication',
                    'companies': 'companies',
                    'subscription_plans': 'companies',
                }
                
                for table, app in critical_tables.items():
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = %s
                        );
                    """, [table])
                    exists = cursor.fetchone()[0]
                    
                    if exists:
                        self.stdout.write(f'  ✅ Table {table}: EXISTS')
                    else:
                        self.stdout.write(self.style.WARNING(f'  ❌ Table {table}: MISSING'))
                        self.stdout.write(f'  🔧 Running {app} migrations...')
                        try:
                            call_command('migrate', app, '--no-input', verbosity=2)
                            self.stdout.write(self.style.SUCCESS(f'  ✅ {app} migrations completed'))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'  ❌ Failed to migrate {app}: {e}'))
                
                # Run any pending migrations
                self.stdout.write('🔄 Applying any pending migrations...')
                try:
                    call_command('migrate', '--no-input', verbosity=1)
                    self.stdout.write(self.style.SUCCESS('✅ All migrations up to date'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Migration error: {e}'))
                    raise
        
        self.stdout.write(self.style.SUCCESS('\n✅ Database check complete!'))