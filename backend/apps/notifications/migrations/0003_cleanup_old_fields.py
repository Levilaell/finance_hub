# Generated manually to cleanup old fields from notifications table

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_add_event_key'),
    ]

    operations = [
        # Remove old fields that are no longer in the model
        migrations.RemoveField(
            model_name='notification',
            name='notification_type',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='data',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='priority',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='email_sent',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='email_sent_at',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='push_sent',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='push_sent_at',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='sms_sent',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='sms_sent_at',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='expires_at',
        ),
        # Alter action_url to match new model (max_length 500, blank=True)
        migrations.AlterField(
            model_name='notification',
            name='action_url',
            field=models.URLField(
                max_length=500,
                blank=True,
                verbose_name='action URL',
                help_text='URL for user action'
            ),
        ),
    ]