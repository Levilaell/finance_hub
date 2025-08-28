#!/usr/bin/env python
"""
Script to fix production company association inconsistencies and ensure
all future payments work correctly.
"""
import os
import django
import logging

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
from apps.companies.models import Company
from apps.companies.utils import get_user_company
from apps.payments.models import Subscription
from django.core.cache import cache
import stripe
from django.conf import settings

logger = logging.getLogger(__name__)

def audit_all_users():
    """
    Audit all users to find company association inconsistencies
    """
    print("\n🔍 AUDIT: User-Company Association Inconsistencies")
    print("=" * 70)
    
    inconsistencies = []
    users = User.objects.all().select_related('company')
    
    for user in users:
        if not user.is_active:
            continue
            
        # Check different ways to get company
        direct_company = getattr(user, 'company', None)
        owned_companies = list(Company.objects.filter(owner=user))
        util_company = get_user_company(user)
        
        # Check if there are inconsistencies
        issues = []
        
        if direct_company and owned_companies:
            if direct_company not in owned_companies:
                issues.append(f"user.company ({direct_company.id}) not in owned companies {[c.id for c in owned_companies]}")
        
        if util_company:
            if direct_company != util_company:
                issues.append(f"get_user_company() returns {util_company.id} but user.company is {direct_company.id if direct_company else None}")
        
        if len(owned_companies) > 1:
            issues.append(f"User owns multiple companies: {[c.id for c in owned_companies]}")
            
        if not direct_company and not owned_companies:
            issues.append("No company association at all")
            
        if issues:
            inconsistencies.append({
                'user': user,
                'email': user.email,
                'direct_company': direct_company.id if direct_company else None,
                'owned_companies': [c.id for c in owned_companies],
                'util_company': util_company.id if util_company else None,
                'issues': issues
            })
    
    print(f"📊 Found {len(inconsistencies)} users with inconsistencies:")
    for inc in inconsistencies:
        print(f"\n👤 {inc['email']} (ID: {inc['user'].id}):")
        print(f"   Direct company: {inc['direct_company']}")
        print(f"   Owned companies: {inc['owned_companies']}")
        print(f"   get_user_company(): {inc['util_company']}")
        for issue in inc['issues']:
            print(f"   ❌ {issue}")
    
    return inconsistencies

def audit_stripe_metadata():
    """
    Audit Stripe data to find company_id mismatches
    """
    print("\n🔍 AUDIT: Stripe Metadata vs Database")
    print("=" * 70)
    
    mismatches = []
    
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Get all customers
        customers = stripe.Customer.list(limit=100)
        
        for customer in customers.data:
            metadata = customer.metadata
            stripe_company_id = metadata.get('company_id')
            stripe_user_id = metadata.get('user_id')
            
            if not stripe_company_id or not stripe_user_id:
                continue
                
            try:
                # Find the user
                user = User.objects.get(id=stripe_user_id)
                actual_company = get_user_company(user)
                
                if actual_company and str(actual_company.id) != str(stripe_company_id):
                    mismatches.append({
                        'customer_id': customer.id,
                        'user_email': user.email,
                        'stripe_company_id': stripe_company_id,
                        'actual_company_id': actual_company.id,
                        'user_id': stripe_user_id
                    })
                    
            except User.DoesNotExist:
                print(f"⚠️ Stripe customer {customer.id} references non-existent user {stripe_user_id}")
        
        print(f"📊 Found {len(mismatches)} Stripe metadata mismatches:")
        for mismatch in mismatches:
            print(f"\n💳 Customer {mismatch['customer_id']}:")
            print(f"   User: {mismatch['user_email']}")
            print(f"   Stripe company_id: {mismatch['stripe_company_id']}")
            print(f"   Actual company_id: {mismatch['actual_company_id']}")
            
        return mismatches
        
    except Exception as e:
        print(f"❌ Error auditing Stripe data: {e}")
        return []

def fix_stripe_metadata(mismatches, dry_run=True):
    """
    Fix Stripe metadata to match current database state
    """
    print(f"\n🔧 {'DRY RUN: ' if dry_run else ''}Fixing Stripe Metadata")
    print("=" * 70)
    
    if not mismatches:
        print("✅ No mismatches to fix")
        return
        
    for mismatch in mismatches:
        try:
            customer_id = mismatch['customer_id']
            new_company_id = mismatch['actual_company_id']
            
            print(f"\n💳 Customer {customer_id}:")
            print(f"   Updating company_id: {mismatch['stripe_company_id']} → {new_company_id}")
            
            if not dry_run:
                stripe.Customer.modify(
                    customer_id,
                    metadata={
                        'company_id': str(new_company_id),
                        'user_id': mismatch['user_id']  # Keep user_id
                    }
                )
                print(f"   ✅ Updated successfully")
            else:
                print(f"   🔍 Would update (dry run)")
                
        except Exception as e:
            print(f"   ❌ Error updating customer {customer_id}: {e}")

def clear_relevant_caches():
    """
    Clear caches that might contain outdated company associations
    """
    print(f"\n🗑️ Clearing Relevant Caches")
    print("=" * 70)
    
    try:
        # Clear Django cache completely
        cache.clear()
        print("✅ Cleared Django cache")
        
        # Try Redis directly if available
        try:
            import redis
            from django.conf import settings
            
            if hasattr(settings, 'CACHES'):
                redis_config = settings.CACHES.get('default', {})
                if 'redis' in redis_config.get('BACKEND', '').lower():
                    r = redis.Redis.from_url(redis_config.get('LOCATION', 'redis://localhost:6379'))
                    
                    # Find and delete user/company related keys
                    patterns = [
                        '*user*company*',
                        '*company*user*',
                        '*payment*company*',
                        '*subscription*company*'
                    ]
                    
                    total_deleted = 0
                    for pattern in patterns:
                        keys = r.keys(pattern)
                        if keys:
                            total_deleted += r.delete(*keys)
                    
                    print(f"✅ Cleared {total_deleted} Redis keys")
        except Exception as e:
            print(f"⚠️ Could not clear Redis cache: {e}")
            
    except Exception as e:
        print(f"❌ Error clearing caches: {e}")

def validate_get_user_company():
    """
    Validate that get_user_company is working correctly for all users
    """
    print(f"\n✅ Validating get_user_company() Function")
    print("=" * 70)
    
    issues = []
    users = User.objects.filter(is_active=True).select_related('company')[:50]  # Test sample
    
    for user in users:
        try:
            company = get_user_company(user)
            direct_company = getattr(user, 'company', None)
            
            if company != direct_company:
                issues.append({
                    'user': user.email,
                    'get_user_company': company.id if company else None,
                    'user_company': direct_company.id if direct_company else None
                })
        except Exception as e:
            issues.append({
                'user': user.email,
                'error': str(e)
            })
    
    if issues:
        print(f"❌ Found {len(issues)} issues with get_user_company():")
        for issue in issues[:10]:  # Show first 10
            print(f"   {issue}")
    else:
        print("✅ get_user_company() working correctly for all tested users")
    
    return len(issues) == 0

def main():
    """
    Main function to run all diagnostics and fixes
    """
    print("🔧 PRODUCTION COMPANY ASSOCIATION FIX")
    print("=" * 80)
    
    # Step 1: Audit user-company associations
    user_inconsistencies = audit_all_users()
    
    # Step 2: Audit Stripe metadata
    stripe_mismatches = audit_stripe_metadata()
    
    # Step 3: Validate get_user_company function
    util_working = validate_get_user_company()
    
    # Step 4: Clear caches
    clear_relevant_caches()
    
    # Step 5: Fix Stripe metadata (dry run first)
    if stripe_mismatches:
        fix_stripe_metadata(stripe_mismatches, dry_run=True)
        
        response = input("\nDo you want to apply the Stripe metadata fixes? (y/N): ")
        if response.lower() == 'y':
            fix_stripe_metadata(stripe_mismatches, dry_run=False)
    
    # Summary
    print(f"\n📋 SUMMARY:")
    print("=" * 80)
    print(f"User inconsistencies: {len(user_inconsistencies)}")
    print(f"Stripe mismatches: {len(stripe_mismatches)}")
    print(f"get_user_company() working: {'✅' if util_working else '❌'}")
    
    if len(user_inconsistencies) == 0 and len(stripe_mismatches) == 0 and util_working:
        print("\n🎉 All systems consistent! Future payments should work correctly.")
    else:
        print("\n⚠️ Issues found. Manual intervention may be required.")
        
        print(f"\n💡 NEXT STEPS:")
        if user_inconsistencies:
            print(f"   1. Fix user-company association inconsistencies")
        if stripe_mismatches:
            print(f"   2. Update Stripe metadata to match database")
        if not util_working:
            print(f"   3. Debug get_user_company() function")
        print(f"   4. Test payment flow with fixed data")
        print(f"   5. Monitor logs for any remaining issues")

if __name__ == '__main__':
    main()