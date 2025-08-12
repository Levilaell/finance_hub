#!/usr/bin/env python
"""
Production initialization script for Finance Hub
Run this after deploying to set up initial data
"""
import os
import sys
import django
from django.core.management import call_command
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_production():
    """Initialize production database with required data"""
    
    print("\n" + "="*60)
    print("FINANCE HUB - PRODUCTION INITIALIZATION")
    print("="*60 + "\n")
    
    try:
        # 1. Run migrations
        print("📦 Running database migrations...")
        call_command('migrate', '--noinput')
        print("✅ Migrations completed\n")
        
        # 2. Create subscription plans
        print("💳 Creating subscription plans...")
        try:
            call_command('create_subscription_plans')
            print("✅ Subscription plans created\n")
        except Exception as e:
            print(f"⚠️  Could not create subscription plans: {e}\n")
        
        # 3. Sync Pluggy connectors (banks)
        print("🏦 Syncing Pluggy connectors (banks)...")
        try:
            call_command('sync_pluggy_connectors')
            print("✅ Pluggy connectors synced\n")
        except Exception as e:
            print(f"⚠️  Could not sync Pluggy connectors: {e}")
            print("   This is expected if Pluggy API is not configured\n")
        
        # 4. Create superuser (optional, only if needed)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            print("👤 No superuser found. Please create one manually:")
            print("   python manage.py createsuperuser\n")
        else:
            print("✅ Superuser already exists\n")
        
        # 5. Collect static files
        print("📁 Collecting static files...")
        try:
            call_command('collectstatic', '--noinput')
            print("✅ Static files collected\n")
        except Exception as e:
            print(f"⚠️  Could not collect static files: {e}\n")
        
        # 6. Verify critical tables
        print("🔍 Verifying critical tables...")
        from django.db import connection
        with connection.cursor() as cursor:
            critical_tables = [
                'auth_user',
                'companies_company',
                'companies_subscriptionplan',
                'banking_pluggyconnector',
                'banking_bankaccount',
                'banking_transaction',
                'payments_subscription',
                'ai_insights_aiconversation',
                'notifications_notification',
            ]
            
            missing_tables = []
            for table in critical_tables:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, [table])
                
                if not cursor.fetchone()[0]:
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"❌ Missing tables: {', '.join(missing_tables)}")
                print("   Please check migrations\n")
            else:
                print("✅ All critical tables exist\n")
        
        # 7. Initialize default data
        print("📊 Initializing default data...")
        
        # Create default transaction categories
        from apps.banking.models import TransactionCategory
        default_categories = [
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
        
        for cat_data in default_categories:
            TransactionCategory.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
        print("✅ Default categories created\n")
        
        print("\n" + "="*60)
        print("✨ PRODUCTION INITIALIZATION COMPLETED!")
        print("="*60 + "\n")
        
        print("📝 Next steps:")
        print("1. Create a superuser if needed: python manage.py createsuperuser")
        print("2. Configure environment variables in Railway")
        print("3. Set up Pluggy webhooks in the dashboard")
        print("4. Configure payment processors (Stripe/MercadoPago)")
        print("5. Monitor logs for any issues")
        print("\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Production initialization failed: {e}")
        print(f"\n❌ Error during initialization: {e}")
        return False


if __name__ == '__main__':
    success = initialize_production()
    sys.exit(0 if success else 1)