# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0011_allow_null_optional_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankaccount',
            name='bank_data',
            field=models.JSONField(blank=True, default=dict, null=True, verbose_name='bank data'),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='credit_data',
            field=models.JSONField(blank=True, default=dict, null=True, verbose_name='credit data'),
        ),
    ]