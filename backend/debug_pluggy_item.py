#!/usr/bin/env python
"""
Debug script for PluggyItem 500 error in Django admin
Tests specific record that's causing issues
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.banking.models import PluggyItem
from apps.banking.utils.encryption import banking_encryption
import traceback
import json

def test_pluggy_item_record():
    """Test the specific PluggyItem record causing 500 error"""
    item_id = '5054f6c3-153a-4450-ba2e-da6f96d269c0'
    
    print(f"🔍 Testing PluggyItem record: {item_id}")
    print("=" * 60)
    
    try:
        # 1. Basic record retrieval
        print("1️⃣ Testing basic record retrieval...")
        item = PluggyItem.objects.get(id=item_id)
        print(f"   ✅ Record found: {item}")
        
        # 2. Test basic fields access
        print("\n2️⃣ Testing basic field access...")
        print(f"   Status: {item.status}")
        print(f"   Execution Status: {item.execution_status}")
        print(f"   Pluggy Item ID: {item.pluggy_item_id}")
        
        # 3. Test foreign key relationships
        print("\n3️⃣ Testing foreign key relationships...")
        try:
            company = item.company
            print(f"   ✅ Company: {company.name if company else 'None'}")
        except Exception as e:
            print(f"   ❌ Company access error: {e}")
        
        try:
            connector = item.connector
            print(f"   ✅ Connector: {connector.name if connector else 'None'}")
        except Exception as e:
            print(f"   ❌ Connector access error: {e}")
        
        # 4. Test parameter fields
        print("\n4️⃣ Testing parameter fields...")
        try:
            print(f"   Parameter (raw): {item.parameter}")
            print(f"   Encrypted Parameter length: {len(item.encrypted_parameter) if item.encrypted_parameter else 0}")
        except Exception as e:
            print(f"   ❌ Parameter field access error: {e}")
        
        # 5. Test encryption methods
        print("\n5️⃣ Testing MFA parameter methods...")
        try:
            mfa_param = item.get_mfa_parameter()
            print(f"   ✅ get_mfa_parameter(): {type(mfa_param)} with {len(mfa_param) if isinstance(mfa_param, dict) else 0} keys")
        except Exception as e:
            print(f"   ❌ get_mfa_parameter() error: {e}")
            traceback.print_exc()
        
        # 6. Test encryption service directly
        print("\n6️⃣ Testing encryption service...")
        try:
            # Test encryption service initialization
            banking_encryption.encrypt_value("test")
            print("   ✅ Encryption service working")
        except Exception as e:
            print(f"   ❌ Encryption service error: {e}")
            traceback.print_exc()
        
        # 7. Test JSON fields
        print("\n7️⃣ Testing JSON fields...")
        try:
            print(f"   Products: {item.products}")
            print(f"   Metadata: {item.metadata}")
            print(f"   Status Detail: {item.status_detail}")
        except Exception as e:
            print(f"   ❌ JSON fields error: {e}")
        
        # 8. Test admin-specific methods
        print("\n8️⃣ Testing admin-specific functionality...")
        try:
            accounts_count = item.accounts.count()
            print(f"   ✅ Accounts count: {accounts_count}")
        except Exception as e:
            print(f"   ❌ Accounts count error: {e}")
        
        # 9. Test string representation
        print("\n9️⃣ Testing string representation...")
        try:
            str_repr = str(item)
            print(f"   ✅ String representation: {str_repr}")
        except Exception as e:
            print(f"   ❌ String representation error: {e}")
        
        print(f"\n✅ All tests completed for PluggyItem {item_id}")
        
    except PluggyItem.DoesNotExist:
        print(f"❌ PluggyItem with id {item_id} does not exist")
        return False
    except Exception as e:
        print(f"❌ Critical error accessing PluggyItem {item_id}: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_encryption_service():
    """Test the encryption service independently"""
    print("\n🔐 Testing Encryption Service")
    print("=" * 40)
    
    try:
        # Test basic encryption/decryption
        test_data = {"code": "123456", "type": "sms"}
        
        print("1️⃣ Testing basic encryption...")
        encrypted = banking_encryption.encrypt_mfa_parameter(test_data)
        print(f"   ✅ Encryption successful: {len(encrypted) if encrypted else 0} chars")
        
        print("2️⃣ Testing basic decryption...")
        decrypted = banking_encryption.decrypt_mfa_parameter(encrypted)
        print(f"   ✅ Decryption successful: {decrypted}")
        
        print("3️⃣ Testing with None values...")
        none_encrypted = banking_encryption.encrypt_mfa_parameter(None)
        print(f"   ✅ None encryption: {none_encrypted}")
        
        none_decrypted = banking_encryption.decrypt_mfa_parameter(None)
        print(f"   ✅ None decryption: {none_decrypted}")
        
        return True
    except Exception as e:
        print(f"❌ Encryption service test failed: {e}")
        traceback.print_exc()
        return False

def test_admin_view_simulation():
    """Simulate what the Django admin does when loading the change view"""
    print("\n🖥️ Simulating Django Admin Operations")
    print("=" * 45)
    
    item_id = '5054f6c3-153a-4450-ba2e-da6f96d269c0'
    
    try:
        # Simulate admin queryset with select_related
        print("1️⃣ Testing admin queryset...")
        queryset = PluggyItem.objects.select_related('company', 'connector').filter(id=item_id)
        item = queryset.first()
        
        if not item:
            print("❌ Item not found with admin queryset")
            return False
        
        print(f"   ✅ Admin queryset successful: {item}")
        
        # 2. Test admin list_display fields
        print("\n2️⃣ Testing admin list_display fields...")
        fields_to_test = [
            'pluggy_item_id',
            'company',
            'connector', 
            'status',
            'execution_status',
            'last_successful_update'
        ]
        
        for field in fields_to_test:
            try:
                value = getattr(item, field)
                print(f"   ✅ {field}: {value}")
            except Exception as e:
                print(f"   ❌ {field}: {e}")
        
        # 3. Test accounts_count custom method
        print("\n3️⃣ Testing accounts_count method...")
        try:
            count = item.accounts.count()
            print(f"   ✅ accounts_count: {count}")
        except Exception as e:
            print(f"   ❌ accounts_count: {e}")
        
        # 4. Test form field access (what happens in change view)
        print("\n4️⃣ Testing form field access...")
        form_fields = [
            'id', 'pluggy_item_id', 'company', 'connector', 'client_user_id',
            'status', 'execution_status', 'last_successful_update',
            'error_code', 'error_message', 'status_detail',
            'consent_id', 'consent_expires_at', 'metadata',
            'pluggy_created_at', 'pluggy_updated_at', 'created_at', 'updated_at'
        ]
        
        for field in form_fields:
            try:
                value = getattr(item, field)
                print(f"   ✅ {field}: OK")
            except Exception as e:
                print(f"   ❌ {field}: {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ Admin simulation failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting PluggyItem 500 Error Debug")
    print("=" * 50)
    
    # Test 1: Encryption service
    encryption_ok = test_encryption_service()
    
    # Test 2: Specific record
    record_ok = test_pluggy_item_record()
    
    # Test 3: Admin simulation
    admin_ok = test_admin_view_simulation()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print(f"Encryption Service: {'✅ OK' if encryption_ok else '❌ FAILED'}")
    print(f"Record Access: {'✅ OK' if record_ok else '❌ FAILED'}")
    print(f"Admin Simulation: {'✅ OK' if admin_ok else '❌ FAILED'}")
    
    if not (encryption_ok and record_ok and admin_ok):
        print("\n❌ Issues found - check output above for details")
        sys.exit(1)
    else:
        print("\n✅ All tests passed - issue might be environment specific")
        sys.exit(0)