#!/usr/bin/env python
"""
Test environment setup script for authentication system
Ensures all components are properly configured for testing
"""
import os
import sys
import django
from pathlib import Path

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from django.contrib.auth import get_user_model

User = get_user_model()

def cleanup_test_users():
    """Remove test users that might cause conflicts"""
    test_patterns = [
        'test_',
        'lockout_test@',
        'test_session_',
        'test_rotation_'
    ]
    
    for pattern in test_patterns:
        users = User.objects.filter(email__startswith=pattern)
        if users.exists():
            count = users.count()
            users.delete()
            print(f"✓ Cleaned up {count} test users with pattern: {pattern}")

def verify_middleware():
    """Verify all middleware classes can be imported"""
    middleware_classes = [
        'core.error_handlers.SecurityErrorMiddleware',
        'apps.payments.middleware.PaymentSecurityMiddleware',
        'core.security.RateLimitMiddleware',
        'core.security.AuditLogMiddleware'
    ]
    
    for middleware_path in middleware_classes:
        try:
            module_path, class_name = middleware_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✓ Middleware verified: {class_name}")
        except Exception as e:
            print(f"✗ Middleware error: {class_name} - {e}")
            return False
    return True

def check_database_connection():
    """Verify database connection is working"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result[0] == 1:
                print("✓ Database connection verified")
                return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def setup_test_environment():
    """Complete test environment setup"""
    print("🔧 Setting up test environment...")
    
    # Check database
    if not check_database_connection():
        return False
    
    # Verify middleware
    if not verify_middleware():
        return False
    
    # Clean up test data
    cleanup_test_users()
    
    # Ensure migrations are up to date
    print("📦 Checking migrations...")
    try:
        execute_from_command_line(['manage.py', 'migrate', '--check'])
        print("✓ Migrations are up to date")
    except SystemExit as e:
        if e.code != 0:
            print("⚠️  Migrations needed, running migrate...")
            execute_from_command_line(['manage.py', 'migrate'])
    
    print("✅ Test environment setup complete!")
    return True

if __name__ == '__main__':
    if setup_test_environment():
        print("\n🚀 Ready to run authentication tests!")
        sys.exit(0)
    else:
        print("\n❌ Test environment setup failed!")
        sys.exit(1)