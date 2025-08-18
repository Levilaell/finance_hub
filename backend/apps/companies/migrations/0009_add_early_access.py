# Generated manually for early access functionality

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('companies', '0008_alter_resourceusage_options_and_more'),
    ]

    operations = [
        # Add early access fields to Company model
        migrations.AddField(
            model_name='company',
            name='is_early_access',
            field=models.BooleanField(default=False, verbose_name='is early access'),
        ),
        migrations.AddField(
            model_name='company',
            name='early_access_expires_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='early access expires at'),
        ),
        migrations.AddField(
            model_name='company',
            name='used_invite_code',
            field=models.CharField(blank=True, max_length=20, verbose_name='used invite code'),
        ),
        
        # Update subscription_status choices to include early_access
        migrations.AlterField(
            model_name='company',
            name='subscription_status',
            field=models.CharField(
                choices=[
                    ('trial', 'Trial'),
                    ('active', 'Active'),
                    ('cancelled', 'Cancelled'),
                    ('expired', 'Expired'),
                    ('early_access', 'Early Access'),
                ],
                default='trial',
                max_length=20,
                verbose_name='status'
            ),
        ),
        
        # Create EarlyAccessInvite model
        migrations.CreateModel(
            name='EarlyAccessInvite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invite_code', models.CharField(max_length=20, unique=True, verbose_name='invite code')),
                ('expires_at', models.DateTimeField(help_text='Date when early access ends', verbose_name='expires at')),
                ('is_used', models.BooleanField(default=False, verbose_name='is used')),
                ('used_at', models.DateTimeField(blank=True, null=True, verbose_name='used at')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('notes', models.TextField(blank=True, help_text='Internal notes about this invite', verbose_name='notes')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_invites', to=settings.AUTH_USER_MODEL)),
                ('used_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='used_invite', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Early Access Invite',
                'verbose_name_plural': 'Early Access Invites',
                'db_table': 'early_access_invites',
                'ordering': ['-created_at'],
            },
        ),
    ]