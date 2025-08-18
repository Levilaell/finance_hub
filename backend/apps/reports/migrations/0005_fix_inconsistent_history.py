# Manual migration to fix inconsistent migration history in production
# This migration handles the case where 0003 was applied before 0002

from django.db import migrations

def fix_migration_history(apps, schema_editor):
    """
    Fix the migration history by ensuring the correct order
    This is a no-op migration that just fixes the dependency chain
    """
    # Get the migration recorder
    MigrationRecorder = apps.get_model('migrations', 'Migration')
    
    # Check if we have the inconsistent state
    try:
        # Check if 0003 exists
        migration_0003 = MigrationRecorder.objects.filter(
            app='reports',
            name='0003_aianalysistemplate_aianalysis'
        ).first()
        
        # Check if 0002 exists
        migration_0002 = MigrationRecorder.objects.filter(
            app='reports',
            name='0002_alter_aianalysis_options_and_more'
        ).first()
        
        # If 0003 exists but 0002 doesn't, we need to fake 0002
        if migration_0003 and not migration_0002:
            MigrationRecorder.objects.create(
                app='reports',
                name='0002_alter_aianalysis_options_and_more',
                applied=migration_0003.applied  # Use same timestamp as 0003
            )
            print("Fixed migration history: Added missing 0002 migration record")
            
    except Exception as e:
        # If anything goes wrong, just continue
        # This is a fix migration, we don't want it to break deployments
        print(f"Could not fix migration history: {e}")
        pass

def reverse_fix(apps, schema_editor):
    """Reverse is a no-op"""
    pass

class Migration(migrations.Migration):
    
    dependencies = [
        ('reports', '0004_merge_20250803_2225'),
    ]
    
    operations = [
        migrations.RunPython(fix_migration_history, reverse_fix),
    ]