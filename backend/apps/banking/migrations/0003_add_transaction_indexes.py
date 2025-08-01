# Generated migration for adding performance indexes to Transaction model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0002_bankaccount_balance_in_account_currency_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['bank_account', 'transaction_date'], name='banking_tra_bank_ac_date_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['transaction_type', 'transaction_date'], name='banking_tra_type_date_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['category', 'transaction_date'], name='banking_tra_cat_date_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['bank_account', 'transaction_type', '-transaction_date'], name='banking_tra_acc_type_date_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['counterpart_name', 'transaction_date'], name='banking_tra_counter_date_idx'),
        ),
    ]