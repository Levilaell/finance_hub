"""
Django Admin configuration for Banking app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Connector, BankConnection, BankAccount,
    Transaction, SyncLog
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
        'category', 'account_name', 'created_at'
    ]
    list_filter = ['type', 'date', 'category']
    search_fields = [
        'description', 'merchant_name', 'category',
        'account__name', 'account__connection__user__username'
    ]
    readonly_fields = [
        'id', 'pluggy_transaction_id', 'payment_data',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['account']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']

    def account_name(self, obj):
        return obj.account.name
    account_name.short_description = 'Account'

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