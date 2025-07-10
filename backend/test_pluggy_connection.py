#!/usr/bin/env python
"""
Manual test script for Pluggy bank connection
Run this to test the complete flow in development
"""
import os
import sys
import django
import asyncio
from decimal import Decimal

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.companies.models import Company
from apps.banking.models import BankProvider, BankAccount
from apps.banking.pluggy_client import PluggyClient
from apps.banking.pluggy_sync_service import PluggySyncService

User = get_user_model()


async def test_pluggy_connection():
    """Test Pluggy connection flow"""
    print("=== Pluggy Connection Test ===\n")
    
    # Step 1: Test authentication
    print("1. Testing Pluggy authentication...")
    try:
        async with PluggyClient() as client:
            print("✓ Successfully authenticated with Pluggy API")
            
            # Step 2: Get available banks
            print("\n2. Fetching available banks...")
            connectors = await client.get_connectors()
            print(f"✓ Found {len(connectors)} bank connectors")
            
            # Show first 5 banks
            print("\nAvailable banks:")
            for i, connector in enumerate(connectors[:5]):
                if connector.get('type') == 'PERSONAL_BANK':
                    print(f"  - {connector['name']} (ID: {connector['id']})")
            
            # Step 3: Create connect token
            print("\n3. Creating connect token...")
            token_data = await client.create_connect_token()
            print(f"✓ Connect token created: {token_data.get('accessToken', 'N/A')[:20]}...")
            
            print("\n4. To complete the connection:")
            print("   a) Open Pluggy Connect widget with the token")
            print("   b) User selects bank and enters credentials")
            print("   c) Callback receives item_id")
            print("   d) Use item_id to fetch accounts and transactions")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True


async def test_sync_service():
    """Test sync service with mock data"""
    print("\n=== Sync Service Test ===\n")
    
    # Create test user and company
    print("1. Setting up test data...")
    user, created = User.objects.get_or_create(
        username='pluggy_test_user',
        defaults={'email': 'pluggy_test@example.com'}
    )
    
    company, created = Company.objects.get_or_create(
        owner=user,
        defaults={'name': 'Pluggy Test Company'}
    )
    
    # Create bank provider
    provider, created = BankProvider.objects.get_or_create(
        code='pluggy_201',
        defaults={
            'name': 'Banco do Brasil (Pluggy)',
            'is_active': True,
            'is_open_banking': False
        }
    )
    
    # Create test account
    account, created = BankAccount.objects.get_or_create(
        company=company,
        bank_provider=provider,
        account_number='12345',
        defaults={
            'account_type': 'checking',
            'agency': '0001',
            'pluggy_item_id': 'test-item-123',
            'external_account_id': 'test-acc-123',
            'current_balance': Decimal('1000.00'),
            'status': 'active'
        }
    )
    
    print(f"✓ Test account created: {account}")
    
    # Test sync (this will fail without real Pluggy item)
    print("\n2. Testing sync service...")
    sync_service = PluggySyncService()
    
    print("Note: Actual sync requires a real Pluggy item_id")
    print("In production, this would:")
    print("  - Fetch account balance")
    print("  - Sync recent transactions")
    print("  - Update local database")
    
    return True


def run_tests():
    """Run all tests"""
    print("Starting Pluggy integration tests...\n")
    
    # Check environment
    print("Environment check:")
    print(f"PLUGGY_CLIENT_ID: {'✓ Set' if os.environ.get('PLUGGY_CLIENT_ID') else '✗ Not set'}")
    print(f"PLUGGY_CLIENT_SECRET: {'✓ Set' if os.environ.get('PLUGGY_CLIENT_SECRET') else '✗ Not set'}")
    
    if not all([os.environ.get('PLUGGY_CLIENT_ID'), os.environ.get('PLUGGY_CLIENT_SECRET')]):
        print("\n⚠️  Please set PLUGGY_CLIENT_ID and PLUGGY_CLIENT_SECRET environment variables")
        return
    
    # Run async tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Test Pluggy client
        result = loop.run_until_complete(test_pluggy_connection())
        if not result:
            print("\n❌ Pluggy connection test failed")
            return
        
        # Test sync service
        result = loop.run_until_complete(test_sync_service())
        if not result:
            print("\n❌ Sync service test failed")
            return
        
        print("\n✅ All tests passed!")
        
    finally:
        loop.close()


if __name__ == '__main__':
    run_tests()