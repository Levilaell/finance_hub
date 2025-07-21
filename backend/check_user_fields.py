#!/usr/bin/env python
"""Check if User model has payment_customer_id field"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Check fields
print("User model fields related to payment:")
for field in User._meta.get_fields():
    if 'payment' in field.name.lower():
        print(f"  - {field.name}: {field.get_internal_type()}")

# Check if payment_customer_id exists
if hasattr(User, 'payment_customer_id'):
    print("\n✓ payment_customer_id field exists")
else:
    print("\n✗ payment_customer_id field NOT FOUND!")
    print("\nYou need to add this field to the User model and create a migration.")