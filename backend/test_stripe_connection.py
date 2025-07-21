#!/usr/bin/env python
"""Test Stripe connection and configuration"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

import stripe
from django.conf import settings

print("=== TESTING STRIPE CONNECTION ===\n")

# Check if keys are set
print(f"STRIPE_SECRET_KEY set: {'Yes' if settings.STRIPE_SECRET_KEY else 'No'}")
print(f"STRIPE_PUBLIC_KEY set: {'Yes' if settings.STRIPE_PUBLIC_KEY else 'No'}")
print(f"STRIPE_WEBHOOK_SECRET set: {'Yes' if settings.STRIPE_WEBHOOK_SECRET else 'No'}")

# Test connection
try:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    # Try to list products
    print("\nTesting Stripe API connection...")
    products = stripe.Product.list(limit=3)
    
    print(f"✓ Connection successful! Found {len(products.data)} products:")
    for product in products.data:
        print(f"  - {product.name} (ID: {product.id})")
    
    # List prices
    print("\nListing prices:")
    prices = stripe.Price.list(active=True, limit=10)
    for price in prices.data:
        interval = price.recurring.interval if price.recurring else 'one-time'
        amount = price.unit_amount / 100
        print(f"  - {price.id}: R$ {amount:.2f}/{interval}")
        
except stripe.error.AuthenticationError as e:
    print(f"\n✗ Authentication Error: {e}")
    print("Check your STRIPE_SECRET_KEY")
except Exception as e:
    print(f"\n✗ Error: {e}")