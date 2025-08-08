# Generated manually to fix database schema

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0010_add_ai_credits_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourceusage',
            name='notified_80_percent',
            field=models.BooleanField(default=False, help_text='80% usage notification sent'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='resourceusage',
            name='notified_90_percent',
            field=models.BooleanField(default=False, help_text='90% usage notification sent'),
            preserve_default=True,
        ),
    ]