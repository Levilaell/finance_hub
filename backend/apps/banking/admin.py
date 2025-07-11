"""
Banking app admin configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from decimal import Decimal

from .models import (
    BankProvider, BankAccount, Transaction, TransactionCategory,
    RecurringTransaction, Budget, FinancialGoal, BankSync
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
        'is_active', 'last_sync_display'
    ]
    list_filter = ['account_type', 'is_active', 'status', 'bank_provider', 'created_at']
    search_fields = ['nickname', 'account_number', 'company__name']
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
        ('Conexão Open Banking', {
            'fields': (
                'external_id', 'pluggy_item_id',
                'token_expires_at', 'status'
            ),
            'classes': ('collapse',)
        }),
        ('Configurações', {
            'fields': ('is_primary', 'is_active', 'last_sync_at', 'sync_frequency')
        }),
    )
    
    readonly_fields = ['last_sync_at', 'created_at', 'updated_at']
    
    def company_name(self, obj):
        return obj.company.name
    company_name.short_description = 'Empresa'
    
    def current_balance_display(self, obj):
        color = 'green' if obj.current_balance >= 0 else 'red'
        return format_html(
            '<span style="color: {};">R$ {:,.2f}</span>',
            color,
            obj.current_balance
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
        'category', 'account_display', 'transaction_type',
        'is_ai_categorized', 'is_manually_reviewed'
    ]
    list_filter = [
        'transaction_type', 'status', 'category', 'transaction_date',
        'is_ai_categorized', 'is_manually_reviewed', 'is_reconciled',
        'bank_account__bank_provider'
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
                'category', 'subcategory', 'ai_suggested_category',
                'ai_category_confidence', 'is_ai_categorized', 'is_manually_reviewed'
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
            '<span style="color: {};">{} R$ {:,.2f}</span>',
            color, sign, abs(obj.amount)
        )
    formatted_amount_display.short_description = 'Valor'
    
    def account_display(self, obj):
        return f"{obj.bank_account.bank_provider.name} - {obj.bank_account.display_name}"
    account_display.short_description = 'Conta'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('bank_account__bank_provider', 'category', 'subcategory', 'ai_suggested_category')


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'company', 'amount_display', 'budget_type',
        'spent_percentage', 'alert_threshold', 'status',
        'start_date', 'end_date'
    ]
    list_filter = ['budget_type', 'status', 'created_at']
    search_fields = ['name', 'company__name']
    date_hierarchy = 'created_at'
    filter_horizontal = ['categories']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('company', 'name', 'description')
        }),
        ('Configurações do Orçamento', {
            'fields': ('budget_type', 'amount', 'spent_amount', 'categories')
        }),
        ('Período', {
            'fields': ('start_date', 'end_date')
        }),
        ('Alertas', {
            'fields': ('alert_threshold', 'is_alert_enabled', 'last_alert_sent')
        }),
        ('Status', {
            'fields': ('status', 'is_rollover', 'created_by')
        }),
    )
    
    readonly_fields = ['spent_amount', 'last_alert_sent', 'created_at', 'updated_at']
    
    def amount_display(self, obj):
        return f"R$ {obj.amount:,.2f}"
    amount_display.short_description = 'Orçamento'
    
    def spent_percentage(self, obj):
        percentage = obj.spent_percentage
        color = 'green' if percentage < 80 else 'orange' if percentage < 100 else 'red'
        return format_html(
            '<span style="color: {};">{}%</span>',
            color, int(percentage)
        )
    spent_percentage.short_description = '% Gasto'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company', 'created_by').prefetch_related('categories')


@admin.register(FinancialGoal)
class FinancialGoalAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'goal_type', 'target_amount_display',
        'progress_bar', 'target_date', 'status'
    ]
    list_filter = ['goal_type', 'status', 'target_date']
    search_fields = ['name', 'description', 'company__name']
    date_hierarchy = 'target_date'
    filter_horizontal = ['categories', 'bank_accounts']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('company', 'name', 'description', 'goal_type')
        }),
        ('Configurações da Meta', {
            'fields': ('target_amount', 'current_amount', 'target_date', 'monthly_target')
        }),
        ('Acompanhamento', {
            'fields': ('categories', 'bank_accounts')
        }),
        ('Configurações', {
            'fields': ('status', 'is_automatic_tracking', 'send_reminders', 'reminder_frequency')
        }),
        ('Metadados', {
            'fields': ('created_by', 'created_at', 'updated_at', 'completed_at')
        }),
    )
    
    readonly_fields = ['current_amount', 'created_at', 'updated_at', 'completed_at']
    
    def target_amount_display(self, obj):
        return f"R$ {obj.target_amount:,.2f}"
    target_amount_display.short_description = 'Meta'
    
    def progress_bar(self, obj):
        percentage = obj.progress_percentage
        return format_html(
            '<div style="width:100px; border:1px solid #ccc;">'
            '<div style="height:20px; background-color:#4CAF50; width:{}%"></div>'
            '</div> {}%',
            min(percentage, 100), int(percentage)
        )
    progress_bar.short_description = 'Progresso'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company', 'created_by').prefetch_related('categories', 'bank_accounts')


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


@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'bank_account', 'expected_amount_display', 
        'frequency', 'next_expected_date', 'is_active',
        'total_occurrences', 'accuracy_rate_display'
    ]
    list_filter = ['frequency', 'is_active', 'auto_categorize', 'send_alerts']
    search_fields = ['name', 'description_pattern', 'bank_account__nickname']
    date_hierarchy = 'next_expected_date'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('bank_account', 'name', 'description_pattern')
        }),
        ('Valores', {
            'fields': ('expected_amount', 'amount_tolerance')
        }),
        ('Frequência', {
            'fields': ('frequency', 'next_expected_date', 'day_tolerance')
        }),
        ('Categorização', {
            'fields': ('category',)
        }),
        ('Configurações', {
            'fields': ('is_active', 'auto_categorize', 'send_alerts')
        }),
        ('Estatísticas', {
            'fields': ('total_occurrences', 'last_occurrence_date', 'accuracy_rate')
        }),
    )
    
    readonly_fields = ['total_occurrences', 'last_occurrence_date', 'accuracy_rate', 'created_at', 'updated_at']
    
    def expected_amount_display(self, obj):
        return f"R$ {obj.expected_amount:,.2f}"
    expected_amount_display.short_description = 'Valor Esperado'
    
    def accuracy_rate_display(self, obj):
        return f"{obj.accuracy_rate:.1%}"
    accuracy_rate_display.short_description = 'Taxa de Acerto'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('bank_account__bank_provider', 'category')


