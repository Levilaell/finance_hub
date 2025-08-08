# Generated migration to simplify Company model
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0003_consolidate_subscriptions'),
    ]

    operations = [
        # This migration is no longer needed as the model already matches the database schema
        # The fields have already been removed and SubscriptionPlan already has created_at/updated_at
        # Marking as a no-op migration to maintain migration history consistency
    ]