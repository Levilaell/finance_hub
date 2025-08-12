#!/usr/bin/env python
"""
Test script for MVP plan limit corrections
Tests the new safe methods for preventing race conditions
"""
import os
import sys
import django
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.db import transaction
from apps.companies.models import Company, SubscriptionPlan
from apps.banking.models import Transaction, BankAccount
from apps.authentication.models import User
from rest_framework.exceptions import PermissionDenied


def test_safe_increment():
    """Test the new increment_usage_safe method"""
    print("\n🧪 Testing increment_usage_safe method...")
    
    # Create test company with plan
    plan = SubscriptionPlan.objects.filter(slug='starter').first()
    if not plan:
        print("❌ No starter plan found. Run create_subscription_plans first.")
        return False
    
    # Create test user and company
    test_user = User.objects.create_user(
        username='test_limits',
        email='test_limits@test.com',
        password='test123'
    )
    
    company = Company.objects.create(
        owner=test_user,
        name='Test Limits Company',
        subscription_plan=plan,
        current_month_transactions=plan.max_transactions - 2  # Near limit
    )
    
    print(f"✅ Created test company with {company.current_month_transactions}/{plan.max_transactions} transactions")
    
    # Test 1: Successful increment
    success, message = company.increment_usage_safe('transactions')
    assert success == True, "Should allow increment when under limit"
    print(f"✅ Increment 1 succeeded: {message}")
    
    # Test 2: Another successful increment (reaching limit)
    success, message = company.increment_usage_safe('transactions')
    assert success == True, "Should allow increment up to limit"
    print(f"✅ Increment 2 succeeded: {message}")
    
    # Test 3: Should fail - at limit
    success, message = company.increment_usage_safe('transactions')
    assert success == False, "Should prevent increment when at limit"
    print(f"✅ Increment 3 correctly blocked: {message}")
    
    # Cleanup
    company.delete()
    test_user.delete()
    
    print("✅ All increment_usage_safe tests passed!")
    return True


def test_transaction_creation():
    """Test the new Transaction.create_safe method"""
    print("\n🧪 Testing Transaction.create_safe method...")
    
    # Setup
    from apps.banking.models import PluggyConnector, PluggyItem
    from django.utils import timezone
    
    plan = SubscriptionPlan.objects.filter(slug='starter').first()
    test_user = User.objects.create_user(
        username='test_trans',
        email='test_trans@test.com',
        password='test123'
    )
    
    company = Company.objects.create(
        owner=test_user,
        name='Test Transaction Company',
        subscription_plan=plan,
        current_month_transactions=plan.max_transactions - 1  # One below limit
    )
    
    # Create connector first
    connector = PluggyConnector.objects.create(
        pluggy_id=999999,
        name='Test Bank',
        type='PERSONAL_BANK',
        country='BR'
    )
    
    # Create item
    item = PluggyItem.objects.create(
        pluggy_item_id='test_item_123',
        company=company,
        connector=connector,
        status='UPDATED',
        pluggy_created_at=timezone.now(),
        pluggy_updated_at=timezone.now()
    )
    
    # Create a fake bank account
    account = BankAccount.objects.create(
        company=company,
        item=item,
        name='Test Account',
        pluggy_account_id='test_account_123',
        type='BANK',
        subtype='CHECKING_ACCOUNT',
        balance=1000.00,
        pluggy_created_at=timezone.now(),
        pluggy_updated_at=timezone.now()
    )
    
    print(f"✅ Setup complete: {company.current_month_transactions}/{plan.max_transactions} transactions")
    
    # Test 1: Create transaction successfully
    try:
        trans1 = Transaction.create_safe(
            company=company,
            pluggy_transaction_id='test_trans_1',
            account=account,
            type='DEBIT',
            amount=Decimal('100.00'),
            description='Test transaction 1',
            date=timezone.now(),
            pluggy_created_at=timezone.now(),
            pluggy_updated_at=timezone.now()
        )
        print(f"✅ Transaction 1 created: ID={trans1.id}")
    except Exception as e:
        print(f"❌ Failed to create transaction 1: {e}")
        return False
    
    # Test 2: Try to create another transaction - should fail
    try:
        trans2 = Transaction.create_safe(
            company=company,
            pluggy_transaction_id='test_trans_2',
            account=account,
            type='DEBIT',
            amount=Decimal('200.00'),
            description='Test transaction 2',
            date=timezone.now(),
            pluggy_created_at=timezone.now(),
            pluggy_updated_at=timezone.now()
        )
        print(f"❌ Transaction 2 should have been blocked!")
        return False
    except PermissionDenied as e:
        print(f"✅ Transaction 2 correctly blocked: {e.detail}")
    
    # Cleanup
    Transaction.objects.filter(company=company).delete()
    account.delete()
    item.delete()
    connector.delete()
    company.delete()
    test_user.delete()
    
    print("✅ All Transaction.create_safe tests passed!")
    return True


def test_race_condition():
    """Test that race conditions are prevented"""
    print("\n🧪 Testing race condition prevention...")
    
    # Setup
    plan = SubscriptionPlan.objects.filter(slug='starter').first()
    test_user = User.objects.create_user(
        username='test_race',
        email='test_race@test.com',
        password='test123'
    )
    
    # Set transactions to 2 below limit
    company = Company.objects.create(
        owner=test_user,
        name='Test Race Company',
        subscription_plan=plan,
        current_month_transactions=plan.max_transactions - 2
    )
    
    print(f"✅ Setup: {company.current_month_transactions}/{plan.max_transactions} transactions")
    
    # Function to increment usage
    def try_increment(company_id, thread_id):
        """Try to increment usage from a thread"""
        company = Company.objects.get(pk=company_id)
        success, message = company.increment_usage_safe('transactions')
        return (thread_id, success, message)
    
    # Try to increment 5 times concurrently (but only 2 should succeed)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in range(5):
            future = executor.submit(try_increment, company.id, i)
            futures.append(future)
        
        results = [f.result() for f in futures]
    
    # Count successes
    successes = sum(1 for _, success, _ in results if success)
    failures = sum(1 for _, success, _ in results if not success)
    
    print(f"✅ Results: {successes} succeeded, {failures} blocked")
    
    # Refresh company
    company.refresh_from_db()
    expected = plan.max_transactions
    actual = company.current_month_transactions
    
    if actual == expected and successes == 2 and failures == 3:
        print(f"✅ Race condition prevented! Final count: {actual}/{expected}")
        result = True
    else:
        print(f"❌ Race condition NOT prevented! Expected {expected}, got {actual}")
        result = False
    
    # Cleanup
    company.delete()
    test_user.delete()
    
    return result


def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 MVP PLAN LIMITS TESTING")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Safe increment
    if not test_safe_increment():
        all_passed = False
    
    # Test 2: Safe transaction creation
    if not test_transaction_creation():
        all_passed = False
    
    # Test 3: Race condition prevention
    if not test_race_condition():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED! MVP corrections are working.")
    else:
        print("❌ SOME TESTS FAILED! Review the corrections.")
    print("=" * 60)
    
    return all_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)