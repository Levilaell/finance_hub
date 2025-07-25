"""
Banking app admin configuration - Pluggy Integration
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import (
    PluggyConnector, PluggyItem, BankAccount, 
    Transaction, TransactionCategory, PluggyCategory, ItemWebhook
)


@admin.register(PluggyConnector)
class PluggyConnectorAdmin(admin.ModelAdmin):
    list_display = ['pluggy_id', 'name', 'type', 'country', 'is_open_finance', 'is_sandbox', 'updated_at']
    list_filter = ['type', 'country', 'is_open_finance', 'is_sandbox', 'has_mfa', 'has_oauth']
    search_fields = ['name', 'pluggy_id']
    readonly_fields = ['pluggy_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('pluggy_id', 'name', 'institution_url', 'image_url', 'primary_color')
        }),
        ('Classification', {
            'fields': ('type', 'country', 'is_sandbox')
        }),
        ('Features', {
            'fields': ('has_mfa', 'has_oauth', 'is_open_finance', 'products')
        }),
        ('Technical', {
            'fields': ('credentials',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            items_count=Count('items'),
            accounts_count=Count('items__accounts')
        )


@admin.register(PluggyItem)
class PluggyItemAdmin(admin.ModelAdmin):
    list_display = ['pluggy_id', 'company', 'connector', 'status', 'execution_status', 'accounts_count', 'last_successful_update']
    list_filter = ['status', 'execution_status', 'connector__name', 'created_at']
    search_fields = ['pluggy_id', 'company__name', 'connector__name', 'client_user_id']
    readonly_fields = ['id', 'pluggy_id', 'created_at', 'updated_at', 'last_successful_update', 'created', 'modified']
    raw_id_fields = ['company', 'connector']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'pluggy_id', 'company', 'connector', 'client_user_id')
        }),
        ('Status', {
            'fields': ('status', 'execution_status', 'last_successful_update')
        }),
        ('Error Information', {
            'fields': ('error_code', 'error_message', 'status_detail'),
            'classes': ('collapse',)
        }),
        ('Open Finance', {
            'fields': ('consent_id', 'consent_expires_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created', 'modified')
        }),
    )
    
    def accounts_count(self, obj):
        return obj.accounts.count()
    accounts_count.short_description = 'Accounts'
    
    actions = ['sync_items']
    
    def sync_items(self, request, queryset):
        from .tasks import sync_bank_account
        count = 0
        for item in queryset:
            sync_bank_account.delay(str(item.id))
            count += 1
        self.message_user(request, f'{count} items queued for synchronization')
    sync_items.short_description = 'Queue sync for selected items'


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'company', 'type', 'balance_display', 'item_status', 'is_active', 'updated_at']
    list_filter = ['type', 'is_active', 'item__status', 'currency_code', 'created_at']
    search_fields = ['name', 'marketing_name', 'number', 'owner', 'company__name']
    readonly_fields = ['id', 'pluggy_id', 'masked_number', 'created_at', 'updated_at', 'created', 'modified']
    raw_id_fields = ['item', 'company']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'pluggy_id', 'item', 'company')
        }),
        ('Account Details', {
            'fields': ('type', 'subtype', 'number', 'masked_number', 'name', 'marketing_name')
        }),
        ('Owner Information', {
            'fields': ('owner', 'tax_number')
        }),
        ('Balance', {
            'fields': ('balance', 'balance_date', 'currency_code')
        }),
        ('Additional Data', {
            'fields': ('bank_data', 'credit_data'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created', 'modified')
        }),
    )
    
    def balance_display(self, obj):
        return f'{obj.currency_code} {obj.balance:,.2f}'
    balance_display.short_description = 'Balance'
    
    def item_status(self, obj):
        status = obj.item.status
        colors = {
            'UPDATED': 'green',
            'LOGIN_ERROR': 'red',
            'OUTDATED': 'orange',
            'ERROR': 'red',
            'UPDATING': 'blue',
            'WAITING_USER_INPUT': 'orange'
        }
        color = colors.get(status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    item_status.short_description = 'Item Status'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('item', 'company', 'item__connector')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'description', 'amount_display', 'type', 'category', 'account_name', 'created_at']
    list_filter = ['type', 'status', 'date', 'category', 'account__type']
    search_fields = ['description', 'pluggy_id', 'notes']
    readonly_fields = ['id', 'pluggy_id', 'created_at', 'updated_at', 'created', 'modified']
    raw_id_fields = ['account', 'category']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'pluggy_id', 'account')
        }),
        ('Transaction Details', {
            'fields': ('type', 'status', 'description', 'amount', 'currency_code', 'date')
        }),
        ('Categorization', {
            'fields': ('pluggy_category_id', 'pluggy_category_description', 'category')
        }),
        ('Additional Information', {
            'fields': ('merchant', 'payment_data', 'operation_type', 'payment_method'),
            'classes': ('collapse',)
        }),
        ('Credit Card', {
            'fields': ('credit_card_metadata',),
            'classes': ('collapse',)
        }),
        ('User Data', {
            'fields': ('notes', 'tags')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created', 'modified')
        }),
    )
    
    def amount_display(self, obj):
        color = 'green' if obj.type == 'CREDIT' else 'red'
        sign = '+' if obj.type == 'CREDIT' else '-'
        return format_html(
            '<span style="color: {};">{}{} {:.2f}</span>',
            color,
            sign,
            obj.currency_code,
            abs(obj.amount)
        )
    amount_display.short_description = 'Amount'
    
    def account_name(self, obj):
        return obj.account.display_name
    account_name.short_description = 'Account'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('account', 'category', 'account__item__connector')


@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'parent', 'icon', 'color_display', 'is_system', 'is_active', 'order']
    list_filter = ['type', 'is_system', 'is_active', 'parent']
    search_fields = ['name', 'slug']
    readonly_fields = ['id', 'slug', 'created', 'modified']
    raw_id_fields = ['company', 'parent']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'slug', 'type', 'company')
        }),
        ('Hierarchy', {
            'fields': ('parent',)
        }),
        ('Visual', {
            'fields': ('icon', 'color')
        }),
        ('Settings', {
            'fields': ('is_system', 'is_active', 'order')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified')
        }),
    )
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 10px; color: white; border-radius: 3px;">{}</span>',
            obj.color,
            obj.color
        )
    color_display.short_description = 'Color'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('parent', 'company')


@admin.register(PluggyCategory)
class PluggyCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'description', 'parent_description', 'internal_category']
    list_filter = ['parent_description']
    search_fields = ['id', 'description', 'parent_description']
    raw_id_fields = ['internal_category']
    
    fieldsets = (
        ('Pluggy Category', {
            'fields': ('id', 'description', 'parent_id', 'parent_description')
        }),
        ('Mapping', {
            'fields': ('internal_category',)
        }),
    )


@admin.register(ItemWebhook)
class ItemWebhookAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'item', 'event_id', 'processed', 'processed_at', 'created']
    list_filter = ['event_type', 'processed', 'created']
    search_fields = ['event_id', 'item__pluggy_id']
    readonly_fields = ['id', 'event_id', 'payload', 'created']
    raw_id_fields = ['item']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('id', 'event_id', 'event_type', 'item')
        }),
        ('Processing', {
            'fields': ('processed', 'processed_at', 'error')
        }),
        ('Payload', {
            'fields': ('payload',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created',)
        }),
    )
    
    actions = ['process_webhooks']
    
    def process_webhooks(self, request, queryset):
        from .tasks import process_webhook_event
        count = 0
        for webhook in queryset.filter(processed=False):
            process_webhook_event.delay(webhook.event_type, webhook.payload)
            count += 1
        self.message_user(request, f'{count} webhooks queued for processing')
    process_webhooks.short_description = 'Process selected webhooks'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('item', 'item__connector')


# Admin Site Customization
admin.site.site_header = "Finance Hub - Banking Admin"
admin.site.site_title = "Banking Admin"
admin.site.index_title = "Banking Management"