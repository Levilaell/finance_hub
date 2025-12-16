"""
Django Admin configuration for Banking app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Connector, BankConnection, BankAccount,
    Transaction, Category, SyncLog, Bill, CategoryRule
)


@admin.register(Connector)
class ConnectorAdmin(admin.ModelAdmin):
    """Admin interface for Connectors."""
    list_display = [
        'name', 'institution_name', 'country', 'type',
        'is_sandbox', 'is_active', 'created_at'
    ]
    list_filter = ['country', 'type', 'is_sandbox', 'is_active']
    search_fields = ['name', 'institution_name']
    readonly_fields = ['pluggy_id', 'created_at', 'updated_at']
    ordering = ['name']

    def has_add_permission(self, request):
        # Connectors should only be synced from Pluggy
        return False


@admin.register(BankConnection)
class BankConnectionAdmin(admin.ModelAdmin):
    """Admin interface for Bank Connections."""
    list_display = [
        'id', 'user', 'connector_name', 'status_badge',
        'last_updated_at', 'is_active', 'created_at'
    ]
    list_filter = ['status', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'connector__name']
    readonly_fields = [
        'id', 'pluggy_item_id', 'status_detail',
        'execution_status', 'last_updated_at',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['user']

    def connector_name(self, obj):
        return obj.connector.name
    connector_name.short_description = 'Connector'

    def status_badge(self, obj):
        colors = {
            'UPDATED': 'green',
            'UPDATING': 'blue',
            'LOGIN_ERROR': 'red',
            'WAITING_USER_INPUT': 'orange',
            'OUTDATED': 'gray',
            'ERROR': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.status
        )
    status_badge.short_description = 'Status'


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    """Admin interface for Bank Accounts."""
    list_display = [
        'name', 'type', 'connection_user', 'balance_display',
        'last_synced_at', 'is_active'
    ]
    list_filter = ['type', 'is_active', 'currency_code']
    search_fields = [
        'name', 'number',
        'connection__user__username',
        'connection__user__email'
    ]
    readonly_fields = [
        'id', 'pluggy_account_id', 'bank_data',
        'created_at', 'updated_at', 'last_synced_at'
    ]
    raw_id_fields = ['connection']

    def connection_user(self, obj):
        return obj.connection.user.username
    connection_user.short_description = 'User'

    def balance_display(self, obj):
        return f"{obj.currency_code} {obj.balance:,.2f}"
    balance_display.short_description = 'Balance'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin interface for Transactions."""
    list_display = [
        'date', 'description', 'type_badge', 'amount_display',
        'effective_category', 'account_name', 'created_at'
    ]
    list_filter = ['type', 'date', 'user_category', 'pluggy_category']
    search_fields = [
        'description', 'merchant_name', 'pluggy_category',
        'account__name', 'account__connection__user__username'
    ]
    readonly_fields = [
        'id', 'pluggy_transaction_id', 'pluggy_category', 'pluggy_category_id',
        'payment_data', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['account', 'user_category']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']

    def account_name(self, obj):
        return obj.account.name
    account_name.short_description = 'Account'

    def effective_category(self, obj):
        """Display user category if set, otherwise Pluggy category."""
        if obj.user_category:
            return f"{obj.user_category.name} (custom)"
        return obj.pluggy_category or '-'
    effective_category.short_description = 'Category'

    def type_badge(self, obj):
        color = 'green' if obj.type == 'CREDIT' else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_type_display()
        )
    type_badge.short_description = 'Type'

    def amount_display(self, obj):
        sign = '+' if obj.type == 'CREDIT' else '-'
        return f"{sign}{obj.currency_code} {obj.amount:,.2f}"
    amount_display.short_description = 'Amount'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Categories."""
    list_display = [
        'name', 'type', 'color_badge', 'icon', 'user',
        'is_system', 'parent', 'created_at'
    ]
    list_filter = ['type', 'is_system', 'created_at']
    search_fields = ['name', 'user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['user', 'parent']
    ordering = ['type', 'name']

    def color_badge(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            obj.color, obj.color
        )
    color_badge.short_description = 'Color'


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    """Admin interface for Sync Logs."""
    list_display = [
        'sync_type', 'status_badge', 'connection_info',
        'records_synced', 'started_at', 'duration'
    ]
    list_filter = ['sync_type', 'status', 'started_at']
    readonly_fields = [
        'sync_type', 'status', 'started_at', 'completed_at',
        'records_synced', 'error_message', 'details'
    ]
    ordering = ['-started_at']

    def connection_info(self, obj):
        if obj.connection:
            return f"{obj.connection.user.username} - {obj.connection.connector.name}"
        return "System"
    connection_info.short_description = 'Connection'

    def status_badge(self, obj):
        colors = {
            'SUCCESS': 'green',
            'IN_PROGRESS': 'blue',
            'PENDING': 'orange',
            'FAILED': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.status
        )
    status_badge.short_description = 'Status'

    def duration(self, obj):
        if obj.completed_at and obj.started_at:
            delta = obj.completed_at - obj.started_at
            return f"{delta.total_seconds():.1f}s"
        return "-"
    duration.short_description = 'Duration'

    def has_add_permission(self, request):
        # Sync logs are created automatically
        return False


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    """Admin interface for Bills (Contas a Pagar/Receber)."""
    list_display = [
        'description', 'user_email', 'type_badge', 'amount_display',
        'status_badge', 'due_date', 'is_overdue_badge', 'category_name',
        'created_from_ocr', 'created_at'
    ]
    list_filter = ['type', 'status', 'recurrence', 'created_from_ocr', 'due_date', 'created_at']
    search_fields = [
        'description', 'customer_supplier', 'barcode',
        'user__email', 'user__first_name', 'user__last_name'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'paid_at',
        'ocr_confidence', 'ocr_raw_data', 'amount_remaining_display',
        'payment_percentage_display'
    ]
    raw_id_fields = ['user', 'category', 'linked_transaction', 'parent_bill']
    date_hierarchy = 'due_date'
    ordering = ['due_date', '-created_at']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'type', 'description', 'customer_supplier')
        }),
        ('Valores', {
            'fields': ('amount', 'amount_paid', 'amount_remaining_display',
                      'payment_percentage_display', 'currency_code')
        }),
        ('Datas e Status', {
            'fields': ('due_date', 'status', 'paid_at')
        }),
        ('Categorização', {
            'fields': ('category', 'recurrence', 'parent_bill', 'installment_number')
        }),
        ('OCR / Boleto', {
            'fields': ('source_file', 'barcode', 'created_from_ocr',
                      'ocr_confidence', 'ocr_raw_data'),
            'classes': ('collapse',)
        }),
        ('Vinculação Bancária', {
            'fields': ('linked_transaction',),
            'classes': ('collapse',)
        }),
        ('Notas', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Usuário'
    user_email.admin_order_field = 'user__email'

    def type_badge(self, obj):
        color = '#10b981' if obj.type == 'receivable' else '#ef4444'
        label = 'A Receber' if obj.type == 'receivable' else 'A Pagar'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, label
        )
    type_badge.short_description = 'Tipo'

    def amount_display(self, obj):
        return f"{obj.currency_code} {obj.amount:,.2f}"
    amount_display.short_description = 'Valor'

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'partially_paid': '#3b82f6',
            'paid': '#10b981',
            'cancelled': '#6b7280',
        }
        labels = {
            'pending': 'Pendente',
            'partially_paid': 'Parcial',
            'paid': 'Pago',
            'cancelled': 'Cancelado',
        }
        color = colors.get(obj.status, '#6b7280')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            color, label
        )
    status_badge.short_description = 'Status'

    def is_overdue_badge(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold;">⚠ Atrasado</span>')
        return '-'
    is_overdue_badge.short_description = 'Atraso'

    def category_name(self, obj):
        return obj.category.name if obj.category else '-'
    category_name.short_description = 'Categoria'

    def amount_remaining_display(self, obj):
        return f"{obj.currency_code} {obj.amount_remaining:,.2f}"
    amount_remaining_display.short_description = 'Valor Restante'

    def payment_percentage_display(self, obj):
        return f"{obj.payment_percentage:.1f}%"
    payment_percentage_display.short_description = '% Pago'


@admin.register(CategoryRule)
class CategoryRuleAdmin(admin.ModelAdmin):
    """Admin interface for Category Rules (Regras de Categorização)."""
    list_display = [
        'pattern', 'match_type_badge', 'category_display', 'user_email',
        'applied_count', 'is_active_badge', 'created_at'
    ]
    list_filter = ['match_type', 'is_active', 'created_at']
    search_fields = [
        'pattern', 'category__name',
        'user__email', 'user__first_name', 'user__last_name'
    ]
    readonly_fields = ['id', 'applied_count', 'created_from_transaction', 'created_at', 'updated_at']
    raw_id_fields = ['user', 'category', 'created_from_transaction']
    ordering = ['-created_at']

    fieldsets = (
        ('Regra', {
            'fields': ('user', 'pattern', 'match_type', 'category')
        }),
        ('Status', {
            'fields': ('is_active', 'applied_count')
        }),
        ('Origem', {
            'fields': ('created_from_transaction',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Usuário'
    user_email.admin_order_field = 'user__email'

    def match_type_badge(self, obj):
        colors = {
            'prefix': '#3b82f6',
            'contains': '#8b5cf6',
            'fuzzy': '#f59e0b',
        }
        color = colors.get(obj.match_type, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_match_type_display()
        )
    match_type_badge.short_description = 'Tipo Match'

    def category_display(self, obj):
        return format_html(
            '<span style="color: {};">{} {}</span>',
            obj.category.color, obj.category.icon, obj.category.name
        )
    category_display.short_description = 'Categoria'

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Ativo</span>')
        return format_html('<span style="color: red;">✗ Inativo</span>')
    is_active_badge.short_description = 'Status'