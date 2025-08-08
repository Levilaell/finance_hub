# Generated manually to fix notification sync issue

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        # Add new fields with null=True first
        migrations.AddField(
            model_name='notification',
            name='event',
            field=models.CharField(
                max_length=50,
                default='sync_completed',
                db_index=True,
                help_text='The event that triggered this notification'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='notification',
            name='event_key',
            field=models.CharField(
                max_length=255,
                blank=True,
                null=True,
                help_text='Unique key for deduplication (event:id:user)'
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='is_critical',
            field=models.BooleanField(
                default=False,
                db_index=True,
                help_text='Critical notifications require immediate attention'
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='metadata',
            field=models.JSONField(
                default=dict,
                help_text='Event-specific metadata'
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='delivery_status',
            field=models.CharField(
                max_length=20,
                default='pending',
                db_index=True
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='delivered_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='retry_count',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='notification',
            name='last_retry_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]