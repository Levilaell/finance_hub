# Placeholder migration for dependency resolution
# This migration serves as a bridge between the initial migration and the encrypted fields migration

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ai_insights', '0001_initial'),
    ]

    operations = [
        # No operations - this is a placeholder migration to fix dependency chain
        # The actual encrypted fields migration is in 0003_add_encrypted_fields
    ]