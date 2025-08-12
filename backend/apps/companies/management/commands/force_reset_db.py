"""
Force reset database - drops all tables and recreates
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Force reset database by dropping all tables and recreating'

    def add_arguments(self, parser):
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        if not options['yes']:
            self.stdout.write(self.style.WARNING(
                '\n⚠️  WARNING: This will DELETE ALL DATA in the database!'
            ))
            confirm = input('Type "yes" to continue: ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Aborted.'))
                return

        self.stdout.write('\n🔄 Starting database reset...\n')

        try:
            with connection.cursor() as cursor:
                # Get all tables
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public';
                """)
                tables = [t[0] for t in cursor.fetchall()]
                
                if tables:
                    self.stdout.write(f'📊 Found {len(tables)} tables to drop')
                    
                    # Disable foreign key checks
                    cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
                    
                    # Drop all tables
                    for table in tables:
                        self.stdout.write(f'   Dropping: {table}')
                        cursor.execute(f'DROP TABLE IF EXISTS {table} CASCADE;')
                    
                    self.stdout.write(self.style.SUCCESS(f'\n✅ Dropped {len(tables)} tables\n'))
                else:
                    self.stdout.write('No tables found to drop\n')
            
            # Run migrations
            self.stdout.write('🔄 Running migrations...')
            call_command('migrate', '--noinput', '--run-syncdb', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✅ Migrations completed\n'))
            
            # Create initial data
            self.stdout.write('📊 Creating initial data...')
            
            # Create subscription plans
            try:
                call_command('create_subscription_plans', verbosity=0)
                self.stdout.write('   ✅ Subscription plans created')
            except:
                self.stdout.write('   ⚠️  Could not create subscription plans')
            
            # Create categories
            try:
                from apps.banking.models import TransactionCategory
                categories = [
                    {'name': 'Alimentação', 'slug': 'alimentacao', 'icon': '🍴', 'color': '#FF6B6B'},
                    {'name': 'Transporte', 'slug': 'transporte', 'icon': '🚗', 'color': '#4ECDC4'},
                    {'name': 'Moradia', 'slug': 'moradia', 'icon': '🏠', 'color': '#45B7D1'},
                    {'name': 'Saúde', 'slug': 'saude', 'icon': '⚕️', 'color': '#96CEB4'},
                    {'name': 'Educação', 'slug': 'educacao', 'icon': '📚', 'color': '#FECA57'},
                    {'name': 'Lazer', 'slug': 'lazer', 'icon': '🎮', 'color': '#9C88FF'},
                    {'name': 'Compras', 'slug': 'compras', 'icon': '🛍️', 'color': '#FD79A8'},
                    {'name': 'Serviços', 'slug': 'servicos', 'icon': '🔧', 'color': '#A29BFE'},
                    {'name': 'Investimentos', 'slug': 'investimentos', 'icon': '📈', 'color': '#00B894'},
                    {'name': 'Outros', 'slug': 'outros', 'icon': '📌', 'color': '#636E72'},
                ]
                for cat in categories:
                    TransactionCategory.objects.get_or_create(slug=cat['slug'], defaults=cat)
                self.stdout.write('   ✅ Categories created')
            except:
                self.stdout.write('   ⚠️  Could not create categories')
            
            self.stdout.write(self.style.SUCCESS(
                '\n' + '='*60 + '\n' +
                '✨ DATABASE RESET COMPLETED SUCCESSFULLY!\n' +
                '='*60 + '\n'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error: {e}\n'))
            raise