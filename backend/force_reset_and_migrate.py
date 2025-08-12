#!/usr/bin/env python
"""
Force reset and migrate - use when migrations are stuck
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.core.management import call_command
from django.db import connection

print("\n" + "="*60)
print("FORCE RESET AND MIGRATE")
print("="*60 + "\n")

try:
    with connection.cursor() as cursor:
        print("1. Dropping all tables...")
        
        # Get all tables
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public';
        """)
        tables = [t[0] for t in cursor.fetchall()]
        
        if tables:
            # Disable foreign key checks
            cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
            
            # Drop all tables including django_migrations
            for table in tables:
                print(f"   Dropping: {table}")
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            
            print(f"   ✅ Dropped {len(tables)} tables\n")
        else:
            print("   No tables to drop\n")
    
    print("2. Running migrations from scratch...")
    call_command('migrate', '--noinput', '--run-syncdb')
    print("   ✅ Migrations completed\n")
    
    print("3. Creating initial data...")
    
    # Create subscription plans
    try:
        call_command('create_subscription_plans')
        print("   ✅ Subscription plans created")
    except:
        print("   ⚠️  Could not create subscription plans")
    
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
        print("   ✅ Categories created")
    except:
        print("   ⚠️  Could not create categories")
    
    print("\n" + "="*60)
    print("✅ FORCE RESET COMPLETED SUCCESSFULLY!")
    print("="*60 + "\n")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    sys.exit(1)