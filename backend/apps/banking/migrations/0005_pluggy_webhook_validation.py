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
        ('banking', '0004_alter_transaction_fields'),
    ]

    operations = [
        # No database changes, just documentation
    ]