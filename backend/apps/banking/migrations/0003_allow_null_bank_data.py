# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0002_change_transaction_date_to_datetime'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankaccount',
            name='bank_data',
            field=models.JSONField(blank=True, default=dict, help_text='Additional bank-specific data'),
        ),
    ]