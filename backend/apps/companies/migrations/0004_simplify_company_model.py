# Generated migration to simplify Company model
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0003_consolidate_subscriptions'),
    ]

    operations = [
        # Remove unused fields from Company model to match current models.py
        # Note: trade_name field kept as it's now in the current model
        migrations.RemoveField(
            model_name='company',
            name='cnpj',
        ),
        migrations.RemoveField(
            model_name='company',
            name='company_type',
        ),
        migrations.RemoveField(
            model_name='company',
            name='business_sector',
        ),
        migrations.RemoveField(
            model_name='company',
            name='email',
        ),
        migrations.RemoveField(
            model_name='company',
            name='phone',
        ),
        migrations.RemoveField(
            model_name='company',
            name='website',
        ),
        migrations.RemoveField(
            model_name='company',
            name='address_street',
        ),
        migrations.RemoveField(
            model_name='company',
            name='address_number',
        ),
        migrations.RemoveField(
            model_name='company',
            name='address_complement',
        ),
        migrations.RemoveField(
            model_name='company',
            name='address_neighborhood',
        ),
        migrations.RemoveField(
            model_name='company',
            name='address_city',
        ),
        migrations.RemoveField(
            model_name='company',
            name='address_state',
        ),
        migrations.RemoveField(
            model_name='company',
            name='address_zipcode',
        ),
        migrations.RemoveField(
            model_name='company',
            name='monthly_revenue',
        ),
        migrations.RemoveField(
            model_name='company',
            name='employee_count',
        ),
        migrations.RemoveField(
            model_name='company',
            name='next_billing_date',
        ),
        migrations.RemoveField(
            model_name='company',
            name='subscription_start_date',
        ),
        migrations.RemoveField(
            model_name='company',
            name='subscription_end_date',
        ),
        migrations.RemoveField(
            model_name='company',
            name='last_usage_reset',
        ),
        migrations.RemoveField(
            model_name='company',
            name='notified_80_percent',
        ),
        migrations.RemoveField(
            model_name='company',
            name='notified_90_percent',
        ),
        migrations.RemoveField(
            model_name='company',
            name='logo',
        ),
        migrations.RemoveField(
            model_name='company',
            name='primary_color',
        ),
        migrations.RemoveField(
            model_name='company',
            name='currency',
        ),
        migrations.RemoveField(
            model_name='company',
            name='fiscal_year_start',
        ),
        migrations.RemoveField(
            model_name='company',
            name='enable_ai_categorization',
        ),
        migrations.RemoveField(
            model_name='company',
            name='auto_categorize_threshold',
        ),
        migrations.RemoveField(
            model_name='company',
            name='enable_notifications',
        ),
        migrations.RemoveField(
            model_name='company',
            name='enable_email_reports',
        ),
        migrations.RemoveField(
            model_name='company',
            name='updated_at',
        ),
        # Add missing created_at and updated_at fields to SubscriptionPlan
        migrations.AddField(
            model_name='subscriptionplan',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]