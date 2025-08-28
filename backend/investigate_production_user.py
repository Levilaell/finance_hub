#!/usr/bin/env python
"""
Script to investigate the production database state for user arabel.bebel@hotmail.com
and identify why she's associated with company_id=4
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
import stripe
from django.conf import settings

logger = logging.getLogger(__name__)

def investigate_user(email):
    """
    Investigate the user's actual company association in the database
    """
    print(f"\n🔍 Investigating user: {email}")
    print("=" * 60)
    
    try:
        # Find the user
        user = User.objects.get(email=email)
        print(f"✅ User found:")
        print(f"   - ID: {user.id}")
        print(f"   - Email: {user.email}")
        print(f"   - Date joined: {user.date_joined}")
        print(f"   - Is active: {user.is_active}")
        
        # Check direct company relationship
        if hasattr(user, 'company'):
            company = user.company
            print(f"\n🏢 Direct company relationship (user.company):")
            print(f"   - Company ID: {company.id}")
            print(f"   - Company Name: {company.name}")
            print(f"   - Created: {company.created_at}")
        else:
            print(f"\n❌ No direct company relationship (user.company is None)")
            
        # Check if user owns any companies
        owned_companies = Company.objects.filter(owner=user)
        print(f"\n👤 Companies owned by this user:")
        if owned_companies.exists():
            for company in owned_companies:
                print(f"   - Company ID: {company.id}")
                print(f"   - Company Name: {company.name}")
                print(f"   - Created: {company.created_at}")
        else:
            print(f"   - None")
            
        # Check get_user_company function result
        company_from_util = get_user_company(user)
        print(f"\n🔧 get_user_company() result:")
        if company_from_util:
            print(f"   - Company ID: {company_from_util.id}")
            print(f"   - Company Name: {company_from_util.name}")
        else:
            print(f"   - None")
            
        # Check subscriptions linked to user
        print(f"\n💳 Subscriptions analysis:")
        
        # Direct subscription search
        subscriptions = Subscription.objects.filter(company__owner=user)
        print(f"   Subscriptions where company.owner = user:")
        for sub in subscriptions:
            print(f"     - Subscription ID: {sub.id}")
            print(f"     - Company ID: {sub.company.id}")
            print(f"     - Company Name: {sub.company.name}")
            print(f"     - Status: {sub.status}")
            print(f"     - Stripe Customer ID: {sub.stripe_customer_id}")
        
        # Check for subscriptions where user.company = subscription.company
        if hasattr(user, 'company') and user.company:
            user_company_subs = Subscription.objects.filter(company=user.company)
            print(f"   Subscriptions for user.company ({user.company.id}):")
            for sub in user_company_subs:
                print(f"     - Subscription ID: {sub.id}")
                print(f"     - Status: {sub.status}")
                print(f"     - Stripe Customer ID: {sub.stripe_customer_id}")
                
        # Check if company_id=4 exists
        print(f"\n🔍 Checking company_id=4:")
        try:
            company_4 = Company.objects.get(id=4)
            print(f"   - Company 4 exists: {company_4.name}")
            print(f"   - Owner: {company_4.owner.email if company_4.owner else 'No owner'}")
            print(f"   - Created: {company_4.created_at}")
        except Company.DoesNotExist:
            print(f"   - Company 4 does not exist")
            
        # Check Stripe customer data if available
        print(f"\n🔄 Stripe investigation:")
        if subscriptions:
            for sub in subscriptions:
                if sub.stripe_customer_id:
                    try:
                        stripe.api_key = settings.STRIPE_SECRET_KEY
                        customer = stripe.Customer.retrieve(sub.stripe_customer_id)
                        print(f"   Stripe Customer {sub.stripe_customer_id}:")
                        print(f"     - Email: {customer.email}")
                        print(f"     - Metadata: {customer.metadata}")
                        
                        # Check recent checkout sessions
                        sessions = stripe.checkout.Session.list(
                            customer=sub.stripe_customer_id,
                            limit=5
                        )
                        print(f"     - Recent sessions:")
                        for session in sessions.data:
                            print(f"       Session {session.id}: metadata = {session.metadata}")
                    except Exception as e:
                        print(f"     - Error retrieving Stripe data: {e}")
        
        return {
            'user_id': user.id,
            'email': user.email,
            'direct_company': company.id if hasattr(user, 'company') and user.company else None,
            'owned_companies': [c.id for c in owned_companies],
            'get_user_company_result': company_from_util.id if company_from_util else None,
            'subscriptions': [(s.id, s.company.id) for s in subscriptions]
        }
        
    except User.DoesNotExist:
        print(f"❌ User {email} not found")
        return None
    except Exception as e:
        print(f"❌ Error investigating user: {e}")
        return None

def check_caching():
    """
    Check for any caching mechanisms that might preserve old associations
    """
    print(f"\n🗂️ Checking for caching mechanisms:")
    print("=" * 60)
    
    # Check Django cache
    from django.core.cache import cache
    print(f"   Django cache backend: {cache.__class__.__name__}")
    
    # Check if Redis is configured
    try:
        import redis
        from django.conf import settings
        
        # Try to connect to Redis
        if hasattr(settings, 'CACHES'):
            redis_config = settings.CACHES.get('default', {})
            if 'redis' in redis_config.get('BACKEND', '').lower():
                print(f"   Redis cache is configured")
                # Try to get some cache keys
                try:
                    r = redis.Redis.from_url(redis_config.get('LOCATION', 'redis://localhost:6379'))
                    keys = r.keys('*user*company*')
                    print(f"   Found {len(keys)} Redis keys related to user/company")
                    for key in keys[:5]:  # Show first 5 keys
                        print(f"     - {key.decode() if isinstance(key, bytes) else key}")
                except Exception as e:
                    print(f"   Could not connect to Redis: {e}")
    except ImportError:
        print(f"   Redis not available")

def main():
    """
    Main investigation function
    """
    print("🕵️ Production Database Investigation")
    print("=" * 80)
    
    # Check caching first
    check_caching()
    
    # Investigate the problematic user
    result = investigate_user('arabel.bebel@hotmail.com')
    
    # Also check the development user for comparison
    print(f"\n" + "=" * 80)
    print(f"🔍 Comparison with development user:")
    dev_result = investigate_user('levilael2@hotmail.com')
    
    # Summary
    print(f"\n📋 SUMMARY:")
    print("=" * 80)
    if result:
        print(f"Production user (arabel.bebel@hotmail.com):")
        print(f"  - Direct company: {result['direct_company']}")
        print(f"  - get_user_company() returns: {result['get_user_company_result']}")
        print(f"  - Owned companies: {result['owned_companies']}")
    
    if dev_result:
        print(f"Development user (levilael2@hotmail.com):")
        print(f"  - Direct company: {dev_result['direct_company']}")
        print(f"  - get_user_company() returns: {dev_result['get_user_company_result']}")
        print(f"  - Owned companies: {dev_result['owned_companies']}")
        
    print(f"\n💡 NEXT STEPS:")
    print(f"  1. Check if the deploy actually updated the code")
    print(f"  2. Look for any cached data that needs clearing")
    print(f"  3. Verify all payment creation points use get_user_company()")
    print(f"  4. Consider database migration to fix any inconsistent data")

if __name__ == '__main__':
    main()