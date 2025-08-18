# Merge migration to fix dependencies

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0010_add_ai_credits_balance'),
    ]

    operations = [
    ]