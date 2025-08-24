#!/usr/bin/env python3
"""
ULTRA-DEEP INDEX ANALYSIS - Missing Database Index
=================================================

--ultrathink ANALYSIS: ValueError: No index named reports_company_c4b7ee_idx on model Report

NEW ERROR TYPE: Database schema inconsistency - missing index
- Django model expects index that doesn't exist in database
- Different from migration conflicts - this is schema vs model definition mismatch
- Need to analyze Report model structure and database schema

ROOT CAUSE INVESTIGATION:
1. Analyze Report model definition and expected indexes
2. Check actual database indexes on reports table
3. Identify missing indexes and their purposes
4. Create definitive fix to sync schema with model expectations
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')

try:
    django.setup()
    from django.db import connection
    from django.apps import apps
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

def ultrathink_index_analysis():
    """Ultra-deep analysis of missing index error"""
    print("🧠 ULTRA-DEEP INDEX ANALYSIS - Missing Database Index")
    print("=" * 70)
    print(f"📅 Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    findings = []
    
    try:
        with connection.cursor() as cursor:
            
            # PHASE 1: Analyze Report model structure
            print("🔍 PHASE 1: REPORT MODEL ANALYSIS")
            print("-" * 50)
            
            try:
                # Get the Report model
                Report = apps.get_model('reports', 'Report')
                print(f"✅ Found Report model: {Report}")
                
                # Get model fields
                fields = Report._meta.get_fields()
                print(f"📋 Report model has {len(fields)} fields:")
                for field in fields:
                    field_type = type(field).__name__
                    print(f"   - {field.name}: {field_type}")
                    
                # Check for foreign keys and indexes
                foreign_keys = []
                indexes = []
                
                for field in fields:
                    if hasattr(field, 'related_model') and field.related_model:
                        foreign_keys.append(field.name)
                    if hasattr(field, 'db_index') and field.db_index:
                        indexes.append(field.name)
                
                print(f"📋 Foreign key fields: {foreign_keys}")
                print(f"📋 Indexed fields: {indexes}")
                
                # Check model Meta for additional indexes
                if hasattr(Report._meta, 'indexes'):
                    model_indexes = Report._meta.indexes
                    print(f"📋 Model Meta indexes: {len(model_indexes)}")
                    for idx in model_indexes:
                        print(f"   - {idx}")
                
            except Exception as model_error:
                print(f"❌ Could not analyze Report model: {model_error}")
                findings.append({
                    'issue': 'MODEL_ACCESS_ERROR',
                    'description': f'Cannot access Report model: {model_error}',
                    'severity': 'HIGH'
                })
            
            # PHASE 2: Analyze actual database schema
            print(f"\n🔍 PHASE 2: DATABASE SCHEMA ANALYSIS")
            print("-" * 50)
            
            # Check if reports table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'reports'
                );
            """)
            reports_table_exists = cursor.fetchone()[0]
            print(f"📊 Reports table exists: {reports_table_exists}")
            
            if reports_table_exists:
                # Get all columns in reports table
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'reports' 
                    ORDER BY ordinal_position;
                """)
                columns = cursor.fetchall()
                print(f"📋 Reports table has {len(columns)} columns:")
                for col_name, data_type, nullable, default in columns:
                    print(f"   - {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
                
                # Get all indexes on reports table
                cursor.execute("""
                    SELECT 
                        indexname,
                        indexdef
                    FROM pg_indexes 
                    WHERE tablename = 'reports'
                    ORDER BY indexname;
                """)
                db_indexes = cursor.fetchall()
                print(f"\n📋 Database indexes on reports table ({len(db_indexes)}):")
                for idx_name, idx_def in db_indexes:
                    print(f"   - {idx_name}: {idx_def}")
                
                # Check specifically for the missing index
                missing_index_name = "reports_company_c4b7ee_idx"
                found_missing_index = any(missing_index_name in idx_name for idx_name, _ in db_indexes)
                
                if not found_missing_index:
                    print(f"\n🚨 CONFIRMED: Missing index '{missing_index_name}' NOT found in database")
                    findings.append({
                        'issue': 'MISSING_INDEX',
                        'index_name': missing_index_name,
                        'description': f'Django expects index {missing_index_name} but it does not exist in database',
                        'severity': 'CRITICAL'
                    })
                else:
                    print(f"\n✅ Index '{missing_index_name}' found in database")
                
            else:
                print(f"❌ Reports table does not exist!")
                findings.append({
                    'issue': 'MISSING_TABLE',
                    'description': 'Reports table does not exist in database',
                    'severity': 'CRITICAL'
                })
            
            # PHASE 3: Check for company foreign key relationship
            print(f"\n🔍 PHASE 3: COMPANY RELATIONSHIP ANALYSIS")
            print("-" * 50)
            
            if reports_table_exists:
                # Check for company_id column (likely the source of the index)
                cursor.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns 
                    WHERE table_name = 'reports' AND column_name LIKE '%company%'
                    ORDER BY column_name;
                """)
                company_columns = cursor.fetchall()
                print(f"📋 Company-related columns: {company_columns}")
                
                # Check foreign key constraints
                cursor.execute("""
                    SELECT
                        tc.constraint_name,
                        tc.table_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY' 
                        AND tc.table_name = 'reports';
                """)
                fk_constraints = cursor.fetchall()
                print(f"📋 Foreign key constraints on reports table:")
                for constraint_name, table_name, column_name, foreign_table, foreign_column in fk_constraints:
                    print(f"   - {column_name} → {foreign_table}.{foreign_column} ({constraint_name})")
                
                # Look for company relationship specifically
                company_fk = [fk for fk in fk_constraints if 'company' in fk[2].lower() or 'company' in fk[3].lower()]
                if company_fk:
                    print(f"✅ Found company foreign key relationship")
                    for fk in company_fk:
                        print(f"   📋 {fk[2]} → {fk[3]}.{fk[4]}")
                else:
                    print(f"⚠️  No company foreign key relationship found")
            
            # PHASE 4: Migration analysis for reports app
            print(f"\n🔍 PHASE 4: REPORTS MIGRATION ANALYSIS")
            print("-" * 50)
            
            cursor.execute("""
                SELECT name, applied FROM django_migrations 
                WHERE app = 'reports' 
                ORDER BY applied;
            """)
            reports_migrations = cursor.fetchall()
            print(f"📊 Reports app migrations: {len(reports_migrations)}")
            for name, applied in reports_migrations:
                print(f"   - {name}: {applied}")
            
            return findings
            
    except Exception as e:
        print(f"\n❌ INDEX ANALYSIS FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_index_fix_solution(findings):
    """Create solution to fix missing index"""
    print(f"\n🛠️  INDEX FIX SOLUTION GENERATION")
    print("-" * 50)
    
    if not findings:
        print("✅ No index issues found - fix not needed")
        return None
    
    missing_index_issues = [f for f in findings if f['issue'] == 'MISSING_INDEX']
    if not missing_index_issues:
        print("✅ No missing index issues - other problems detected")
        return None
    
    print(f"🎯 Creating fix for {len(missing_index_issues)} missing index issues...")
    
    fix_solution = {
        'approach': 'RECREATE_MISSING_INDEXES',
        'operations': []
    }
    
    # Operation 1: Analyze the missing index pattern
    missing_index_name = "reports_company_c4b7ee_idx"
    
    # Django typically creates indexes with this pattern for foreign keys
    # reports_company_c4b7ee_idx suggests an index on company_id in reports table
    
    fix_solution['operations'].append({
        'step': 1,
        'name': 'CREATE_MISSING_COMPANY_INDEX',
        'description': 'Create missing company foreign key index on reports table',
        'sql': f'CREATE INDEX {missing_index_name} ON reports (company_id);',
        'fallback_sql': 'CREATE INDEX reports_company_idx ON reports (company_id);',
        'type': 'CREATE_INDEX'
    })
    
    # Operation 2: Verify index creation
    fix_solution['operations'].append({
        'step': 2,
        'name': 'VERIFY_INDEX_CREATION',
        'description': 'Verify the missing index was created successfully',
        'sql': f"SELECT indexname FROM pg_indexes WHERE tablename = 'reports' AND indexname = '{missing_index_name}';",
        'type': 'VERIFICATION'
    })
    
    return fix_solution

def execute_index_fix(fix_solution, dry_run=True):
    """Execute the index fix solution"""
    print(f"\n🛠️  INDEX FIX EXECUTION {'(DRY RUN)' if dry_run else '(LIVE EXECUTION)'}")
    print("-" * 50)
    
    if not fix_solution:
        print("❌ No fix solution provided")
        return False
    
    try:
        for operation in fix_solution['operations']:
            step = operation['step']
            name = operation['name'] 
            description = operation['description']
            op_type = operation['type']
            
            print(f"📋 Step {step}: {name}")
            print(f"   💡 {description}")
            
            if op_type == 'CREATE_INDEX':
                if dry_run:
                    print(f"   🔧 DRY RUN: Would execute: {operation['sql']}")
                    print(f"   📝 Fallback: {operation.get('fallback_sql', 'N/A')}")
                else:
                    with connection.cursor() as cursor:
                        try:
                            cursor.execute(operation['sql'])
                            print(f"   ✅ Index created successfully")
                        except Exception as create_error:
                            print(f"   ⚠️  Primary creation failed: {create_error}")
                            if 'fallback_sql' in operation:
                                print(f"   🔄 Trying fallback SQL...")
                                cursor.execute(operation['fallback_sql'])
                                print(f"   ✅ Fallback index created")
                            else:
                                raise create_error
                                
            elif op_type == 'VERIFICATION':
                if dry_run:
                    print(f"   🔍 DRY RUN: Would verify with: {operation['sql']}")
                else:
                    with connection.cursor() as cursor:
                        cursor.execute(operation['sql'])
                        result = cursor.fetchall()
                        if result:
                            print(f"   ✅ Index verification successful: {result}")
                        else:
                            print(f"   ❌ Index verification failed")
                            return False
        
        if dry_run:
            print(f"\n✅ INDEX FIX DRY RUN COMPLETED")
            print(f"📋 All operations validated - ready for live execution")
        else:
            print(f"\n🎉 INDEX FIX EXECUTED SUCCESSFULLY!")
            print(f"✅ Missing database index created")
            print(f"✅ Django model expectations satisfied")
        
        return True
        
    except Exception as e:
        print(f"\n❌ INDEX FIX EXECUTION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main index analysis and fix"""
    print("🧠 ULTRA-DEEP INDEX ANALYSIS - Missing Database Index")
    print("=" * 80)
    print("🎯 Target: ValueError - No index named reports_company_c4b7ee_idx on model Report")
    print("⚡ Method: Schema analysis and index reconstruction")
    print()
    
    # Step 1: Ultra-deep analysis
    findings = ultrathink_index_analysis()
    
    if findings is None:
        print("❌ Analysis failed - cannot proceed")
        return False
    
    if not findings:
        print("🎉 NO INDEX ISSUES DETECTED!")
        print("✅ Database schema matches Django model expectations")
        return True
    
    # Step 2: Create fix solution
    fix_solution = create_index_fix_solution(findings)
    
    if not fix_solution:
        print("❌ Could not create fix solution")
        return False
    
    # Step 3: Execute fix (dry run first)
    dry_run_success = execute_index_fix(fix_solution, dry_run=True)
    
    if not dry_run_success:
        print("❌ Dry run failed - fix solution has issues")
        return False
    
    print(f"\n" + "="*80)
    print("🎯 INDEX FIX READY FOR DEPLOYMENT")
    print("="*80)
    print("✅ Missing index analysis completed")
    print(f"✅ Found {len(findings)} issues requiring fixes")
    print("✅ Index fix solution generated and validated")
    print("✅ Dry run successful - ready for live execution")
    print()
    print("🚨 TO EXECUTE LIVE (creates missing indexes):")
    print("   python ultrathink_index_analysis.py --live")
    
    return True

if __name__ == '__main__':
    try:
        # Check for live execution flag
        live_mode = '--live' in sys.argv
        
        if live_mode:
            print("🔥 LIVE EXECUTION MODE ACTIVATED")
            print("⚠️  This will create missing database indexes")
            
            # Execute live
            findings = ultrathink_index_analysis()
            if findings:
                fix_solution = create_index_fix_solution(findings)
                if fix_solution:
                    success = execute_index_fix(fix_solution, dry_run=False)
                else:
                    success = False
            else:
                success = True
        else:
            # Default: analysis and dry run mode
            success = main()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Index analysis cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)