# Generated manually to add PaymentAuditLog model

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('companies', '0009_add_early_access'),
        ('payments', '0002_alter_subscription_plan_paymentretry_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[
                    ('subscription_created', 'Subscription Created'),
                    ('subscription_activated', 'Subscription Activated'),
                    ('subscription_cancelled', 'Subscription Cancelled'),
                    ('subscription_expired', 'Subscription Expired'),
                    ('subscription_plan_changed', 'Subscription Plan Changed'),
                    ('payment_initiated', 'Payment Initiated'),
                    ('payment_succeeded', 'Payment Succeeded'),
                    ('payment_failed', 'Payment Failed'),
                    ('payment_validated', 'Payment Validated'),
                    ('payment_refunded', 'Payment Refunded'),
                    ('payment_disputed', 'Payment Disputed'),
                    ('payment_method_added', 'Payment Method Added'),
                    ('payment_method_updated', 'Payment Method Updated'),
                    ('payment_method_removed', 'Payment Method Removed'),
                    ('invoice_created', 'Invoice Created'),
                    ('invoice_paid', 'Invoice Paid'),
                    ('invoice_failed', 'Invoice Failed'),
                    ('trial_started', 'Trial Started'),
                    ('trial_ended', 'Trial Ended'),
                    ('trial_extended', 'Trial Extended'),
                    ('webhook_received', 'Webhook Received'),
                    ('webhook_processed', 'Webhook Processed'),
                    ('webhook_failed', 'Webhook Failed'),
                    ('security_alert', 'Security Alert'),
                    ('fraud_detected', 'Fraud Detected'),
                    ('compliance_check', 'Compliance Check'),
                    ('data_export', 'Data Export'),
                    ('data_deletion', 'Data Deletion'),
                    ('admin_action', 'Admin Action'),
                    ('api_call', 'API Call'),
                    ('rate_limit_exceeded', 'Rate Limit Exceeded'),
                    ('system_error', 'System Error'),
                    ('maintenance_mode', 'Maintenance Mode')
                ], max_length=50, verbose_name='action')),
                ('severity', models.CharField(choices=[
                    ('low', 'Low'),
                    ('medium', 'Medium'),
                    ('high', 'High'),
                    ('critical', 'Critical')
                ], default='medium', max_length=20, verbose_name='severity')),
                ('status', models.CharField(choices=[
                    ('success', 'Success'),
                    ('failed', 'Failed'),
                    ('pending', 'Pending'),
                    ('cancelled', 'Cancelled'),
                    ('timeout', 'Timeout')
                ], max_length=20, verbose_name='status')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP address')),
                ('user_agent', models.TextField(blank=True, verbose_name='user agent')),
                ('request_id', models.CharField(blank=True, max_length=100, verbose_name='request ID')),
                ('session_id', models.CharField(blank=True, max_length=100, verbose_name='session ID')),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='amount')),
                ('currency', models.CharField(blank=True, max_length=3, verbose_name='currency')),
                ('payment_method', models.CharField(blank=True, max_length=50, verbose_name='payment method')),
                ('gateway_response', models.JSONField(blank=True, default=dict, verbose_name='gateway response')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='metadata')),
                ('error_code', models.CharField(blank=True, max_length=50, verbose_name='error code')),
                ('error_message', models.TextField(blank=True, verbose_name='error message')),
                ('processing_time', models.IntegerField(blank=True, null=True, verbose_name='processing time (ms)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='payment_audit_logs', to='companies.company', verbose_name='company')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payment_audit_logs', to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'verbose_name': 'Payment Audit Log',
                'verbose_name_plural': 'Payment Audit Logs',
                'db_table': 'payments_paymentauditlog',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['action', 'created_at'], name='payments_paymentauditlog_action_created_at_idx'),
                    models.Index(fields=['company', 'created_at'], name='payments_paymentauditlog_company_created_at_idx'),
                    models.Index(fields=['user', 'created_at'], name='payments_paymentauditlog_user_created_at_idx'),
                    models.Index(fields=['severity'], name='payments_paymentauditlog_severity_idx'),
                    models.Index(fields=['status'], name='payments_paymentauditlog_status_idx'),
                    models.Index(fields=['session_id'], name='payments_paymentauditlog_session_id_idx'),
                    models.Index(fields=['request_id'], name='payments_paymentauditlog_request_id_idx'),
                ],
            },
        ),
    ]