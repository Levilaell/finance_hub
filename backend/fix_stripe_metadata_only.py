#!/usr/bin/env python
"""
Fix Stripe customer metadata without database access.
Since we found ALL Stripe customers for arabel.bebel@hotmail.com have stale company_id=4,
this script updates them to use the correct company ID.
"""
import os
import stripe

# Setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')

# Import Django settings but avoid database setup since Railway can't connect to DB
from django.conf import settings
stripe.api_key = settings.STRIPE_SECRET_KEY

def fix_stripe_metadata_for_user(email, correct_company_id, dry_run=True):
    """
    Fix Stripe customer metadata for a specific user
    """
    print(f"🔧 {'DRY RUN: ' if dry_run else ''}Fixing Stripe metadata for {email}")
    print(f"📝 Setting company_id to: {correct_company_id}")
    print("=" * 70)
    
    # Get all customers for this email
    customers = stripe.Customer.list(email=email, limit=10)
    
    if not customers.data:
        print(f"❌ No Stripe customers found for {email}")
        return
    
    print(f"🔍 Found {len(customers.data)} customers to update:")
    
    for customer in customers.data:
        current_metadata = customer.metadata
        current_company_id = current_metadata.get('company_id')
        user_id = current_metadata.get('user_id')
        
        print(f"\n💳 Customer: {customer.id}")
        print(f"   Current company_id: {current_company_id}")
        print(f"   User ID: {user_id}")
        
        if current_company_id == str(correct_company_id):
            print(f"   ✅ Already correct, skipping")
            continue
            
        if dry_run:
            print(f"   🔍 Would update: {current_company_id} → {correct_company_id}")
        else:
            try:
                # Update customer metadata
                stripe.Customer.modify(
                    customer.id,
                    metadata={
                        'company_id': str(correct_company_id),
                        'user_id': user_id  # Keep existing user_id
                    }
                )
                print(f"   ✅ Updated successfully: {current_company_id} → {correct_company_id}")
            except Exception as e:
                print(f"   ❌ Error updating customer {customer.id}: {e}")

def main():
    print("🔧 STRIPE METADATA FIX")
    print("=" * 50)
    
    # Based on Stripe investigation, all customers have company_id=4
    # We need to determine the correct company_id for arabel.bebel@hotmail.com
    
    # First run dry-run to see what would be changed
    print("\n=== DRY RUN ===")
    
    # We need to determine the correct company_id
    # Options:
    # 1. Ask user what the correct company_id should be
    # 2. Try to infer from other data
    # 3. Use a safe default or create new company
    
    print("❗ ATTENTION: Need to determine correct company_id")
    print("Current situation:")
    print("  - All Stripe customers have company_id=4")
    print("  - User ID is 6 (from Stripe metadata)")
    print("  - Need to check what company this user should actually have")
    
    print("\nTo complete the fix:")
    print("1. Check user's actual company_id in database")
    print("2. Run this script with: python fix_stripe_metadata_only.py {correct_company_id}")
    
    # For now, show what customers exist
    customers = stripe.Customer.list(email='arabel.bebel@hotmail.com', limit=10)
    print(f"\n📊 Summary: {len(customers.data)} customers need company_id updated from '4' to correct value")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        # Usage: python fix_stripe_metadata_only.py 123 [--apply]
        correct_company_id = sys.argv[1]
        apply_fix = '--apply' in sys.argv
        
        fix_stripe_metadata_for_user(
            'arabel.bebel@hotmail.com', 
            correct_company_id, 
            dry_run=not apply_fix
        )
    else:
        main()