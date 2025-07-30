# Generated manually to fix nullable fields issue

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0003_alter_transaction_merchant'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='description_raw',
            field=models.TextField(
                blank=True,
                null=True,  # Allow NULL values
                verbose_name='description raw'
            ),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='payment_data',
            field=models.JSONField(
                default=dict,
                blank=True,
                null=True,  # Allow NULL values
                verbose_name='payment data'
            ),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='credit_card_metadata',
            field=models.JSONField(
                default=dict,
                blank=True,
                null=True,  # Allow NULL values
                verbose_name='credit card metadata'
            ),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='tags',
            field=models.JSONField(
                default=list,
                blank=True,
                null=True,  # Allow NULL values
                verbose_name='tags'
            ),
        ),
    ]