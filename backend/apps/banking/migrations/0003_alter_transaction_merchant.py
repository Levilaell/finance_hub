# Generated manually to fix merchant field nullable issue

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0002_bankaccount_balance_in_account_currency_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='merchant',
            field=models.JSONField(
                default=dict,
                blank=True,
                null=True,  # Allow NULL values
                verbose_name='merchant'
            ),
        ),
    ]