#!/usr/bin/env python
"""
Test runner for payment tests with proper environment setup
"""
import os
import sys

# Set environment variables before Django imports
os.environ['OPENAI_API_KEY'] = 'test-key-not-for-real-use'
os.environ['AI_INSIGHTS_ENCRYPTION_KEY'] = 'test-encryption-key-32-chars-long!!!'
os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret-key'
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings.test'

# Now import Django and run tests
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    django.setup()
    # Run payment tests with keepdb to reuse existing test database
    execute_from_command_line(['manage.py', 'test', 'apps.payments.tests', '--verbosity=2', '--keepdb'])