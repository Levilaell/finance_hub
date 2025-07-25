# Generated manually for Pluggy integration

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0008_bankprovider_is_open_finance'),
        ('companies', '0008_company_companies_subscri_f72d81_idx_and_more'),
    ]

    operations = [
        # Create new models
        migrations.CreateModel(
            name='PluggyConnector',
            fields=[
                ('pluggy_id', models.IntegerField(primary_key=True, serialize=False, unique=True, verbose_name='Pluggy ID')),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('institution_url', models.URLField(blank=True, verbose_name='institution URL')),
                ('image_url', models.URLField(blank=True, verbose_name='image URL')),
                ('primary_color', models.CharField(default='#000000', max_length=7, verbose_name='primary color')),
                ('type', models.CharField(max_length=50, verbose_name='type')),
                ('country', models.CharField(default='BR', max_length=2, verbose_name='country')),
                ('has_mfa', models.BooleanField(default=False, verbose_name='has MFA')),
                ('has_oauth', models.BooleanField(default=False, verbose_name='has OAuth')),
                ('is_open_finance', models.BooleanField(default=False, verbose_name='is Open Finance')),
                ('is_sandbox', models.BooleanField(default=False, verbose_name='is sandbox')),
                ('products', models.JSONField(default=list, verbose_name='supported products')),
                ('credentials', models.JSONField(default=list, verbose_name='credentials schema')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
            ],
            options={
                'verbose_name': 'Pluggy Connector',
                'verbose_name_plural': 'Pluggy Connectors',
                'db_table': 'pluggy_connectors',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PluggyItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('pluggy_id', models.CharField(db_index=True, max_length=100, unique=True, verbose_name='Pluggy Item ID')),
                ('client_user_id', models.CharField(blank=True, max_length=100, verbose_name='client user ID')),
                ('status', models.CharField(choices=[('LOGIN_IN_PROGRESS', 'Login in Progress'), ('WAITING_USER_INPUT', 'Waiting User Input'), ('UPDATING', 'Updating'), ('UPDATED', 'Updated'), ('LOGIN_ERROR', 'Login Error'), ('OUTDATED', 'Outdated'), ('ERROR', 'Error')], default='CREATED', max_length=30, verbose_name='status')),
                ('execution_status', models.CharField(blank=True, choices=[('CREATED', 'Created'), ('SUCCESS', 'Success'), ('PARTIAL_SUCCESS', 'Partial Success'), ('LOGIN_ERROR', 'Login Error'), ('INVALID_CREDENTIALS', 'Invalid Credentials'), ('USER_INPUT_TIMEOUT', 'User Input Timeout'), ('USER_AUTHORIZATION_PENDING', 'User Authorization Pending'), ('USER_AUTHORIZATION_NOT_GRANTED', 'User Authorization Not Granted'), ('SITE_NOT_AVAILABLE', 'Site Not Available'), ('ERROR', 'Error')], max_length=50, verbose_name='execution status')),
                ('created_at', models.DateTimeField(verbose_name='created at')),
                ('updated_at', models.DateTimeField(verbose_name='updated at')),
                ('last_successful_update', models.DateTimeField(blank=True, null=True, verbose_name='last successful update')),
                ('error_code', models.CharField(blank=True, max_length=50, verbose_name='error code')),
                ('error_message', models.TextField(blank=True, verbose_name='error message')),
                ('status_detail', models.JSONField(blank=True, default=dict, verbose_name='status detail')),
                ('consent_id', models.CharField(blank=True, max_length=100, verbose_name='consent ID')),
                ('consent_expires_at', models.DateTimeField(blank=True, null=True, verbose_name='consent expires at')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='metadata')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pluggy_items', to='companies.company')),
                ('connector', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='items', to='banking.pluggyconnector')),
            ],
            options={
                'verbose_name': 'Pluggy Item',
                'verbose_name_plural': 'Pluggy Items',
                'db_table': 'pluggy_items',
                'indexes': [models.Index(fields=['company', 'status'], name='pluggy_item_company_06c7ff_idx'), models.Index(fields=['pluggy_id'], name='pluggy_item_pluggy__d5b22e_idx'), models.Index(fields=['last_successful_update'], name='pluggy_item_last_su_8e5a65_idx')],
            },
        ),
        migrations.CreateModel(
            name='TransactionCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('slug', models.SlugField(unique=True, verbose_name='slug')),
                ('type', models.CharField(choices=[('income', 'Income'), ('expense', 'Expense'), ('transfer', 'Transfer'), ('both', 'Both')], max_length=20, verbose_name='type')),
                ('icon', models.CharField(default='📁', max_length=50, verbose_name='icon')),
                ('color', models.CharField(default='#6B7280', max_length=7, verbose_name='color')),
                ('is_system', models.BooleanField(default=False, verbose_name='is system category')),
                ('is_active', models.BooleanField(default=True, verbose_name='is active')),
                ('order', models.IntegerField(default=0, verbose_name='order')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='transaction_categories', to='companies.company')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subcategories', to='banking.transactioncategory')),
            ],
            options={
                'verbose_name': 'Transaction Category',
                'verbose_name_plural': 'Transaction Categories',
                'db_table': 'transaction_categories_v2',
                'ordering': ['type', 'order', 'name'],
                'unique_together': {('company', 'slug')},
            },
        ),
        migrations.CreateModel(
            name='PluggyCategory',
            fields=[
                ('id', models.CharField(max_length=100, primary_key=True, serialize=False, verbose_name='category ID')),
                ('description', models.CharField(max_length=200, verbose_name='description')),
                ('parent_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='parent ID')),
                ('parent_description', models.CharField(blank=True, max_length=200, verbose_name='parent description')),
                ('internal_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pluggy_mappings', to='banking.transactioncategory')),
            ],
            options={
                'verbose_name': 'Pluggy Category',
                'verbose_name_plural': 'Pluggy Categories',
                'db_table': 'pluggy_categories',
                'ordering': ['parent_description', 'description'],
            },
        ),
        migrations.CreateModel(
            name='ItemWebhook',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event_type', models.CharField(choices=[('item.created', 'Item Created'), ('item.updated', 'Item Updated'), ('item.error', 'Item Error'), ('item.deleted', 'Item Deleted'), ('item.login_succeeded', 'Login Succeeded'), ('item.waiting_user_input', 'Waiting User Input'), ('transactions.created', 'Transactions Created'), ('transactions.updated', 'Transactions Updated'), ('transactions.deleted', 'Transactions Deleted'), ('consent.created', 'Consent Created'), ('consent.updated', 'Consent Updated'), ('consent.revoked', 'Consent Revoked')], max_length=50, verbose_name='event type')),
                ('event_id', models.CharField(max_length=100, unique=True, verbose_name='event ID')),
                ('payload', models.JSONField(verbose_name='payload')),
                ('processed', models.BooleanField(default=False, verbose_name='processed')),
                ('processed_at', models.DateTimeField(blank=True, null=True, verbose_name='processed at')),
                ('error', models.TextField(blank=True, verbose_name='error')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='webhooks', to='banking.pluggyitem')),
            ],
            options={
                'verbose_name': 'Item Webhook',
                'verbose_name_plural': 'Item Webhooks',
                'db_table': 'item_webhooks',
                'ordering': ['-created'],
                'indexes': [models.Index(fields=['item', 'event_type'], name='item_webhoo_item_id_fef4d6_idx'), models.Index(fields=['processed', 'created'], name='item_webhoo_process_2f8c59_idx'), models.Index(fields=['event_id'], name='item_webhoo_event_i_2e8baa_idx')],
            },
        ),
        
        # Rename existing models/fields
        migrations.RenameModel(
            old_name='BankAccount',
            new_name='BankAccountOld',
        ),
        
        # Create new BankAccount model
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('pluggy_id', models.CharField(db_index=True, max_length=100, unique=True, verbose_name='Pluggy Account ID')),
                ('type', models.CharField(choices=[('BANK', 'Bank Account'), ('CREDIT', 'Credit Card'), ('INVESTMENT', 'Investment'), ('LOAN', 'Loan'), ('OTHER', 'Other')], max_length=20, verbose_name='type')),
                ('subtype', models.CharField(blank=True, choices=[('CHECKING_ACCOUNT', 'Checking Account'), ('SAVINGS_ACCOUNT', 'Savings Account'), ('CREDIT_CARD', 'Credit Card'), ('PREPAID_CARD', 'Prepaid Card'), ('INVESTMENT_ACCOUNT', 'Investment Account'), ('LOAN_ACCOUNT', 'Loan Account'), ('OTHER', 'Other')], max_length=30, verbose_name='subtype')),
                ('number', models.CharField(blank=True, max_length=50, verbose_name='number')),
                ('name', models.CharField(blank=True, max_length=200, verbose_name='name')),
                ('marketing_name', models.CharField(blank=True, max_length=200, verbose_name='marketing name')),
                ('owner', models.CharField(blank=True, max_length=200, verbose_name='owner')),
                ('tax_number', models.CharField(blank=True, max_length=20, verbose_name='tax number')),
                ('balance', models.DecimalField(decimal_places=2, default=0.00, max_digits=15, verbose_name='balance')),
                ('balance_date', models.DateTimeField(blank=True, null=True, verbose_name='balance date')),
                ('currency_code', models.CharField(default='BRL', max_length=3, verbose_name='currency code')),
                ('bank_data', models.JSONField(blank=True, default=dict, verbose_name='bank data')),
                ('credit_data', models.JSONField(blank=True, default=dict, verbose_name='credit data')),
                ('is_active', models.BooleanField(default=True, verbose_name='is active')),
                ('created_at', models.DateTimeField(verbose_name='created at')),
                ('updated_at', models.DateTimeField(verbose_name='updated at')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bank_accounts_v2', to='companies.company')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accounts', to='banking.pluggyitem')),
            ],
            options={
                'verbose_name': 'Bank Account',
                'verbose_name_plural': 'Bank Accounts',
                'db_table': 'bank_accounts_v2',
                'unique_together': {('company', 'pluggy_id')},
                'indexes': [models.Index(fields=['company', 'is_active'], name='bank_accoun_company_4e5fa2_idx'), models.Index(fields=['item', 'type'], name='bank_accoun_item_id_b7b9c3_idx'), models.Index(fields=['pluggy_id'], name='bank_accoun_pluggy__0e6e87_idx')],
            },
        ),
        
        # Rename existing Transaction model
        migrations.RenameModel(
            old_name='Transaction',
            new_name='TransactionOld',
        ),
        
        # Create new Transaction model
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('pluggy_id', models.CharField(db_index=True, max_length=100, unique=True, verbose_name='Pluggy Transaction ID')),
                ('type', models.CharField(choices=[('DEBIT', 'Debit'), ('CREDIT', 'Credit')], max_length=10, verbose_name='type')),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('POSTED', 'Posted')], default='POSTED', max_length=10, verbose_name='status')),
                ('description', models.CharField(max_length=500, verbose_name='description')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='amount')),
                ('currency_code', models.CharField(default='BRL', max_length=3, verbose_name='currency code')),
                ('date', models.DateTimeField(verbose_name='transaction date')),
                ('merchant', models.JSONField(blank=True, default=dict, verbose_name='merchant')),
                ('payment_data', models.JSONField(blank=True, default=dict, verbose_name='payment data')),
                ('pluggy_category_id', models.CharField(blank=True, max_length=100, verbose_name='Pluggy category ID')),
                ('pluggy_category_description', models.CharField(blank=True, max_length=200, verbose_name='Pluggy category')),
                ('operation_type', models.CharField(blank=True, max_length=50, verbose_name='operation type')),
                ('payment_method', models.CharField(blank=True, max_length=50, verbose_name='payment method')),
                ('credit_card_metadata', models.JSONField(blank=True, default=dict, verbose_name='credit card metadata')),
                ('notes', models.TextField(blank=True, verbose_name='notes')),
                ('tags', models.JSONField(default=list, verbose_name='tags')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='metadata')),
                ('created_at', models.DateTimeField(verbose_name='created at')),
                ('updated_at', models.DateTimeField(verbose_name='updated at')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='banking.bankaccount')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions_v2', to='banking.transactioncategory')),
            ],
            options={
                'verbose_name': 'Transaction',
                'verbose_name_plural': 'Transactions',
                'db_table': 'transactions_v2',
                'ordering': ['-date', '-created_at'],
                'indexes': [models.Index(fields=['account', 'date'], name='transaction_account_25e589_idx'), models.Index(fields=['pluggy_id'], name='transaction_pluggy__1e5c65_idx'), models.Index(fields=['date', 'type'], name='transaction_date_d5ad25_idx'), models.Index(fields=['pluggy_category_id'], name='transaction_pluggy__0e8b2e_idx'), models.Index(fields=['category', 'date'], name='transaction_categor_9f5c48_idx')],
            },
        ),
    ]