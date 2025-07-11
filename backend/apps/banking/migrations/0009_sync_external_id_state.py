# Generated to sync Django migration state with database

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0008_fix_field_state'),
    ]

    operations = [
        # Tell Django that external_account_id has been renamed to external_id
        # This was already done in migration 0007 using raw SQL
        migrations.RenameField(
            model_name='bankaccount',
            old_name='external_account_id',
            new_name='external_id',
        ),
    ]