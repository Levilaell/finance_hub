# Generated manually on 2025-10-03
# Add credit card fields to BankAccount model

from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0007_rename_banking_tra_pluggy__c44c0e_idx_banking_tra_pluggy__05816c_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bankaccount',
            name='available_credit_limit',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=None,
                max_digits=15,
                null=True,
                help_text='Available credit limit for credit cards'
            ),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='credit_limit',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=None,
                max_digits=15,
                null=True,
                help_text='Total credit limit for credit cards'
            ),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='credit_data',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Additional credit card data from Pluggy'
            ),
        ),
    ]
