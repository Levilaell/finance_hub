#!/usr/bin/env python
"""
Simple test runner for payment tests
"""
import os
import sys
import unittest

# Set environment variables before any imports
os.environ['OPENAI_API_KEY'] = 'test-key-not-for-real-use'
os.environ['AI_INSIGHTS_ENCRYPTION_KEY'] = 'test-encryption-key-32-chars-long!!!'
os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret-key'
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings.development'

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    # Just run the unit tests directly without full Django test runner
    test_modules = [
        'apps.payments.tests.unit.test_models',
        'apps.payments.tests.unit.test_serializers',
        'apps.payments.tests.unit.test_services',
    ]
    
    # Import Django and setup
    import django
    django.setup()
    
    # Load and run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
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
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)