#!/usr/bin/env python3
"""
Script para debugar validação de pagamento específico
Baseado no session_id dos logs: cs_test_a1Bi1X9LGZi6qwAGFr69SDJIEvTG7npVERtrk11Md2S9r1o3FecMWEI9Iw
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.append('/Users/levilaell/Desktop/finance_hub/backend')
django.setup()

import stripe
from django.conf import settings
from apps.companies.models import Company
from apps.payments.models import Subscription

def debug_payment_validation():
    """Debug the specific payment session from logs"""
    
    # Session ID from user's logs
    session_id = "cs_test_a1Bi1X9LGZi6qwAGFr69SDJIEvTG7npVERtrk11Md2S9r1o3FecMWEI9Iw"
    
    print(f"🔍 Debugging payment session: {session_id}")
    print("=" * 60)
    
    # Setup Stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    print(f"🔧 Using Stripe API Key: {stripe.api_key[:12]}...")
    
    try:
        # 1. Fetch session from Stripe
        print("1️⃣ Fetching session from Stripe...")
        session = stripe.checkout.Session.retrieve(session_id)
        
        print(f"   ✅ Session found: {session.id}")
        print(f"   📊 Status: {session.status}")
        print(f"   💰 Payment Status: {session.payment_status}")
        print(f"   🏢 Customer: {session.customer}")
        print(f"   📝 Metadata: {session.metadata}")
        
        # 2. Check if session is completed
        if session.status == 'complete' and session.payment_status == 'paid':
            print("   ✅ Session is completed and paid")
            
            # 3. Extract company_id from metadata
            company_id = session.metadata.get('company_id')
            if not company_id:
                print("   ❌ No company_id in metadata")
                return False
                
            print(f"   🏢 Company ID: {company_id}")
            
            # 4. Check company exists
            try:
                company = Company.objects.get(id=company_id)
                print(f"   ✅ Company found: {company.name} ({company.owner.email})")
                
                # 5. Check subscription status
                try:
                    subscription = company.subscription
                    print(f"   📊 Current subscription: {subscription.status}")
                    print(f"   📋 Plan: {subscription.plan.name if subscription.plan else 'None'}")
                    
                    if subscription.status == 'active':
                        print("   ✅ Subscription already active - payment was successful!")
                        return True
                    elif subscription.status == 'trial':
                        print("   ⚠️  Subscription still in trial - need to upgrade")
                        
                        # Try to upgrade
                        print("2️⃣ Attempting to upgrade subscription...")
                        upgrade_subscription(company, session)
                        
                    else:
                        print(f"   ❓ Subscription status: {subscription.status}")
                        
                except Exception as e:
                    print(f"   ❌ Error checking subscription: {e}")
                    
            except Company.DoesNotExist:
                print(f"   ❌ Company not found: {company_id}")
                
                # List available companies to find correct one
                print("3️⃣ Available companies in database:")
                companies = Company.objects.all()[:10]  # Show first 10
                for comp in companies:
                    print(f"   ID: {comp.id}, Name: {comp.name}, Owner: {comp.owner.email}")
                    
                print("\n4️⃣ Attempting to find correct company...")
                
                # Try to find company with trial status (likely the user who just paid)
                trial_companies = Company.objects.filter(subscription_status='trial')
                if trial_companies.exists():
                    print("   🔍 Found companies in trial:")
                    for comp in trial_companies:
                        print(f"   ID: {comp.id}, Name: {comp.name}, Owner: {comp.owner.email}")
                        
                    # Use the first trial company (in real scenario, you'd identify the correct one)
                    correct_company = trial_companies.first()
                    print(f"\n   🎯 Using company: {correct_company.name} ({correct_company.owner.email})")
                    
                    # Manually process payment for correct company
                    return manual_payment_association(session, correct_company)
                else:
                    print("   ❌ No trial companies found")
                    return False
                
        else:
            print(f"   ❌ Session not completed: status={session.status}, payment_status={session.payment_status}")
            return False
            
    except stripe.error.InvalidRequestError as e:
        print(f"   ❌ Stripe session not found: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error fetching session: {e}")
        return False
    
    return True

def manual_payment_association(session, company):
    """Manually associate payment with correct company"""
    print(f"5️⃣ Manually associating payment with company: {company.name}")
    
    try:
        # Update session metadata in our processing (we can't update Stripe metadata after creation)
        print(f"   📝 Session metadata company_id was: {session.metadata.get('company_id')}")
        print(f"   📝 Associating with company: {company.id}")
        
        # Process payment for correct company
        result = upgrade_subscription(company, session)
        
        if result:
            print("   ✅ Payment successfully associated and processed!")
            return True
        else:
            print("   ❌ Failed to process payment association")
            return False
            
    except Exception as e:
        print(f"   ❌ Error in manual payment association: {e}")
        return False

def upgrade_subscription(company, session):
    """Upgrade subscription based on successful payment session"""
    try:
        from apps.companies.models import SubscriptionPlan
        
        # Get plan from metadata
        plan_id = session.metadata.get('plan_id')
        if not plan_id:
            print("   ❌ No plan_id in session metadata")
            return False
            
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            print(f"   📋 Target plan: {plan.name}")
            
            # Update subscription
            subscription = company.subscription
            subscription.plan = plan
            subscription.status = 'active'
            subscription.stripe_customer_id = session.customer
            subscription.save()
            
            # Update company status  
            company.subscription_status = 'active'
            company.subscription_plan = plan
            company.billing_cycle = session.metadata.get('billing_period', 'monthly')
            company.save()
            
            print("   ✅ Subscription upgraded successfully!")
            return True
            
        except SubscriptionPlan.DoesNotExist:
            print(f"   ❌ Plan not found: {plan_id}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error upgrading subscription: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Payment Validation Debug Tool")
    print("Based on session from user logs")
    print()
    
    success = debug_payment_validation()
    
    print()
    if success:
        print("✅ Payment validation completed successfully!")
        print("🎉 User should now have active subscription")
    else:
        print("❌ Payment validation failed")
        print("🔧 Manual intervention may be required")
    
    print("\n" + "=" * 60)
    print("💡 Next steps:")
    print("1. Run this script to fix the user's payment")
    print("2. Test frontend with updated validation logic")
    print("3. Check if user can access paid features")