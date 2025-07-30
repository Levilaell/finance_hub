# Generated manually for Pluggy webhook validation documentation

from django.db import migrations


class Migration(migrations.Migration):
    """
    This migration documents the need for PLUGGY_WEBHOOK_SECRET setting.
    
    Add to your environment variables:
    PLUGGY_WEBHOOK_SECRET=your-webhook-secret-from-pluggy
    
    This secret is used to validate webhook signatures using HMAC-SHA256.
    """

    dependencies = [
        ('banking', '0019_auto_20240101_0000'),  # Update this to your latest migration
    ]

    operations = [
        # No database changes, just documentation
    ]