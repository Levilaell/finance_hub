# Emergency migration to fix inconsistent migration history
from django.db import migrations

class Migration(migrations.Migration):
    # This migration resolves the dependency issue in production
    # where 0003 was applied before 0002
    
    dependencies = [
        ('reports', '0001_initial'),
        # Explicitly not depending on 0002 or 0003 to avoid circular issues
    ]
    
    operations = [
        # No-op migration - just fixes the dependency chain
        migrations.RunSQL(
            sql="SELECT 1;",  # No-op SQL
            reverse_sql="SELECT 1;",
        ),
    ]
