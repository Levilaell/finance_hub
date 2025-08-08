# Generated migration for new payment models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial'),
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubscriptionPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('starter', 'Starter'), ('professional', 'Professional'), ('enterprise', 'Enterprise')], max_length=50, unique=True)),
                ('display_name', models.CharField(max_length=100)),
                ('price_monthly', models.DecimalField(decimal_places=2, max_digits=10)),
                ('price_yearly', models.DecimalField(decimal_places=2, max_digits=10)),
                ('max_transactions', models.IntegerField()),
                ('max_bank_accounts', models.IntegerField()),
                ('max_ai_requests', models.IntegerField()),
                ('features', models.JSONField(default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['price_monthly'],
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('trial', 'Trial'), ('active', 'Active'), ('cancelled', 'Cancelled'), ('expired', 'Expired'), ('past_due', 'Past Due')], default='trial', max_length=20)),
                ('billing_period', models.CharField(choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')], default='monthly', max_length=10)),
                ('stripe_subscription_id', models.CharField(blank=True, max_length=255, null=True)),
                ('stripe_customer_id', models.CharField(blank=True, max_length=255, null=True)),
                ('mercadopago_subscription_id', models.CharField(blank=True, max_length=255, null=True)),
                ('trial_ends_at', models.DateTimeField(blank=True, null=True)),
                ('current_period_start', models.DateTimeField(blank=True, null=True)),
                ('current_period_end', models.DateTimeField(blank=True, null=True)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to='companies.company')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='payments.subscriptionplan')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('card', 'Credit/Debit Card'), ('bank_account', 'Bank Account'), ('pix', 'PIX')], max_length=20)),
                ('is_default', models.BooleanField(default=False)),
                ('stripe_payment_method_id', models.CharField(blank=True, max_length=255, null=True)),
                ('mercadopago_card_id', models.CharField(blank=True, max_length=255, null=True)),
                ('brand', models.CharField(blank=True, max_length=50)),
                ('last4', models.CharField(blank=True, max_length=4)),
                ('exp_month', models.IntegerField(blank=True, null=True)),
                ('exp_year', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_methods', to='companies.company')),
            ],
            options={
                'ordering': ['-is_default', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='BRL', max_length=3)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('succeeded', 'Succeeded'), ('failed', 'Failed'), ('cancelled', 'Cancelled'), ('refunded', 'Refunded')], max_length=20)),
                ('description', models.CharField(max_length=255)),
                ('stripe_payment_intent_id', models.CharField(blank=True, max_length=255, null=True)),
                ('stripe_invoice_id', models.CharField(blank=True, max_length=255, null=True)),
                ('mercadopago_payment_id', models.CharField(blank=True, max_length=255, null=True)),
                ('gateway', models.CharField(max_length=20)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='companies.company')),
                ('payment_method', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='payments.paymentmethod')),
                ('subscription', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='payments.subscription')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='UsageRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('transaction', 'Transaction'), ('bank_account', 'Bank Account'), ('ai_request', 'AI Request')], max_length=20)),
                ('count', models.IntegerField(default=0)),
                ('period_start', models.DateTimeField()),
                ('period_end', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usage_records', to='companies.company')),
            ],
            options={
                'ordering': ['-period_start'],
                'unique_together': {('company', 'type', 'period_start')},
            },
        ),
    ]