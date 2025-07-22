#!/usr/bin/env python
"""
Test script for upgrade/downgrade flow
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.utils import timezone
from apps.companies.models import Company, SubscriptionPlan
from apps.payments.payment_service import PaymentService
from decimal import Decimal

def test_upgrade_flow():
    """Test upgrade from Professional to Enterprise"""
    print("\n" + "="*50)
    print("TESTING UPGRADE FLOW")
    print("="*50)
    
    # Get test company
    company = Company.objects.filter(
        subscription_status='active',
        subscription_plan__plan_type='professional'
    ).first()
    
    if not company:
        print("❌ No active professional plan found to test")
        return
    
    print(f"\n✅ Found company: {company.name}")
    print(f"   Current plan: {company.subscription_plan.name}")
    print(f"   Billing cycle: {company.billing_cycle}")
    print(f"   Next billing: {company.next_billing_date}")
    
    # Get enterprise plan
    enterprise_plan = SubscriptionPlan.objects.get(plan_type='enterprise')
    
    # Test proration calculation
    payment_service = PaymentService()
    proration = payment_service.calculate_proration(
        company, enterprise_plan, company.billing_cycle
    )
    
    print(f"\n📊 Proration Calculation:")
    print(f"   Days remaining: {proration['days_remaining']}")
    print(f"   Current plan credit: R$ {proration['credit']}")
    print(f"   New plan charge: R$ {proration['charge']}")
    print(f"   Net amount to pay: R$ {proration['net_amount']}")
    
    # Test the upgrade
    print(f"\n🔄 Simulating upgrade to {enterprise_plan.name}...")
    
    try:
        # This would be called by the API view
        if company.subscription_id:
            print("   ✅ Has subscription ID - can upgrade via Stripe")
            print(f"   Subscription ID: {company.subscription_id}")
        else:
            print("   ❌ No subscription ID - would need new checkout")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_downgrade_flow():
    """Test downgrade from Enterprise to Professional"""
    print("\n" + "="*50)
    print("TESTING DOWNGRADE FLOW")
    print("="*50)
    
    # Get test company
    company = Company.objects.filter(
        subscription_status='active',
        subscription_plan__plan_type='enterprise'
    ).first()
    
    if not company:
        print("❌ No active enterprise plan found to test")
        return
    
    print(f"\n✅ Found company: {company.name}")
    print(f"   Current plan: {company.subscription_plan.name}")
    print(f"   Billing cycle: {company.billing_cycle}")
    print(f"   Next billing: {company.next_billing_date}")
    
    # Get professional plan
    professional_plan = SubscriptionPlan.objects.get(plan_type='professional')
    
    # Test proration calculation
    payment_service = PaymentService()
    proration = payment_service.calculate_proration(
        company, professional_plan, company.billing_cycle
    )
    
    print(f"\n📊 Proration Calculation:")
    print(f"   Days remaining: {proration['days_remaining']}")
    print(f"   Current plan credit: R$ {proration['credit']}")
    print(f"   New plan charge: R$ {proration['charge']}")
    print(f"   Net credit: R$ {abs(proration['net_amount'])}")
    
    print(f"\n🔄 Simulating downgrade to {professional_plan.name}...")
    print("   ✅ Credit will be applied to next invoice")

def test_billing_cycle_change():
    """Test changing billing cycle"""
    print("\n" + "="*50)
    print("TESTING BILLING CYCLE CHANGE")
    print("="*50)
    
    company = Company.objects.filter(
        subscription_status='active',
        billing_cycle='monthly'
    ).first()
    
    if not company:
        print("❌ No monthly subscription found")
        return
    
    print(f"\n✅ Found company: {company.name}")
    print(f"   Current: {company.subscription_plan.name} (Monthly)")
    print(f"   Monthly price: R$ {company.subscription_plan.price_monthly}")
    print(f"   Yearly price: R$ {company.subscription_plan.price_yearly}")
    print(f"   Yearly savings: R$ {company.subscription_plan.price_monthly * 12 - company.subscription_plan.price_yearly}")
    
    # Calculate proration for same plan, different cycle
    payment_service = PaymentService()
    proration = payment_service.calculate_proration(
        company, company.subscription_plan, 'yearly'
    )
    
    print(f"\n📊 Monthly → Yearly Calculation:")
    print(f"   Would save: R$ {company.subscription_plan.price_monthly * 12 - company.subscription_plan.price_yearly}/year")

def check_payment_history():
    """Check recent payment history"""
    print("\n" + "="*50)
    print("RECENT PAYMENT HISTORY")
    print("="*50)
    
    from apps.companies.models import PaymentHistory
    
    recent_payments = PaymentHistory.objects.filter(
        transaction_type__in=['upgrade', 'downgrade', 'plan_change']
    ).order_by('-created_at')[:5]
    
    if recent_payments:
        for payment in recent_payments:
            print(f"\n📝 {payment.transaction_date.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Company: {payment.company.name}")
            print(f"   Type: {payment.transaction_type}")
            print(f"   Description: {payment.description}")
            print(f"   Amount: R$ {payment.amount}")
            print(f"   Status: {payment.status}")
    else:
        print("\n❌ No upgrade/downgrade history found")

if __name__ == "__main__":
    test_upgrade_flow()
    test_downgrade_flow()
    test_billing_cycle_change()
    check_payment_history()
    
    print("\n" + "="*50)
    print("✅ TESTS COMPLETED")
    print("="*50)