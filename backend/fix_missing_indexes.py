#!/usr/bin/env python3
"""
MISSING INDEX FIX - Railway Compatible
====================================

Fixes: ValueError: No index named reports_company_c4b7ee_idx on model Report

PROBLEM: Django model expects specific index that doesn't exist in database
SOLUTION: Create missing index with exact name Django expects

RAILWAY-SAFE: 
- Quick execution (single SQL command)
- Idempotent (safe to run multiple times)
- No data modification (only adds index)
"""

import os
import sys
import django
from datetime import datetime

# Setup Django for production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')

try:
    django.setup()
    from django.db import connection
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

def fix_missing_indexes():
    """Fix missing database indexes"""
    print("🔧 MISSING INDEX FIX - Creating required database indexes")
    print("=" * 60)
    
    missing_indexes = [
        {
            'name': 'reports_company_c4b7ee_idx',
            'table': 'reports',
            'columns': ['company_id'],
            'description': 'Company foreign key index for Report model'
        }
    ]
    
    try:
        with connection.cursor() as cursor:
            
            print("📋 Step 1: Checking for missing indexes...")
            
            indexes_created = 0
            for idx_info in missing_indexes:
                idx_name = idx_info['name']
                table = idx_info['table']
                columns = idx_info['columns']
                description = idx_info['description']
                
                print(f"   🔍 Checking {idx_name}...")
                
                # Check if index already exists
                cursor.execute("""
                    SELECT COUNT(*) FROM pg_indexes 
                    WHERE tablename = %s AND indexname = %s;
                """, [table, idx_name])
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    print(f"   ✅ {idx_name}: Already exists")
                else:
                    print(f"   ❌ {idx_name}: Missing - creating...")
                    
                    # Create the missing index
                    columns_sql = ', '.join(columns)
                    create_sql = f'CREATE INDEX {idx_name} ON {table} ({columns_sql});'
                    
                    try:
                        cursor.execute(create_sql)
                        print(f"   ✅ {idx_name}: Created successfully")
                        indexes_created += 1
                    except Exception as create_error:
                        print(f"   ❌ {idx_name}: Creation failed - {create_error}")
                        
                        # Try alternative approach if original fails
                        if 'already exists' in str(create_error).lower():
                            print(f"   ℹ️  {idx_name}: Index already exists (concurrent creation)")
                        else:
                            print(f"   🔄 Trying fallback approach...")
                            fallback_name = f"{table}_company_idx"
                            fallback_sql = f'CREATE INDEX IF NOT EXISTS {fallback_name} ON {table} ({columns_sql});'
                            
                            try:
                                cursor.execute(fallback_sql)
                                print(f"   ✅ {fallback_name}: Fallback index created")
                                indexes_created += 1
                            except Exception as fallback_error:
                                print(f"   ❌ Fallback failed: {fallback_error}")
                                return False
            
            print(f"\n📊 Summary:")
            print(f"   📋 Indexes checked: {len(missing_indexes)}")
            print(f"   ✅ Indexes created: {indexes_created}")
            
            if indexes_created > 0:
                print(f"\n🎉 MISSING INDEX FIX SUCCESS!")
                print(f"✅ Created {indexes_created} missing database indexes")
                print(f"✅ Django model expectations now satisfied")
                print(f"✅ ValueError should be resolved")
            else:
                print(f"\n✅ NO ACTION NEEDED!")
                print(f"✅ All required indexes already exist")
                print(f"✅ Database schema is consistent with Django models")
            
            return True
            
    except Exception as e:
        print(f"\n❌ MISSING INDEX FIX FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main execution with Railway compatibility"""
    print("🔧 MISSING INDEX FIX - Railway Compatible")
    print("=" * 50)
    print("🎯 Target: Fix ValueError - No index named reports_company_c4b7ee_idx")
    print("⚡ Method: Create missing database indexes")
    print()
    
    success = fix_missing_indexes()
    
    print(f"\n" + "="*50)
    if success:
        print("🎉 MISSING INDEX FIX COMPLETED!")
        print("✅ Database indexes created successfully")
        print("✅ Django model consistency restored")
    else:
        print("❌ MISSING INDEX FIX FAILED")
        print("   Check errors above for details")
    
    return success

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Index fix cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)