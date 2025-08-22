#!/usr/bin/env python
"""
Debug script for EarlyAccessInvite admin 500 error
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.db import connection
from apps.companies.models import EarlyAccessInvite
from apps.companies.admin import EarlyAccessInviteAdmin
from django.contrib import admin
from django.http import HttpRequest
from django.contrib.auth import get_user_model

User = get_user_model()

def check_table_structure():
    """Check if early_access_invites table exists and has correct structure"""
    print("=== DATABASE TABLE CHECK ===")
    try:
        with connection.cursor() as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'early_access_invites'
                );
            """)
            exists = cursor.fetchone()[0]
            
            if exists:
                print('✅ Table early_access_invites exists')
                
                # Get table columns
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'early_access_invites'
                    ORDER BY ordinal_position;
                """)
                
                columns = cursor.fetchall()
                print('Table columns:')
                for col in columns:
                    print(f'  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})')
                    
                # Check if we can query the table
                cursor.execute("SELECT COUNT(*) FROM early_access_invites;")
                count = cursor.fetchone()[0]
                print(f'✅ Table has {count} records')
                
            else:
                print('❌ Table early_access_invites does not exist')
                return False
                
    except Exception as e:
        print(f'❌ Database error: {e}')
        return False
    
    return True

def check_model():
    """Check if EarlyAccessInvite model works"""
    print("\n=== MODEL CHECK ===")
    try:
        # Test model access
        count = EarlyAccessInvite.objects.count()
        print(f'✅ EarlyAccessInvite model works: {count} objects')
        
        # Test model fields
        print('Model fields:')
        for field in EarlyAccessInvite._meta.fields:
            print(f'  - {field.name}: {field.__class__.__name__}')
            
    except Exception as e:
        print(f'❌ Model error: {e}')
        import traceback
        traceback.print_exc()
        return False
    
    return True

def check_admin():
    """Check if admin configuration works"""
    print("\n=== ADMIN CHECK ===")
    try:
        # Check if admin is registered
        admin_class = admin.site._registry.get(EarlyAccessInvite)
        if admin_class:
            print(f'✅ EarlyAccessInvite is registered with admin: {admin_class.__class__.__name__}')
            
            # Test admin methods
            admin_instance = admin_class
            
            # Create a mock request
            request = HttpRequest()
            request.user = User.objects.filter(is_superuser=True).first()
            
            if not request.user:
                print('❌ No superuser found for testing')
                return False
                
            print(f'✅ Using admin user: {request.user.email}')
            
            # Test queryset
            qs = admin_instance.get_queryset(request)
            print(f'✅ Admin queryset works: {qs.count()} objects')
            
            # Test list display methods
            if qs.exists():
                obj = qs.first()
                print('Testing admin display methods:')
                
                try:
                    result = admin_instance.used_by_email(obj)
                    print(f'✅ used_by_email: {result}')
                except Exception as e:
                    print(f'❌ used_by_email error: {e}')
                
                try:
                    result = admin_instance.days_remaining(obj)
                    print(f'✅ days_remaining: {result}')
                except Exception as e:
                    print(f'❌ days_remaining error: {e}')
            
            # Test fieldsets
            print('Fieldsets configuration:')
            for name, options in admin_instance.fieldsets:
                print(f'  {name}: {options["fields"]}')
                
        else:
            print('❌ EarlyAccessInvite not registered with admin')
            return False
            
    except Exception as e:
        print(f'❌ Admin error: {e}')
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Run all checks"""
    print("Finance Hub - EarlyAccessInvite Admin Debug")
    print("=" * 50)
    
    # Run checks
    table_ok = check_table_structure()
    model_ok = check_model()
    admin_ok = check_admin()
    
    print("\n=== SUMMARY ===")
    print(f"Database table: {'✅' if table_ok else '❌'}")
    print(f"Django model: {'✅' if model_ok else '❌'}")
    print(f"Admin config: {'✅' if admin_ok else '❌'}")
    
    if table_ok and model_ok and admin_ok:
        print("\n✅ All checks passed - admin should work")
    else:
        print("\n❌ Some checks failed - this explains the 500 error")

if __name__ == '__main__':
    main()