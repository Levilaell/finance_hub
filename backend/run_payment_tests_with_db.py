#!/usr/bin/env python
"""
Test runner for payment tests with proper database setup
"""
import os
import sys
import django
from django.core.management import call_command

# Set environment variables before any imports
os.environ['OPENAI_API_KEY'] = 'test-key-not-for-real-use'
os.environ['AI_INSIGHTS_ENCRYPTION_KEY'] = 'test-encryption-key-32-chars-long!!!'
os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret-key'
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings.development'

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    # Setup Django
    django.setup()
    
    print("Creating test database...")
    # Create test database
    from django.db import connection
    from django.core.management.commands.test import Command as TestCommand
    from django.test.utils import setup_test_environment, teardown_test_environment
    
    # Setup test environment
    setup_test_environment()
    
    # Create test database
    test_db_name = 'test_finance_db'
    with connection.cursor() as cursor:
        # Drop existing test database
        cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
        # Create new test database
        cursor.execute(f"CREATE DATABASE {test_db_name}")
    
    # Switch to test database
    from django.conf import settings
    settings.DATABASES['default']['NAME'] = test_db_name
    
    # Run migrations
    print("Running migrations...")
    call_command('migrate', verbosity=0, interactive=False)
    
    # Run tests
    print("Running payment tests...")
    import unittest
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Load test modules
    test_modules = [
        'apps.payments.tests.unit.test_models',
        'apps.payments.tests.unit.test_serializers',
        'apps.payments.tests.unit.test_services',
    ]
    
    for module_name in test_modules:
        try:
            module = __import__(module_name, fromlist=[''])
            tests = loader.loadTestsFromModule(module)
            suite.addTests(tests)
        except Exception as e:
            print(f"Error loading {module_name}: {e}")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Cleanup
    print("\nCleaning up...")
    teardown_test_environment()
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)