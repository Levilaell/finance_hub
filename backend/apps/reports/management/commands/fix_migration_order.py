"""
ULTRA-DEEP ANALYSIS: Fix reports migration dependency issue
Problem: reports.0003 applied before its dependency reports.0002
Solution: Remove 0003 from django_migrations, allow correct order reapplication
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.migrations.recorder import MigrationRecorder
import sys


class Command(BaseCommand):
    help = 'Fix reports migration dependency issue by resetting migration order'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("🔍 ULTRA-DEEP ANALYSIS: Reports Migration Order Fix")
        self.stdout.write("=" * 60)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No changes will be made"))
        
        try:
            with transaction.atomic():
                recorder = MigrationRecorder(connection)
                
                # STEP 1: Check current state
                self.stdout.write("📊 STEP 1: Checking current migration state...")
                
                applied_migrations = list(
                    recorder.migration_qs.filter(app='reports').order_by('applied')
                )
                
                self.stdout.write(f"Found {len(applied_migrations)} reports migrations:")
                for migration in applied_migrations:
                    self.stdout.write(f"  ✓ {migration.app}.{migration.name} (applied: {migration.applied})")
                
                # Check if 0003 exists (the problematic one)
                problematic_migration = None
                dependency_migration = None
                
                for migration in applied_migrations:
                    if migration.name == '0003_aianalysistemplate_aianalysis':
                        problematic_migration = migration
                    elif migration.name == '0002_alter_aianalysis_options_and_more':
                        dependency_migration = migration
                
                if not problematic_migration:
                    self.stdout.write(self.style.ERROR("❌ Migration 0003 not found in applied migrations"))
                    self.stdout.write("The issue may already be resolved or different than expected")
                    return
                
                if dependency_migration:
                    self.stdout.write(self.style.ERROR("❌ Migration 0002 already applied"))
                    self.stdout.write("This indicates the dependency issue may be resolved")
                    self.stdout.write("Run 'python manage.py migrate reports' to verify")
                    return
                
                # STEP 2: Remove problematic migration
                self.stdout.write("\n🔧 STEP 2: Removing problematic migration 0003...")
                
                if dry_run:
                    self.stdout.write(self.style.WARNING("Would delete: reports.0003_aianalysistemplate_aianalysis"))
                else:
                    problematic_migration.delete()
                    self.stdout.write(self.style.SUCCESS("✅ Removed migration record"))
                
                # STEP 3: Verify what remains
                self.stdout.write("\n✅ STEP 3: Checking remaining migrations...")
                
                if not dry_run:
                    remaining_migrations = list(
                        recorder.migration_qs.filter(app='reports').order_by('applied')
                    )
                    self.stdout.write(f"Remaining {len(remaining_migrations)} reports migrations:")
                    for migration in remaining_migrations:
                        self.stdout.write(f"  ✓ {migration.app}.{migration.name} (applied: {migration.applied})")
                
                # STEP 4: Instructions
                self.stdout.write("\n🎯 NEXT STEPS:")
                self.stdout.write("1. Run: python manage.py migrate reports")
                self.stdout.write("2. This will apply 0002 first, then 0003 in correct order")
                self.stdout.write("3. Verify with: python manage.py showmigrations reports")
                
                if dry_run:
                    self.stdout.write(self.style.WARNING("\n🔍 DRY RUN COMPLETED - No actual changes made"))
                    self.stdout.write("Run without --dry-run to apply the fix")
                else:
                    self.stdout.write(self.style.SUCCESS("\n✅ Migration order fix completed successfully!"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n💥 ERROR: {e}"))
            import traceback
            traceback.print_exc()
            sys.exit(1)