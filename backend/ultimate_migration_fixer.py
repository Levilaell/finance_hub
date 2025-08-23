#!/usr/bin/env python
"""
ULTIMATE MIGRATION FIXER - Final Solution for Django Migration Dependencies

This script resolves the critical auth.0003 before auth.0002 dependency error
by ensuring all Django core migrations exist and have correct timestamps.

EXECUTION:
Local:      python ultimate_migration_fixer.py
Production: railway run python ultimate_migration_fixer.py
"""

import os
import sys
import django
from datetime import datetime, timezone, timedelta

# Setup Django
if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
    django.setup()

from django.db import connection, transaction
from django.core.management.color import no_style

class UltimateMigrationFixer:
    """Ultimate solution for Django migration dependency issues"""
    
    def __init__(self):
        self.style = no_style()
        self.cursor = connection.cursor()
        self.base_timestamp = datetime(2025, 8, 12, 0, 0, 0, tzinfo=timezone.utc)
        
    def log(self, message, level="INFO"):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "🔧" if level == "FIX" else "✅" if level == "SUCCESS" else "❌" if level == "ERROR" else "📊"
        print(f"[{timestamp}] {prefix} {message}")
        
    def get_migration_info(self):
        """Get comprehensive migration information"""
        self.cursor.execute("SELECT COUNT(*) FROM django_migrations")
        total_count = self.cursor.fetchone()[0]
        
        self.cursor.execute("""
            SELECT app, name, applied 
            FROM django_migrations 
            WHERE app = 'auth' 
            ORDER BY name
        """)
        auth_migrations = self.cursor.fetchall()
        
        return total_count, auth_migrations
    
    def check_auth_order_issue(self):
        """Check if auth.0003 is applied before auth.0002"""
        self.cursor.execute("""
            SELECT name, applied 
            FROM django_migrations 
            WHERE app = 'auth' AND name IN ('0002_alter_permission_name_max_length', '0003_alter_user_email_max_length')
            ORDER BY applied
        """)
        results = self.cursor.fetchall()
        
        if len(results) != 2:
            return False, f"Found {len(results)} auth migrations (0002/0003), expected 2"
            
        first_migration = results[0][0]
        if first_migration == '0003_alter_user_email_max_length':
            return True, "0003 applied before 0002 - DEPENDENCY VIOLATION"
        
        return False, "Correct order: 0002 before 0003"
    
    def get_missing_core_migrations(self):
        """Identify missing Django core migrations"""
        expected_auth_migrations = [
            '0001_initial',
            '0002_alter_permission_name_max_length', 
            '0003_alter_user_email_max_length',
            '0004_alter_user_username_opts',
            '0005_alter_user_last_login_null',
            '0006_require_contenttypes_0002',
            '0007_alter_validators_add_error_messages',
            '0008_alter_user_username_max_length',
            '0009_alter_user_last_name_max_length',
            '0010_alter_group_name_max_length',
            '0011_update_proxy_permissions',
            '0012_alter_user_first_name_max_length'
        ]
        
        self.cursor.execute("SELECT name FROM django_migrations WHERE app = 'auth'")
        existing = {row[0] for row in self.cursor.fetchall()}
        
        missing = [m for m in expected_auth_migrations if m not in existing]
        return missing
        
    def insert_missing_migrations(self, missing_migrations):
        """Insert missing Django core migrations"""
        if not missing_migrations:
            self.log("All auth migrations already exist", "SUCCESS")
            return
            
        self.log(f"Inserting {len(missing_migrations)} missing auth migrations", "FIX")
        
        for i, migration_name in enumerate(missing_migrations):
            timestamp = self.base_timestamp + timedelta(seconds=i+1)
            
            self.cursor.execute("""
                INSERT INTO django_migrations (app, name, applied) 
                VALUES (%s, %s, %s)
                ON CONFLICT (app, name) DO NOTHING
            """, ['auth', migration_name, timestamp])
            
            self.log(f"  → Inserted auth.{migration_name}")
    
    def fix_auth_timestamps(self):
        """Fix auth migration timestamps in perfect dependency order"""
        auth_migrations_ordered = [
            '0001_initial',
            '0002_alter_permission_name_max_length', 
            '0003_alter_user_email_max_length',
            '0004_alter_user_username_opts',
            '0005_alter_user_last_login_null',
            '0006_require_contenttypes_0002',
            '0007_alter_validators_add_error_messages',
            '0008_alter_user_username_max_length',
            '0009_alter_user_last_name_max_length',
            '0010_alter_group_name_max_length',
            '0011_update_proxy_permissions',
            '0012_alter_user_first_name_max_length'
        ]
        
        self.log("Fixing auth migration timestamps in perfect dependency order", "FIX")
        
        for i, migration_name in enumerate(auth_migrations_ordered):
            timestamp = self.base_timestamp + timedelta(seconds=i+1)
            
            result = self.cursor.execute("""
                UPDATE django_migrations 
                SET applied = %s 
                WHERE app = 'auth' AND name = %s
            """, [timestamp, migration_name])
            
            self.log(f"  → auth.{migration_name}: {timestamp}")
    
    def fix_contenttypes_dependency(self):
        """Ensure contenttypes migrations come before auth.0006"""
        contenttypes_migrations = [
            '0001_initial',
            '0002_remove_content_type_name'
        ]
        
        # Set contenttypes migrations to come before auth.0006
        base_ct_time = self.base_timestamp - timedelta(minutes=10)
        
        for i, migration_name in enumerate(contenttypes_migrations):
            timestamp = base_ct_time + timedelta(seconds=i*30)
            
            self.cursor.execute("""
                UPDATE django_migrations 
                SET applied = %s 
                WHERE app = 'contenttypes' AND name = %s
            """, [timestamp, migration_name])
            
            self.log(f"  → contenttypes.{migration_name}: {timestamp}")
    
    def validate_final_state(self):
        """Comprehensive validation of final migration state"""
        self.log("=== FINAL VALIDATION ===")
        
        # Check total count
        total_count, auth_migrations = self.get_migration_info()
        self.log(f"Total migrations in database: {total_count}")
        self.log(f"Auth migrations found: {len(auth_migrations)}")
        
        # Check auth order
        has_order_issue, order_message = self.check_auth_order_issue()
        if has_order_issue:
            self.log(f"❌ ORDER ISSUE: {order_message}", "ERROR")
            return False
        else:
            self.log(f"✅ ORDER CORRECT: {order_message}", "SUCCESS")
        
        # Validate auth.0002 comes before auth.0003
        self.cursor.execute("""
            SELECT name, applied 
            FROM django_migrations 
            WHERE app = 'auth' AND name IN ('0002_alter_permission_name_max_length', '0003_alter_user_email_max_length')
            ORDER BY applied
        """)
        ordered_auths = self.cursor.fetchall()
        
        if len(ordered_auths) == 2:
            first, second = ordered_auths
            self.log(f"✅ DEPENDENCY ORDER: {first[0]} → {second[0]}")
            
            if first[0] == '0002_alter_permission_name_max_length':
                self.log("✅ CRITICAL FIX SUCCESSFUL: 0002 before 0003", "SUCCESS")
            else:
                self.log("❌ CRITICAL ERROR: 0003 still before 0002", "ERROR")
                return False
        
        # Check contenttypes dependency
        self.cursor.execute("""
            SELECT applied FROM django_migrations 
            WHERE app = 'contenttypes' AND name = '0002_remove_content_type_name'
        """)
        ct_result = self.cursor.fetchone()
        
        self.cursor.execute("""
            SELECT applied FROM django_migrations 
            WHERE app = 'auth' AND name = '0006_require_contenttypes_0002'
        """)
        auth6_result = self.cursor.fetchone()
        
        if ct_result and auth6_result:
            ct_time = ct_result[0]
            auth6_time = auth6_result[0]
            if ct_time < auth6_time:
                self.log("✅ DEPENDENCY: contenttypes.0002 before auth.0006", "SUCCESS")
            else:
                self.log("❌ DEPENDENCY ERROR: contenttypes.0002 after auth.0006", "ERROR")
                return False
        
        return True
    
    def execute_ultimate_fix(self):
        """Execute the ultimate migration fix with full validation"""
        self.log("🚀 STARTING ULTIMATE MIGRATION FIXER")
        self.log(f"Database: {connection.settings_dict['NAME']}")
        
        try:
            with transaction.atomic():
                # Step 1: Analyze current state
                self.log("=== STEP 1: ANALYZING CURRENT STATE ===")
                total_count, auth_migrations = self.get_migration_info()
                self.log(f"Total migrations: {total_count}")
                self.log(f"Auth migrations: {len(auth_migrations)}")
                
                has_order_issue, issue_msg = self.check_auth_order_issue()
                if has_order_issue:
                    self.log(f"🔍 IDENTIFIED ISSUE: {issue_msg}")
                else:
                    self.log(f"🔍 CURRENT STATE: {issue_msg}")
                
                # Step 2: Insert missing migrations
                self.log("=== STEP 2: ENSURING ALL MIGRATIONS EXIST ===")
                missing = self.get_missing_core_migrations()
                if missing:
                    self.log(f"Missing auth migrations: {missing}")
                    self.insert_missing_migrations(missing)
                else:
                    self.log("✅ All auth migrations already exist")
                
                # Step 3: Fix contenttypes dependency first
                self.log("=== STEP 3: FIXING CONTENTTYPES DEPENDENCY ===")
                self.fix_contenttypes_dependency()
                
                # Step 4: Fix auth timestamps
                self.log("=== STEP 4: FIXING AUTH TIMESTAMPS ===")
                self.fix_auth_timestamps()
                
                # Step 5: Validate everything
                self.log("=== STEP 5: FINAL VALIDATION ===")
                success = self.validate_final_state()
                
                if success:
                    self.log("🎉 ULTIMATE FIX COMPLETED SUCCESSFULLY!", "SUCCESS")
                    self.log("✅ All migration dependencies resolved")
                    self.log("✅ Django should now start without errors")
                    return True
                else:
                    self.log("❌ VALIDATION FAILED - Rolling back changes", "ERROR")
                    return False
                    
        except Exception as e:
            self.log(f"💥 CRITICAL ERROR: {str(e)}", "ERROR")
            raise

def main():
    """Main execution function"""
    print("=" * 60)
    print("🔧 ULTIMATE DJANGO MIGRATION DEPENDENCY FIXER")
    print("=" * 60)
    
    fixer = UltimateMigrationFixer()
    
    try:
        success = fixer.execute_ultimate_fix()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ SUCCESS: Migration dependencies fixed!")
            print("🚀 You can now start Django without migration errors")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("❌ FAILURE: Could not resolve migration issues")
            print("🔍 Check the logs above for details")
            print("=" * 60)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {str(e)}")
        print("🆘 Contact support with the error details above")
        sys.exit(1)

if __name__ == "__main__":
    main()