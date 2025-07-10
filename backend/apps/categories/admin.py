"""
Categories app admin configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg

from .models import (
    CategoryRule, AITrainingData, CategorySuggestion,
    CategoryPerformance, CategorizationLog
)


@admin.register(CategoryRule)
class CategoryRuleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'company', 'category', 'rule_type',
        'priority', 'is_active', 'match_count',
        'created_at'
    ]
    list_filter = ['rule_type', 'is_active', 'category', 'created_at']
    search_fields = ['name', 'company__name']
    ordering = ['company', '-priority', 'name']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('company', 'name', 'category')
        }),
        ('Configuração da Regra', {
            'fields': ('rule_type', 'conditions', 'priority', 'is_active', 'confidence_threshold')
        }),
        ('Estatísticas', {
            'fields': ('match_count', 'accuracy_rate'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['match_count', 'accuracy_rate']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company', 'category')


@admin.register(AITrainingData)
class AITrainingDataAdmin(admin.ModelAdmin):
    list_display = [
        'description_truncated', 'category',
        'subcategory', 'amount',
        'verification_source', 'is_verified', 'created_at'
    ]
    list_filter = [
        'is_verified', 'verification_source',
        'category', 'created_at'
    ]
    search_fields = ['description', 'counterpart_name']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Dados da Transação', {
            'fields': (
                'company', 'description',
                'counterpart_name', 'amount', 'transaction_type'
            )
        }),
        ('Categorização', {
            'fields': (
                'category', 'subcategory'
            )
        }),
        ('Verificação', {
            'fields': (
                'is_verified', 'verification_source',
                'verified_by'
            )
        }),
        ('Dados Técnicos', {
            'fields': ('extracted_features',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def description_truncated(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_truncated.short_description = 'Descrição'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company', 'category', 'subcategory', 'verified_by')


@admin.register(CategorySuggestion)
class CategorySuggestionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_display', 'suggested_category',
        'confidence_display', 'acceptance_status',
        'created_at'
    ]
    list_filter = ['is_accepted', 'is_rejected', 'suggested_category', 'created_at']
    search_fields = ['transaction__description']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Transação', {
            'fields': ('transaction',)
        }),
        ('Sugestão', {
            'fields': (
                'suggested_category', 'confidence_score',
                'alternative_suggestions'
            )
        }),
        ('Feedback', {
            'fields': (
                'is_accepted', 'is_rejected', 'user_feedback',
                'reviewed_at', 'reviewed_by'
            )
        }),
        ('Técnico', {
            'fields': ('model_version', 'features_used'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['reviewed_at', 'created_at']
    
    def transaction_display(self, obj):
        return f"{obj.transaction.description[:40]}..."
    transaction_display.short_description = 'Transação'
    
    def confidence_display(self, obj):
        color = 'green' if obj.confidence_score >= 0.8 else 'orange' if obj.confidence_score >= 0.6 else 'red'
        return format_html(
            '<span style="color: {};">{:.2%}</span>',
            color, obj.confidence_score
        )
    confidence_display.short_description = 'Confiança'
    
    def acceptance_status(self, obj):
        if obj.is_accepted:
            return format_html('<span style="color: green;">Aceita</span>')
        elif obj.is_rejected:
            return format_html('<span style="color: red;">Rejeitada</span>')
        else:
            return format_html('<span style="color: gray;">Pendente</span>')
    acceptance_status.short_description = 'Status'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('transaction', 'suggested_category', 'reviewed_by')


@admin.register(CategoryPerformance)
class CategoryPerformanceAdmin(admin.ModelAdmin):
    list_display = [
        'category', 'company', 'accuracy_display',
        'total_predictions', 'correct_predictions',
        'period_start', 'period_end'
    ]
    list_filter = ['category', 'period_start']
    search_fields = ['company__name', 'category__name']
    date_hierarchy = 'period_start'
    ordering = ['-period_start', '-accuracy']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('company', 'category', 'period_start', 'period_end')
        }),
        ('Métricas de Desempenho', {
            'fields': (
                'total_predictions', 'correct_predictions',
                'false_positives', 'false_negatives'
            )
        }),
        ('Métricas Calculadas', {
            'fields': ('accuracy', 'precision', 'recall', 'f1_score'),
            'description': 'Métricas calculadas automaticamente'
        }),
    )
    
    readonly_fields = ['accuracy', 'precision', 'recall', 'f1_score', 'calculated_at']
    
    def accuracy_display(self, obj):
        color = 'green' if obj.accuracy >= 0.9 else 'orange' if obj.accuracy >= 0.7 else 'red'
        return format_html(
            '<span style="color: {};">{:.2%}</span>',
            color, obj.accuracy
        )
    accuracy_display.short_description = 'Taxa de Acerto'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company', 'category')


@admin.register(CategorizationLog)
class CategorizationLogAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_display', 'method', 'suggested_category',
        'confidence_score_display', 'processing_time_display',
        'was_accepted', 'created_at'
    ]
    list_filter = ['method', 'was_accepted', 'suggested_category', 'created_at']
    search_fields = ['transaction__description']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Transação', {
            'fields': ('transaction',)
        }),
        ('Categorização', {
            'fields': (
                'method', 'suggested_category', 'confidence_score',
                'processing_time_ms'
            )
        }),
        ('Contexto', {
            'fields': ('rule_used', 'ai_model_version')
        }),
        ('Resultado', {
            'fields': ('was_accepted', 'final_category')
        }),
    )
    
    readonly_fields = ['created_at', 'processing_time_ms']
    
    def transaction_display(self, obj):
        return f"{obj.transaction.description[:40]}..."
    transaction_display.short_description = 'Transação'
    
    def confidence_score_display(self, obj):
        if obj.confidence_score:
            color = 'green' if obj.confidence_score >= 0.8 else 'orange' if obj.confidence_score >= 0.6 else 'red'
            return format_html(
                '<span style="color: {};">{:.2%}</span>',
                color, obj.confidence_score
            )
        return '-'
    confidence_score_display.short_description = 'Confiança'
    
    def processing_time_display(self, obj):
        if obj.processing_time_ms:
            return f"{obj.processing_time_ms}ms"
        return '-'
    processing_time_display.short_description = 'Tempo'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('transaction', 'suggested_category', 'final_category', 'rule_used')