#!/usr/bin/env python
"""
FIX DUPLICATE EARLY ACCESS MIGRATIONS
Consolidate companies/0008 and companies/0009 duplicate migrations
"""
import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
django.setup()

from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from django.core.management import call_command

def analyze_duplicate_problem():
    """Analyze the duplicate migration problem"""
    print("🔍 ANALYZING DUPLICATE MIGRATION PROBLEM")
    print("=" * 50)
    
    # Check which migrations are applied
    applied_migrations = MigrationRecorder.Migration.objects.filter(
        app='companies',
        name__in=['0008_alter_resourceusage_options_and_more', '0009_add_early_access']
    ).order_by('applied')
    
    print("Applied migrations:")
    for migration in applied_migrations:
        print(f"  - {migration.name} (applied: {migration.applied})")
    
    # Check current schema state
    with connection.cursor() as cursor:
        # Check early access fields
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'companies' 
            AND column_name IN ('is_early_access', 'early_access_expires_at', 'used_invite_code')
            ORDER BY column_name;
        """)
        fields = cursor.fetchall()
        
        print(f"\nCurrent early access fields in DB: {len(fields)}")
        for field in fields:
            print(f"  - {field[0]}: {field[1]} (nullable: {field[2]})")
        
        # Check EarlyAccessInvite table
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'early_access_invites'
            );
        """)
        table_exists = cursor.fetchone()[0]
        print(f"\nEarlyAccessInvite table exists: {table_exists}")
        
        if table_exists:
            cursor.execute("""
                SELECT count(*) FROM early_access_invites;
            """)
            count = cursor.fetchone()[0]
            print(f"Records in early_access_invites: {count}")

def create_consolidated_migration():
    """Create a consolidated migration to fix the duplicate issue"""
    print("\n🛠️ CREATING CONSOLIDATED MIGRATION")
    print("=" * 50)
    
    migration_content = '''# Consolidated migration to fix duplicate early access migrations
# This replaces the functionality of both 0008 and 0009

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('companies', '0007_add_stripe_price_ids'),
    ]

    operations = [
        # ResourceUsage model improvements
        migrations.AlterModelOptions(
            name='resourceusage',
            options={'ordering': ['-month']},
        ),
        migrations.AddField(
            model_name='resourceusage',
            name='notified_80_percent',
            field=models.BooleanField(default=False, help_text='80% usage notification sent'),
        ),
        migrations.AddField(
            model_name='resourceusage',
            name='notified_90_percent',
            field=models.BooleanField(default=False, help_text='90% usage notification sent'),
        ),
        migrations.AlterField(
            model_name='resourceusage',
            name='ai_requests_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='resourceusage',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usage_history', to='companies.company'),
        ),
        migrations.AlterField(
            model_name='resourceusage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='resourceusage',
            name='month',
            field=models.DateField(help_text='First day of the month'),
        ),
        migrations.AlterField(
            model_name='resourceusage',
            name='reports_generated',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='resourceusage',
            name='transactions_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='resourceusage',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Early Access functionality - consolidated from both migrations
        migrations.AddField(
            model_name='company',
            name='is_early_access',
            field=models.BooleanField(default=False, verbose_name='is early access'),
        ),
        migrations.AddField(
            model_name='company',
            name='early_access_expires_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='early access expires at'),
        ),
        migrations.AddField(
            model_name='company',
            name='used_invite_code',
            field=models.CharField(blank=True, max_length=20, verbose_name='used invite code'),
        ),
        
        # Update subscription_status choices to include early_access
        migrations.AlterField(
            model_name='company',
            name='subscription_status',
            field=models.CharField(
                choices=[
                    ('trial', 'Trial'),
                    ('active', 'Active'),
                    ('cancelled', 'Cancelled'),
                    ('expired', 'Expired'),
                    ('early_access', 'Early Access'),
                ],
                default='trial',
                max_length=20,
                verbose_name='status'
            ),
        ),
        
        # Create EarlyAccessInvite model
        migrations.CreateModel(
            name='EarlyAccessInvite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invite_code', models.CharField(max_length=20, unique=True, verbose_name='invite code')),
                ('expires_at', models.DateTimeField(help_text='Date when early access ends', verbose_name='expires at')),
                ('is_used', models.BooleanField(default=False, verbose_name='is used')),
                ('used_at', models.DateTimeField(blank=True, null=True, verbose_name='used at')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('notes', models.TextField(blank=True, help_text='Internal notes about this invite', verbose_name='notes')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_invites', to=settings.AUTH_USER_MODEL)),
                ('used_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='used_invite', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Early Access Invite',
                'verbose_name_plural': 'Early Access Invites',
                'db_table': 'early_access_invites',
                'ordering': ['-created_at'],
            },
        ),
    ]
'''
    
    # Save the consolidated migration (for reference)
    consolidated_path = 'apps/companies/migrations/0008_consolidated_early_access.py.template'
    with open(consolidated_path, 'w') as f:
        f.write(migration_content)
    
    print(f"✅ Consolidated migration template saved: {consolidated_path}")
    print("   This shows what a proper consolidated migration would look like")

def generate_production_fix():
    """Generate production fix script"""
    print("\n🔧 GENERATING PRODUCTION FIX SCRIPT")
    print("=" * 50)
    
    fix_script = '''-- PRODUCTION FIX FOR DUPLICATE EARLY ACCESS MIGRATIONS
-- This script handles the case where both 0008 and 0009 were applied

BEGIN;

-- Step 1: Verify current state
DO $$
DECLARE
    field_count INTEGER;
    table_exists BOOLEAN;
BEGIN
    -- Check how many early access fields exist
    SELECT COUNT(*) INTO field_count
    FROM information_schema.columns 
    WHERE table_name = 'companies' 
    AND column_name IN ('is_early_access', 'early_access_expires_at', 'used_invite_code');
    
    -- Check if early_access_invites table exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'early_access_invites'
    ) INTO table_exists;
    
    RAISE NOTICE 'Early access fields found: %', field_count;
    RAISE NOTICE 'Early access table exists: %', table_exists;
    
    -- If fields are missing, this indicates PostgreSQL rejected the duplicate operations
    IF field_count < 3 THEN
        RAISE NOTICE 'Adding missing early access fields...';
        
        -- Add missing fields
        ALTER TABLE companies ADD COLUMN IF NOT EXISTS is_early_access BOOLEAN DEFAULT FALSE;
        ALTER TABLE companies ADD COLUMN IF NOT EXISTS early_access_expires_at TIMESTAMPTZ NULL;
        ALTER TABLE companies ADD COLUMN IF NOT EXISTS used_invite_code VARCHAR(20) DEFAULT '';
        
        -- Update subscription_status choices
        -- Note: This requires Django to handle the choices validation
        
        RAISE NOTICE 'Early access fields added successfully';
    ELSE
        RAISE NOTICE 'All early access fields already exist';
    END IF;
    
    -- Create table if it doesn't exist
    IF NOT table_exists THEN
        RAISE NOTICE 'Creating early_access_invites table...';
        
        CREATE TABLE early_access_invites (
            id BIGSERIAL PRIMARY KEY,
            invite_code VARCHAR(20) UNIQUE NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            is_used BOOLEAN DEFAULT FALSE,
            used_at TIMESTAMPTZ NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            notes TEXT DEFAULT '',
            created_by_id BIGINT REFERENCES auth_user(id) ON DELETE CASCADE,
            used_by_id BIGINT REFERENCES auth_user(id) ON DELETE SET NULL
        );
        
        RAISE NOTICE 'early_access_invites table created successfully';
    ELSE
        RAISE NOTICE 'early_access_invites table already exists';
    END IF;
    
END $$;

-- Step 2: Verify the fix
SELECT 'companies_early_access_fields' as validation,
       COUNT(*) as field_count
FROM information_schema.columns 
WHERE table_name = 'companies' 
AND column_name IN ('is_early_access', 'early_access_expires_at', 'used_invite_code')

UNION ALL

SELECT 'early_access_invites_table' as validation,
       COUNT(*) as table_count
FROM information_schema.tables 
WHERE table_name = 'early_access_invites';

COMMIT;

-- Final verification queries
\\echo '=== VERIFICATION ==='
\\echo 'Early access fields in companies table:'
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'companies' 
AND column_name IN ('is_early_access', 'early_access_expires_at', 'used_invite_code')
ORDER BY column_name;

\\echo 'Early access invites table structure:'
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'early_access_invites'
ORDER BY ordinal_position;'''
    
    # Save the fix script
    fix_script_path = 'fix_duplicate_early_access_production.sql'
    with open(fix_script_path, 'w') as f:
        f.write(fix_script)
    
    print(f"✅ Production fix script saved: {fix_script_path}")
    print("   Run this in Railway console if early access fields are missing")

def recommend_future_prevention():
    """Recommend steps to prevent this in the future"""
    print("\n📋 FUTURE PREVENTION RECOMMENDATIONS")
    print("=" * 50)
    
    recommendations = [
        "1. MIGRATION REVIEW PROCESS:",
        "   - Always review migration content before applying",
        "   - Check for duplicate operations across migrations",
        "   - Use 'makemigrations --dry-run' to preview changes",
        "",
        "2. SQUASH DUPLICATE MIGRATIONS:",
        "   - Consider squashing 0008 and 0009 into single migration",
        "   - Use 'squashmigrations companies 0008 0009'",
        "   - Test squashed migration in development first",
        "",
        "3. STAGING ENVIRONMENT:",
        "   - Always test migrations in staging before production",
        "   - Use identical database setup to production",
        "   - Verify migration rollback procedures",
        "",
        "4. AUTOMATED CHECKS:",
        "   - Add migration linting to CI/CD pipeline",
        "   - Check for duplicate field additions",
        "   - Validate migration dependencies",
        "",
        "5. DOCUMENTATION:",
        "   - Document all manual schema changes",
        "   - Keep migration notes for complex operations",
        "   - Track production schema drift"
    ]
    
    for rec in recommendations:
        print(rec)

def main():
    """Main execution"""
    print("🔧 DUPLICATE MIGRATION FIX UTILITY")
    print("=" * 60)
    print(f"Analysis started: {datetime.now().isoformat()}")
    
    try:
        analyze_duplicate_problem()
        create_consolidated_migration()
        generate_production_fix()
        recommend_future_prevention()
        
        print("\n✅ ANALYSIS AND FIX GENERATION COMPLETE")
        print("=" * 60)
        print("Next steps:")
        print("1. Review generated fix_duplicate_early_access_production.sql")
        print("2. Test the fix script in staging environment")
        print("3. Apply fix in Railway production if validation fails")
        print("4. Consider squashing migrations 0008-0009 for clean state")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return 1
        
    return 0

if __name__ == '__main__':
    sys.exit(main())