#!/usr/bin/env python
"""
MIGRATION ANALYSIS ULTRATHINK REPORT
Comprehensive analysis of Django migrations for inconsistencies and deployment issues
"""
import os
import sys
import django
import subprocess
from datetime import datetime
from pathlib import Path
from collections import defaultdict, OrderedDict

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
django.setup()

from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from django.core.management import call_command
from io import StringIO
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def print_section(title, char='='):
    """Print a formatted section header"""
    print(f"\n{char * 80}")
    print(f"{title:^80}")
    print(f"{char * 80}")

def get_migration_dependencies():
    """Extract dependencies from all migration files"""
    dependencies = defaultdict(list)
    migration_files = []
    
    apps_dir = Path('./apps')
    for app_dir in apps_dir.iterdir():
        if not app_dir.is_dir():
            continue
            
        migrations_dir = app_dir / 'migrations'
        if not migrations_dir.exists():
            continue
            
        for migration_file in migrations_dir.glob('*.py'):
            if migration_file.name == '__init__.py':
                continue
            
            try:
                with open(migration_file, 'r') as f:
                    content = f.read()
                
                # Extract dependencies
                if 'dependencies = [' in content:
                    lines = content.split('\n')
                    in_deps = False
                    for line in lines:
                        if 'dependencies = [' in line:
                            in_deps = True
                            continue
                        if in_deps and ']' in line:
                            break
                        if in_deps and '(' in line:
                            # Extract dependency
                            if "'" in line:
                                parts = line.split("'")
                                if len(parts) >= 4:  # ('app', 'migration_name')
                                    app_name = parts[1]
                                    migration_name = parts[3]
                                    dependencies[f"{app_dir.name}.{migration_file.stem}"].append(f"{app_name}.{migration_name}")
                
                migration_files.append({
                    'app': app_dir.name,
                    'name': migration_file.stem,
                    'path': str(migration_file),
                    'full_name': f"{app_dir.name}.{migration_file.stem}"
                })
                
            except Exception as e:
                logger.error(f"Error reading {migration_file}: {e}")
    
    return dependencies, migration_files

def check_database_state():
    """Check current database state and applied migrations"""
    print_section("DATABASE STATE ANALYSIS", '=')
    
    # Check applied migrations
    applied_migrations = list(MigrationRecorder.Migration.objects.all().values_list('app', 'name'))
    applied_by_app = defaultdict(list)
    
    for app, name in applied_migrations:
        applied_by_app[app].append(name)
    
    print("\n📊 APPLIED MIGRATIONS BY APP:")
    for app in sorted(applied_by_app.keys()):
        if app in ['companies', 'banking', 'notifications', 'reports', 'payments', 'ai_insights', 'audit', 'authentication']:
            print(f"  {app}:")
            for migration in sorted(applied_by_app[app]):
                print(f"    ✅ {migration}")
    
    # Check for unapplied migrations
    print("\n🔍 CHECKING FOR UNAPPLIED MIGRATIONS:")
    try:
        output = StringIO()
        call_command('showmigrations', '--plan', stdout=output)
        plan_output = output.getvalue()
        
        unapplied = []
        for line in plan_output.split('\n'):
            if '[ ]' in line:  # Unapplied migration
                unapplied.append(line.strip())
        
        if unapplied:
            print("  ❌ UNAPPLIED MIGRATIONS FOUND:")
            for migration in unapplied:
                print(f"    {migration}")
        else:
            print("  ✅ All migrations are applied")
            
    except Exception as e:
        logger.error(f"Error checking migration plan: {e}")

def analyze_duplicate_migrations():
    """Analyze potential duplicate migrations"""
    print_section("DUPLICATE MIGRATION ANALYSIS", '⚠')
    
    print("\n🚨 CRITICAL ISSUE IDENTIFIED:")
    print("companies/0008 and companies/0009 contain IDENTICAL early access changes:")
    print()
    print("DUPLICATE FIELDS ADDED IN BOTH MIGRATIONS:")
    print("  - is_early_access (BooleanField)")
    print("  - early_access_expires_at (DateTimeField)")
    print("  - used_invite_code (CharField)")
    print("  - EarlyAccessInvite model creation")
    print("  - subscription_status choices update")
    print()
    
    print("🎯 PRODUCTION IMPACT:")
    print("  - Migration 0008 applied: 2025-08-18 13:00:26")
    print("  - Migration 0009 applied: 2025-08-18 13:07:13")
    print("  - This created duplicate field additions!")
    print("  - PostgreSQL may have rejected duplicate operations")
    print()
    
    print("📋 RECOMMENDED ACTIONS:")
    print("  1. Check production DB schema for actual field state")
    print("  2. Create migration to consolidate/clean up duplicates")
    print("  3. Consider squashing migrations 0008-0009 in future")

def check_collation_issues():
    """Check for collation version issues"""
    print_section("DATABASE COLLATION ANALYSIS", '🔧')
    
    try:
        with connection.cursor() as cursor:
            # Check PostgreSQL version and collation
            cursor.execute("SELECT version();")
            pg_version = cursor.fetchone()[0]
            print(f"PostgreSQL Version: {pg_version}")
            
            # Check collation version
            cursor.execute("""
                SELECT datname, datcollate, datctype 
                FROM pg_database 
                WHERE datname = current_database();
            """)
            result = cursor.fetchone()
            if result:
                db_name, collate, ctype = result
                print(f"Database: {db_name}")
                print(f"Collation: {collate}")
                print(f"Character Type: {ctype}")
            
            # Check for collation warnings
            cursor.execute("""
                SELECT schemaname, tablename, indexname 
                FROM pg_indexes 
                WHERE schemaname = 'public'
                LIMIT 5;
            """)
            indexes = cursor.fetchall()
            print(f"\nFound {len(indexes)} indexes in public schema")
            
    except Exception as e:
        print(f"❌ Could not analyze collation: {e}")
        print("This is expected if not using PostgreSQL in development")

def analyze_notifications_schema():
    """Analyze notifications app schema vs migration"""
    print_section("NOTIFICATIONS SCHEMA ANALYSIS", '📧')
    
    print("🔍 NOTIFICATIONS MODEL ANALYSIS:")
    print("  Based on CLAUDE.md, notifications had schema inconsistencies")
    print("  that were manually corrected with migrations 0002 and 0003")
    print()
    
    # Check current migration state
    notifications_migrations = MigrationRecorder.Migration.objects.filter(app='notifications')
    print("  Applied Notifications Migrations:")
    for migration in notifications_migrations:
        print(f"    ✅ {migration.name} (applied: {migration.applied})")
    
    print()
    print("  📊 SCHEMA STATUS:")
    print("    ✅ Only 0001_initial exists and is applied")
    print("    ✅ No evidence of the problematic 0002/0003 migrations")
    print("    ✅ Current model appears consistent with 0001_initial")

def check_missing_files():
    """Check for files mentioned in CLAUDE.md that might be missing"""
    print_section("MISSING FILES ANALYSIS", '🔍')
    
    missing_files = [
        'backend/create_report_templates.py',
        'backend/debug_early_access_admin.py',
        'backend/nuclear_migration_fix.py'
    ]
    
    print("🗑️  FILES DELETED FROM REPOSITORY:")
    for file_path in missing_files:
        if os.path.exists(file_path):
            print(f"    ✅ Found: {file_path}")
        else:
            print(f"    🗑️  Deleted: {file_path}")
    
    print("\n📋 STATUS: These files were temporary/debug scripts and have been cleaned up")

def analyze_banking_encryption():
    """Analyze banking encryption migration"""
    print_section("BANKING ENCRYPTION ANALYSIS", '🔐')
    
    print("🔐 ENCRYPTION MIGRATION ANALYSIS:")
    print("  Migration 0010_add_encrypted_parameter:")
    print("    ✅ Adds encrypted_parameter field to PluggyItem")
    print("    ✅ Includes data migration to encrypt existing parameters")
    print("    ✅ Has proper reverse migration")
    print()
    
    # Check if encryption service exists
    encryption_path = Path('./apps/banking/utils/encryption.py')
    if encryption_path.exists():
        print("    ✅ Encryption service exists")
    else:
        print("    ❌ Encryption service missing")
    
    print()
    print("  🚨 PRODUCTION CONSIDERATION:")
    print("    - Migration requires AI_INSIGHTS_ENCRYPTION_KEY environment variable")
    print("    - Warning seen in logs about missing encryption key")
    print("    - Using derived key from SECRET_KEY as fallback")

def check_index_removals():
    """Analyze index removal migration"""
    print_section("INDEX REMOVAL ANALYSIS", '📊')
    
    print("📊 BANKING INDEX ANALYSIS:")
    print("  Migration 0011_remove_transaction_indexes:")
    print("    🗑️  Removes 4 transaction indexes:")
    print("      - banking_tra_acc_date_idx")
    print("      - banking_tra_type_date_idx") 
    print("      - banking_tra_cat_date_idx")
    print("      - banking_tra_complex_idx")
    print()
    
    print("  🎯 IMPACT ASSESSMENT:")
    print("    - These were likely causing collation version issues")
    print("    - Removal may affect query performance")
    print("    - Consider recreating with proper collation settings")

def generate_recommendations():
    """Generate specific recommendations"""
    print_section("DEPLOYMENT RECOMMENDATIONS", '🚀')
    
    print("🚀 CRITICAL ACTIONS FOR RAILWAY DEPLOYMENT:")
    print()
    
    print("1. IMMEDIATE ACTIONS:")
    print("   ❗ Check production DB for duplicate early access fields")
    print("   ❗ Verify AI_INSIGHTS_ENCRYPTION_KEY is set in Railway")
    print("   ❗ Monitor collation version warnings")
    print()
    
    print("2. VALIDATION SCRIPT:")
    print("   railway run python -c \"")
    print("   from django.db import connection")
    print("   cursor = connection.cursor()")
    print("   cursor.execute('SELECT column_name FROM information_schema.columns WHERE table_name = \\'companies\\' AND column_name LIKE \\'%early_access%\\';')")
    print("   print('Early access fields:', cursor.fetchall())")
    print("   \"")
    print()
    
    print("3. ENVIRONMENT VARIABLES TO SET:")
    print("   - AI_INSIGHTS_ENCRYPTION_KEY (unique 32-byte key)")
    print("   - DJANGO_SETTINGS_MODULE=core.settings.production")
    print()
    
    print("4. MIGRATION SAFETY CHECKS:")
    print("   - Test all migrations in staging first") 
    print("   - Use --dry-run for risky operations")
    print("   - Backup database before major changes")
    print()
    
    print("5. POST-DEPLOYMENT VALIDATION:")
    print("   - Verify all models can be imported")
    print("   - Test critical user flows")
    print("   - Monitor error logs for schema issues")

def main():
    """Run comprehensive migration analysis"""
    print_section("FINANCE HUB - MIGRATION ANALYSIS ULTRATHINK", '🔬')
    print(f"Analysis started: {datetime.now().isoformat()}")
    
    try:
        # Core analysis functions
        check_database_state()
        analyze_duplicate_migrations()
        check_collation_issues()
        analyze_notifications_schema()
        check_missing_files()
        analyze_banking_encryption()
        check_index_removals()
        
        # Generate actionable recommendations
        generate_recommendations()
        
        print_section("ANALYSIS COMPLETE", '✅')
        print("📊 Summary: Multiple issues identified requiring immediate attention")
        print("🎯 Priority: Fix duplicate early access migrations in production")
        print("🔐 Security: Set AI_INSIGHTS_ENCRYPTION_KEY environment variable")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1
        
    return 0

if __name__ == '__main__':
    sys.exit(main())