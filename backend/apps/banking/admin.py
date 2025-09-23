"""
Banking Django Admin configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum

from .models import (
    PluggyConnector, PluggyItem, BankAccount, Transaction,
    TransactionCategory, PluggyCategory, ItemWebhook
)


@admin.register(PluggyConnector)
class PluggyConnectorAdmin(admin.ModelAdmin):
    """Admin for Pluggy connectors"""
    
    list_display = (
        'name', 'pluggy_id', 'type', 'country', 'is_open_finance',
        'is_sandbox', 'has_mfa', 'has_oauth', 'item_count'
    )
    list_filter = (
        'type', 'country', 'is_open_finance', 'is_sandbox',
        'has_mfa', 'has_oauth'
    )
    search_fields = ('name', 'pluggy_id', 'type')
    readonly_fields = (
        'pluggy_id', 'products', 'credentials', 'created_at', 'updated_at'
    )
    ordering = ['name']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'pluggy_id', 'type', 'country')
        }),
        (_('Visual'), {
            'fields': ('image_url', 'primary_color')
        }),
        (_('Capabilities'), {
            'fields': ('has_mfa', 'has_oauth', 'is_open_finance', 'is_sandbox')
        }),
        (_('Configuration'), {
            'fields': ('products', 'credentials'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('institution_url', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def item_count(self, obj):
        """Count of items using this connector"""
        count = obj.items.count()
        if count > 0:
            url = reverse('admin:banking_pluggyitem_changelist') + f'?connector__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    item_count.short_description = _('Items')
    
    actions = ['sync_selected_connectors']
    
    def sync_selected_connectors(self, request, queryset):
        """Sync selected connectors"""
        from .tasks import sync_connectors_task
        sync_connectors_task.delay()
        self.message_user(request, _('Connector sync started in background'))
    sync_selected_connectors.short_description = _('Sync selected connectors')


@admin.register(PluggyItem)
class PluggyItemAdmin(admin.ModelAdmin):
    """Admin for Pluggy items"""
    
    list_display = (
        'connector_name', 'company_name', 'status', 'execution_status',
        'account_count', 'last_successful_update', 'created_at'
    )
    list_filter = (
        'status', 'execution_status', 'connector__name',
        'created_at', 'last_successful_update'
    )
    search_fields = (
        'pluggy_item_id', 'company__name', 'connector__name',
        'client_user_id'
    )
    readonly_fields = (
        'pluggy_item_id', 'pluggy_created_at', 'pluggy_updated_at',
        'created_at', 'updated_at', 'status_detail'
    )
    raw_id_fields = ('company', 'connector')
    ordering = ['-created_at']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('company', 'connector', 'pluggy_item_id', 'client_user_id')
        }),
        (_('Status'), {
            'fields': ('status', 'execution_status', 'last_successful_update')
        }),
        (_('Configuration'), {
            'fields': ('webhook_url', 'products'),
            'classes': ('collapse',)
        }),
        (_('Error Information'), {
            'fields': ('error_code', 'error_message', 'status_detail'),
            'classes': ('collapse',)
        }),
        (_('Open Finance'), {
            'fields': ('consent_id', 'consent_expires_at'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': (
                'pluggy_created_at', 'pluggy_updated_at',
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def connector_name(self, obj):
        return obj.connector.name
    connector_name.short_description = _('Connector')
    connector_name.admin_order_field = 'connector__name'
    
    def company_name(self, obj):
        return obj.company.name
    company_name.short_description = _('Company')
    company_name.admin_order_field = 'company__name'
    
    def account_count(self, obj):
        """Count of accounts for this item"""
        count = obj.accounts.filter(is_active=True).count()
        if count > 0:
            url = reverse('admin:banking_bankaccount_changelist') + f'?item__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    account_count.short_description = _('Accounts')
    
    actions = ['sync_selected_items', 'sync_item_status']
    
    def sync_selected_items(self, request, queryset):
        """Sync selected items"""
        from .tasks import sync_item_task
        for item in queryset:
            sync_item_task.delay(str(item.id))
        self.message_user(request, f'Sync started for {queryset.count()} items')
    sync_selected_items.short_description = _('Sync selected items')
    
    def sync_item_status(self, request, queryset):
        """Sync status for selected items"""
        from .integrations.pluggy.sync_service import PluggySyncService
        sync_service = PluggySyncService()
        updated = 0
        for item in queryset:
            if sync_service.sync_item_status(item):
                updated += 1
        self.message_user(request, f'Updated status for {updated} items')
    sync_item_status.short_description = _('Update status for selected items')


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    """Admin for bank accounts"""
    
    list_display = (
        'name_or_number', 'bank_name', 'type', 'subtype',
        'balance', 'currency_code', 'is_active', 'transaction_count'
    )
    list_filter = (
        'type', 'subtype', 'currency_code', 'is_active',
        'item__connector__name', 'created_at'
    )
    search_fields = (
        'name', 'number', 'marketing_name', 'owner',
        'pluggy_account_id', 'item__company__name'
    )
    readonly_fields = (
        'pluggy_account_id', 'pluggy_created_at', 'pluggy_updated_at',
        'created_at', 'updated_at'
    )
    raw_id_fields = ('company', 'item')
    ordering = ['-balance']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('company', 'item', 'pluggy_account_id')
        }),
        (_('Account Details'), {
            'fields': (
                'type', 'subtype', 'number', 'name', 'marketing_name'
            )
        }),
        (_('Owner Information'), {
            'fields': ('owner', 'tax_number')
        }),
        (_('Balance'), {
            'fields': (
                'balance', 'balance_in_account_currency',
                'balance_date', 'currency_code'
            )
        }),
        (_('Additional Data'), {
            'fields': ('bank_data', 'credit_data'),
            'classes': ('collapse',)
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Timestamps'), {
            'fields': (
                'pluggy_created_at', 'pluggy_updated_at',
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def name_or_number(self, obj):
        return obj.name or obj.number or obj.pluggy_account_id
    name_or_number.short_description = _('Account')
    
    def bank_name(self, obj):
        return obj.item.connector.name
    bank_name.short_description = _('Bank')
    bank_name.admin_order_field = 'item__connector__name'
    
    def transaction_count(self, obj):
        """Count of transactions for this account"""
        count = obj.transactions.filter(is_deleted=False).count()
        if count > 0:
            url = reverse('admin:banking_transaction_changelist') + f'?account__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    transaction_count.short_description = _('Transactions')
    
    actions = ['sync_transactions_for_selected']
    
    def sync_transactions_for_selected(self, request, queryset):
        """Sync transactions for selected accounts"""
        from .tasks import sync_account_transactions_task
        for account in queryset:
            sync_account_transactions_task.delay(str(account.id))
        self.message_user(request, f'Transaction sync started for {queryset.count()} accounts')
    sync_transactions_for_selected.short_description = _('Sync transactions for selected accounts')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin for transactions"""
    
    list_display = (
        'description_short', 'type_display', 'amount_display',
        'date', 'account_name', 'category', 'status'
    )
    list_filter = (
        'type', 'status', 'date', 'account__item__connector__name',
        'category', 'is_deleted'
    )
    search_fields = (
        'description', 'pluggy_transaction_id',
        'account__name', 'account__number'
    )
    readonly_fields = (
        'pluggy_transaction_id', 'type', 'status', 'description',
        'amount', 'date', 'account', 'pluggy_created_at',
        'pluggy_updated_at', 'created_at', 'updated_at'
    )
    raw_id_fields = ('company', 'account', 'category')
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'company', 'account', 'pluggy_transaction_id'
            )
        }),
        (_('Transaction Details'), {
            'fields': (
                'type', 'status', 'description', 'description_raw',
                'amount', 'amount_in_account_currency', 'currency_code', 'date'
            )
        }),
        (_('Categorization'), {
            'fields': (
                'category', 'pluggy_category_id', 'pluggy_category_description'
            )
        }),
        (_('Provider Information'), {
            'fields': ('provider_code', 'provider_id')
        }),
        (_('Additional Data'), {
            'fields': (
                'operation_type', 'payment_method', 'merchant',
                'payment_data', 'credit_card_metadata'
            ),
            'classes': ('collapse',)
        }),
        (_('User Annotations'), {
            'fields': ('notes', 'tags')
        }),
        (_('Status'), {
            'fields': ('is_deleted', 'deleted_at')
        }),
        (_('Timestamps'), {
            'fields': (
                'pluggy_created_at', 'pluggy_updated_at',
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def description_short(self, obj):
        """Shortened description"""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = _('Description')
    
    def type_display(self, obj):
        """Display type with icon"""
        icon = '📈' if obj.type == 'CREDIT' else '📉'
        return f"{icon} {obj.get_type_display()}"
    type_display.short_description = _('Type')
    
    def amount_display(self, obj):
        """Display amount with formatting"""
        symbol = '+' if obj.type == 'CREDIT' else '-'
        return f"{symbol} {obj.formatted_amount}"
    amount_display.short_description = _('Amount')
    
    def account_name(self, obj):
        return obj.account.name or obj.account.number
    account_name.short_description = _('Account')
    account_name.admin_order_field = 'account__name'
    
    actions = ['categorize_transactions', 'soft_delete_selected']
    
    def categorize_transactions(self, request, queryset):
        """Auto-categorize selected transactions"""
        # TODO: Implement auto-categorization logic
        self.message_user(request, 'Auto-categorization not yet implemented')
    categorize_transactions.short_description = _('Auto-categorize selected transactions')
    
    def soft_delete_selected(self, request, queryset):
        """Soft delete selected transactions"""
        count = 0
        for transaction in queryset:
            if not transaction.is_deleted:
                transaction.soft_delete()
                count += 1
        self.message_user(request, f'Soft deleted {count} transactions')
    soft_delete_selected.short_description = _('Soft delete selected transactions')


@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    """Admin for transaction categories"""
    
    list_display = (
        'name', 'type', 'icon_display', 'color_display',
        'is_system', 'is_active', 'transaction_count', 'company'
    )
    list_filter = ('type', 'is_system', 'is_active', 'company')
    search_fields = ('name', 'slug')
    readonly_fields = ('slug', 'created_at', 'updated_at')
    raw_id_fields = ('company', 'parent')
    ordering = ['type', 'order', 'name']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('company', 'parent', 'name', 'slug', 'type')
        }),
        (_('Visual'), {
            'fields': ('icon', 'color')
        }),
        (_('Settings'), {
            'fields': ('is_system', 'is_active', 'order')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def icon_display(self, obj):
        """Display icon"""
        return obj.icon
    icon_display.short_description = _('Icon')
    
    def color_display(self, obj):
        """Display color as colored square"""
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.color
        )
    color_display.short_description = _('Color')
    
    def transaction_count(self, obj):
        """Count of transactions in this category"""
        count = obj.transactions.filter(is_deleted=False).count()
        if count > 0:
            url = reverse('admin:banking_transaction_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    transaction_count.short_description = _('Transactions')


@admin.register(PluggyCategory)
class PluggyCategoryAdmin(admin.ModelAdmin):
    """Admin for Pluggy categories"""
    
    list_display = ('id', 'description', 'parent_description', 'internal_category')
    list_filter = ('parent_description', 'internal_category')
    search_fields = ('id', 'description', 'parent_description')
    raw_id_fields = ('internal_category',)
    ordering = ['parent_description', 'description']
    
    actions = ['sync_categories']
    
    def sync_categories(self, request, queryset):
        """Sync categories from Pluggy"""
        from .tasks import sync_categories_task
        sync_categories_task.delay()
        self.message_user(request, _('Category sync started in background'))
    sync_categories.short_description = _('Sync categories from Pluggy')


@admin.register(ItemWebhook)
class ItemWebhookAdmin(admin.ModelAdmin):
    """Admin for webhook events"""
    
    list_display = (
        'event_type', 'item', 'processed', 'triggered_by',
        'created_at', 'processed_at'
    )
    list_filter = (
        'event_type', 'processed', 'triggered_by', 'created_at'
    )
    search_fields = ('event_id', 'item__pluggy_item_id', 'item__company__name')
    readonly_fields = (
        'event_id', 'payload', 'created_at', 'processed_at'
    )
    raw_id_fields = ('item',)
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        (_('Event Information'), {
            'fields': ('item', 'event_type', 'event_id', 'triggered_by')
        }),
        (_('Processing'), {
            'fields': ('processed', 'processed_at', 'error')
        }),
        (_('Data'), {
            'fields': ('payload',),
            'classes': ('collapse',)
        }),
        (_('Timestamp'), {
            'fields': ('created_at',)
        }),
    )
    
    actions = ['mark_as_processed', 'retry_processing']
    
    def mark_as_processed(self, request, queryset):
        """Mark selected webhooks as processed"""
        count = 0
        for webhook in queryset.filter(processed=False):
            webhook.mark_as_processed()
            count += 1
        self.message_user(request, f'Marked {count} webhooks as processed')
    mark_as_processed.short_description = _('Mark as processed')
    
    def retry_processing(self, request, queryset):
        """Retry processing selected webhooks"""
        from .tasks import retry_failed_webhooks
        retry_failed_webhooks.delay()
        self.message_user(request, _('Webhook retry started in background'))
    retry_processing.short_description = _('Retry processing')


# Custom admin site configuration
admin.site.site_header = 'CaixaHub Banking Administration'
admin.site.site_title = 'CaixaHub Banking Admin'
admin.site.index_title = 'Banking System Administration'