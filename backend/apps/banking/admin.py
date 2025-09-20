"""
Django Admin configuration for banking and financial transaction models
Pluggy Integration management interface
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import (
    PluggyConnector,
    PluggyItem,
    BankAccount,
    PluggyCategory,
    Transaction,
    TransactionCategory,
    ItemWebhook
)


@admin.register(PluggyConnector)
class PluggyConnectorAdmin(admin.ModelAdmin):
    """Admin interface for Pluggy Connectors"""
    list_display = (
        'name',
        'pluggy_id',
        'type',
        'country',
        'is_open_finance',
        'is_sandbox',
        'has_mfa',
        'created_at'
    )
    list_filter = (
        'type',
        'country',
        'is_open_finance',
        'is_sandbox',
        'has_mfa',
        'has_oauth'
    )
    search_fields = ('name', 'pluggy_id', 'institution_url')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ['name']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('pluggy_id', 'name', 'institution_url', 'image_url', 'primary_color')
        }),
        (_('Classification'), {
            'fields': ('type', 'country')
        }),
        (_('Features'), {
            'fields': ('has_mfa', 'has_oauth', 'is_open_finance', 'is_sandbox')
        }),
        (_('Products & Credentials'), {
            'fields': ('products', 'credentials'),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': ('id', 'created_at', 'updated_at'),
        }),
    )


@admin.register(PluggyItem)
class PluggyItemAdmin(admin.ModelAdmin):
    """Admin interface for Pluggy Items (connections)"""
    list_display = (
        'display_name',
        'company',
        'connector',
        'status',
        'execution_status',
        'last_successful_update',
        'created_at'
    )
    list_filter = (
        'status',
        'execution_status',
        'connector',
        'created_at',
        'last_successful_update'
    )
    search_fields = (
        'pluggy_item_id',
        'company__name',
        'connector__name',
        'client_user_id'
    )
    readonly_fields = (
        'id',
        'pluggy_item_id',
        'pluggy_created_at',
        'pluggy_updated_at',
        'created_at',
        'updated_at'
    )
    raw_id_fields = ('company', 'connector')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Connection Info'), {
            'fields': ('pluggy_item_id', 'company', 'connector', 'client_user_id')
        }),
        (_('Status'), {
            'fields': ('status', 'execution_status', 'last_successful_update')
        }),
        (_('Configuration'), {
            'fields': ('products', 'webhook_url')
        }),
        (_('Error Tracking'), {
            'fields': ('error_code', 'error_message'),
            'classes': ('collapse',)
        }),
        (_('Open Finance Consent'), {
            'fields': ('consent_id', 'consent_expires_at'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('status_detail', 'metadata'),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': ('id', 'pluggy_created_at', 'pluggy_updated_at', 'created_at', 'updated_at'),
        }),
    )
    
    def display_name(self, obj):
        return str(obj)
    display_name.short_description = _('Item')


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    """Admin interface for Bank Accounts"""
    list_display = (
        'display_name',
        'company',
        'type',
        'subtype',
        'balance_formatted',
        'currency_code',
        'is_active',
        'balance_date'
    )
    list_filter = (
        'type',
        'subtype',
        'is_active',
        'currency_code',
        'created_at'
    )
    search_fields = (
        'name',
        'marketing_name',
        'number',
        'owner',
        'company__name',
        'pluggy_account_id'
    )
    readonly_fields = (
        'id',
        'pluggy_account_id',
        'masked_number',
        'pluggy_created_at',
        'pluggy_updated_at',
        'created_at',
        'updated_at'
    )
    raw_id_fields = ('item', 'company')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Account Information'), {
            'fields': (
                'pluggy_account_id',
                'item',
                'company',
                'type',
                'subtype',
                'name',
                'marketing_name',
                'number',
                'masked_number'
            )
        }),
        (_('Owner Information'), {
            'fields': ('owner', 'tax_number')
        }),
        (_('Balance'), {
            'fields': (
                'balance',
                'balance_in_account_currency',
                'currency_code',
                'balance_date'
            )
        }),
        (_('Additional Data'), {
            'fields': ('bank_data', 'credit_data'),
            'classes': ('collapse',)
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('System Info'), {
            'fields': ('id', 'pluggy_created_at', 'pluggy_updated_at', 'created_at', 'updated_at'),
        }),
    )
    
    def balance_formatted(self, obj):
        return f"{obj.currency_code} {obj.balance:,.2f}"
    balance_formatted.short_description = _('Balance')


@admin.register(PluggyCategory)
class PluggyCategoryAdmin(admin.ModelAdmin):
    """Admin interface for Pluggy Categories"""
    list_display = ('id', 'description', 'parent_description', 'internal_category')
    list_filter = ('parent_description',)
    search_fields = ('id', 'description', 'parent_description')
    raw_id_fields = ('internal_category',)
    ordering = ['parent_description', 'description']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin interface for Transactions"""
    list_display = (
        'description_truncated',
        'company',
        'type',
        'amount_formatted',
        'date',
        'status',
        'category',
        'is_deleted'
    )
    list_filter = (
        'type',
        'status',
        'is_deleted',
        'date',
        'category',
        'account__type'
    )
    search_fields = (
        'description',
        'pluggy_transaction_id',
        'company__name',
        'merchant'
    )
    readonly_fields = (
        'id',
        'pluggy_transaction_id',
        'pluggy_created_at',
        'pluggy_updated_at',
        'created_at',
        'updated_at'
    )
    raw_id_fields = ('account', 'company', 'category')
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    
    fieldsets = (
        (_('Transaction Info'), {
            'fields': (
                'pluggy_transaction_id',
                'account',
                'company',
                'type',
                'status',
                'date'
            )
        }),
        (_('Description'), {
            'fields': ('description', 'description_raw')
        }),
        (_('Amount'), {
            'fields': (
                'amount',
                'amount_in_account_currency',
                'currency_code',
                'balance'
            )
        }),
        (_('Categorization'), {
            'fields': (
                'pluggy_category_id',
                'pluggy_category_description',
                'category'
            )
        }),
        (_('Additional Info'), {
            'fields': (
                'provider_code',
                'provider_id',
                'operation_type',
                'payment_method',
                'merchant',
                'payment_data',
                'credit_card_metadata'
            ),
            'classes': ('collapse',)
        }),
        (_('User Data'), {
            'fields': ('notes', 'tags'),
            'classes': ('collapse',)
        }),
        (_('Deletion'), {
            'fields': ('is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': (
                'id',
                'metadata',
                'pluggy_created_at',
                'pluggy_updated_at',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def description_truncated(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_truncated.short_description = _('Description')
    
    def amount_formatted(self, obj):
        return obj.get_amount_display()
    amount_formatted.short_description = _('Amount')
    
    def get_queryset(self, request):
        """Show all transactions including deleted ones in admin"""
        return self.model.objects.all()


@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    """Admin interface for Transaction Categories"""
    list_display = (
        'display_name',
        'type',
        'company',
        'parent',
        'icon',
        'color_display',
        'is_system',
        'is_active',
        'order'
    )
    list_filter = (
        'type',
        'is_system',
        'is_active',
        'created_at'
    )
    search_fields = ('name', 'slug', 'company__name')
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('company', 'parent')
    ordering = ['type', 'order', 'name']
    
    fieldsets = (
        (_('Basic Info'), {
            'fields': ('name', 'slug', 'type', 'company')
        }),
        (_('Hierarchy'), {
            'fields': ('parent', 'order')
        }),
        (_('Visual'), {
            'fields': ('icon', 'color')
        }),
        (_('Settings'), {
            'fields': ('is_system', 'is_active')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def display_name(self, obj):
        return str(obj)
    display_name.short_description = _('Category')
    
    def color_display(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; '
            'border: 1px solid #ccc; border-radius: 2px;"></div>',
            obj.color
        )
    color_display.short_description = _('Color')


@admin.register(ItemWebhook)
class ItemWebhookAdmin(admin.ModelAdmin):
    """Admin interface for Item Webhooks"""
    list_display = (
        'event_id',
        'item',
        'event_type',
        'processed',
        'triggered_by',
        'processed_at',
        'created_at'
    )
    list_filter = (
        'event_type',
        'processed',
        'triggered_by',
        'created_at'
    )
    search_fields = ('event_id', 'item__pluggy_item_id', 'error')
    readonly_fields = ('id', 'event_id', 'created_at', 'payload')
    raw_id_fields = ('item',)
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        (_('Event Info'), {
            'fields': ('event_id', 'item', 'event_type', 'triggered_by')
        }),
        (_('Processing'), {
            'fields': ('processed', 'processed_at', 'error')
        }),
        (_('Data'), {
            'fields': ('payload',),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': ('id', 'created_at'),
        }),
    )
    
    actions = ['mark_as_processed', 'mark_as_unprocessed']
    
    def mark_as_processed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(processed=True, processed_at=timezone.now())
        self.message_user(request, f'{updated} webhook(s) marked as processed.')
    mark_as_processed.short_description = _('Mark selected as processed')
    
    def mark_as_unprocessed(self, request, queryset):
        updated = queryset.update(processed=False, processed_at=None)
        self.message_user(request, f'{updated} webhook(s) marked as unprocessed.')
    mark_as_unprocessed.short_description = _('Mark selected as unprocessed')