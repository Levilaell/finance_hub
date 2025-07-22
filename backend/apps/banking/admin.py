"""
Banking app admin configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from decimal import Decimal

from .models import (
    BankProvider, BankAccount, Transaction, TransactionCategory,
    BankSync
)


@admin.register(BankProvider)
class BankProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_open_banking', 'is_active', 'account_count']
    list_filter = ['is_open_banking', 'is_active', 'supports_pix', 'supports_ted', 'supports_doc']
    search_fields = ['name', 'code']
    ordering = ['name']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'code', 'logo', 'color')
        }),
        ('Configurações de API', {
            'fields': ('is_open_banking', 'api_endpoint', 'is_active')
        }),
        ('Requisitos de Integração', {
            'fields': ('requires_agency', 'requires_account', 'supports_pix', 'supports_ted', 'supports_doc')
        }),
    )
    
    def account_count(self, obj):
        return obj.bankaccount_set.count()
    account_count.short_description = 'Contas conectadas'


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = [
        'display_name', 'company_name', 'bank_provider',
        'account_type', 'current_balance_display',
        'pluggy_status_display', 'is_active', 'last_sync_display'
    ]
    list_filter = ['account_type', 'is_active', 'status', 'bank_provider', 'created_at']
    search_fields = ['nickname', 'account_number', 'company__name', 'external_id', 'pluggy_item_id']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informações da Conta', {
            'fields': (
                'company', 'bank_provider', 'nickname',
                'account_type', 'agency', 'account_number', 'account_digit'
            )
        }),
        ('Saldos', {
            'fields': ('current_balance', 'available_balance')
        }),
        ('🔌 Integração Pluggy', {
            'fields': (
                'pluggy_connection_status', 'external_id', 'pluggy_item_id',
                'pluggy_item_status_info', 'sync_status', 'sync_error_message'
            ),
            'description': 'Status da conexão com a Pluggy. Items ACTIVE recebem webhooks automáticos.'
        }),
        ('Configurações', {
            'fields': ('is_primary', 'is_active', 'status', 'last_sync_at', 'sync_frequency')
        }),
    )
    
    readonly_fields = [
        'last_sync_at', 'created_at', 'updated_at', 
        'pluggy_connection_status', 'pluggy_item_status_info'
    ]
    
    def company_name(self, obj):
        return obj.company.name
    company_name.short_description = 'Empresa'
    
    def current_balance_display(self, obj):
        color = 'green' if obj.current_balance >= 0 else 'red'
        return format_html(
            '<span style="color: {};">R$ {}</span>',
            color,
            '{:,.2f}'.format(obj.current_balance)
        )
    current_balance_display.short_description = 'Saldo'
    
    def last_sync_display(self, obj):
        if obj.last_sync_at:
            return obj.last_sync_at.strftime('%d/%m/%Y %H:%M')
        return 'Nunca sincronizado'
    last_sync_display.short_description = 'Última sincronização'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company', 'bank_provider')
    
    def pluggy_status_display(self, obj):
        """Mostra status da conexão Pluggy"""
        if not obj.pluggy_item_id:
            return format_html('<span style="color: gray;">Não conectado</span>')
        
        # TODO: Buscar status real do item via API
        # Por enquanto, mostrar se tem IDs
        if obj.external_id and obj.pluggy_item_id:
            return format_html(
                '<span style="color: orange;" title="Item ID: {}">⚡ Conectado</span>',
                obj.pluggy_item_id[:8]
            )
        return format_html('<span style="color: red;">❌ Erro</span>')
    pluggy_status_display.short_description = 'Pluggy'
    
    def pluggy_connection_status(self, obj):
        """Status detalhado da conexão Pluggy"""
        if not obj.pluggy_item_id:
            return "Não conectado à Pluggy"
        
        return format_html(
            '<strong>✅ Conectado</strong><br>'
            'External ID: <code>{}</code><br>'
            'Item ID: <code>{}</code>',
            obj.external_id or 'N/A',
            obj.pluggy_item_id or 'N/A'
        )
    pluggy_connection_status.short_description = 'Status da Conexão'
    
    def pluggy_item_status_info(self, obj):
        """Informações sobre o status do item"""
        if not obj.pluggy_item_id:
            return "—"
        
        # TODO: Implementar chamada à API para pegar status real
        return format_html(
            '<div style="background: #f0f0f0; padding: 10px; border-radius: 5px;">'
            '<strong>⚠️ Status do Item: UPDATED</strong><br>'
            '<small>Items com status UPDATED não recebem webhooks automáticos.<br>'
            'Para ativar webhooks, reconecte a conta autorizando "Atualização Automática".</small>'
            '</div>'
        )
    pluggy_item_status_info.short_description = 'Informações do Item Pluggy'


@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'slug', 'category_type', 'parent',
        'icon_display', 'color_display', 'transaction_count',
        'is_system', 'is_active'
    ]
    list_filter = ['category_type', 'is_system', 'is_active']
    search_fields = ['name', 'slug']
    ordering = ['category_type', 'order', 'name']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'slug', 'category_type', 'parent')
        }),
        ('Visual', {
            'fields': ('icon', 'color')
        }),
        ('Configurações de IA', {
            'fields': ('keywords', 'confidence_threshold')
        }),
        ('Status', {
            'fields': ('is_system', 'is_active', 'order')
        }),
    )
    
    def icon_display(self, obj):
        return obj.icon or ''
    icon_display.short_description = 'Ícone'
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 8px; color: white;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = 'Cor'
    
    def transaction_count(self, obj):
        return obj.transactions.count()
    transaction_count.short_description = 'Transações'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_date', 'description', 'formatted_amount_display',
        'category', 'account_display', 'transaction_type'
    ]
    list_filter = [
        'transaction_type', 'status', 'category', 'transaction_date',
        'is_reconciled', 'bank_account__bank_provider'
    ]
    search_fields = ['description', 'counterpart_name', 'external_id', 'reference_number']
    date_hierarchy = 'transaction_date'
    ordering = ['-transaction_date']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': (
                'bank_account', 'transaction_type', 'amount',
                'transaction_date', 'posted_date', 'description',
                'status'
            )
        }),
        ('Categorização', {
            'fields': (
                'category', 'subcategory'
            )
        }),
        ('Contrapartida', {
            'fields': (
                'counterpart_name', 'counterpart_document', 'counterpart_bank',
                'counterpart_agency', 'counterpart_account'
            ),
            'classes': ('collapse',)
        }),
        ('Detalhes Adicionais', {
            'fields': (
                'external_id', 'reference_number', 'pix_key',
                'balance_after', 'notes', 'tags'
            ),
            'classes': ('collapse',)
        }),
        ('Conciliação', {
            'fields': (
                'is_reconciled', 'reconciled_at', 'reconciled_by'
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['id', 'created_at', 'updated_at', 'reconciled_at']
    
    def formatted_amount_display(self, obj):
        if obj.is_income:
            color = 'green'
            sign = '+'
        else:
            color = 'red'
            sign = '-'
        return format_html(
            '<span style="color: {};">{} R$ {}</span>',
            color, sign, '{:,.2f}'.format(abs(obj.amount))
        )
    formatted_amount_display.short_description = 'Valor'
    
    def account_display(self, obj):
        return f"{obj.bank_account.bank_provider.name} - {obj.bank_account.display_name}"
    account_display.short_description = 'Conta'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('bank_account__bank_provider', 'category', 'subcategory')


@admin.register(BankSync)
class BankSyncAdmin(admin.ModelAdmin):
    list_display = [
        'bank_account_display', 'status',
        'transactions_found', 'transactions_new', 'transactions_updated',
        'duration_display', 'started_at'
    ]
    list_filter = ['status', 'started_at']
    search_fields = ['bank_account__nickname', 'error_message']
    date_hierarchy = 'started_at'
    ordering = ['-started_at']
    
    fieldsets = (
        ('Informações da Sincronização', {
            'fields': ('bank_account', 'status')
        }),
        ('Período da Sincronização', {
            'fields': ('sync_from_date', 'sync_to_date')
        }),
        ('Resultados', {
            'fields': ('transactions_found', 'transactions_new', 'transactions_updated')
        }),
        ('Tempo', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Erros', {
            'fields': ('error_code', 'error_message'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'started_at', 'completed_at',
        'transactions_found', 'transactions_new', 'transactions_updated'
    ]
    
    def bank_account_display(self, obj):
        return f"{obj.bank_account.bank_provider.name} - {obj.bank_account.display_name}"
    bank_account_display.short_description = 'Conta'
    
    def duration_display(self, obj):
        if obj.duration:
            total_seconds = obj.duration.total_seconds()
            if total_seconds < 60:
                return f"{total_seconds:.1f}s"
            else:
                minutes = int(total_seconds // 60)
                seconds = total_seconds % 60
                return f"{minutes}m {seconds:.0f}s"
        return '-'
    duration_display.short_description = 'Duração'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('bank_account__bank_provider', 'bank_account__company')



