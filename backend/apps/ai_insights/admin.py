"""
AI Insights admin configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum
from core.admin import BaseModelAdmin, ExportMixin, StatusColorMixin

from .models import (
    AICredit,
    AICreditTransaction,
    AIConversation,
    AIMessage,
    AIInsight
)


@admin.register(AICredit)
class AICreditAdmin(BaseModelAdmin):
    """Admin para créditos AI"""
    list_display = [
        'company', 'balance', 'monthly_allowance', 'bonus_credits',
        'total_available', 'last_reset', 'created_at'
    ]
    list_filter = ['last_reset', 'created_at']
    search_fields = ['company__name', 'company__cnpj']
    readonly_fields = ['created_at', 'updated_at', 'total_available']
    
    def total_available(self, obj):
        """Total de créditos disponíveis"""
        return obj.balance + obj.bonus_credits
    total_available.short_description = 'Total Disponível'
    
    fieldsets = (
        ('Empresa', {
            'fields': ('company',)
        }),
        ('Créditos', {
            'fields': (
                'balance', 'monthly_allowance', 'bonus_credits',
                'total_available', 'total_purchased'
            )
        }),
        ('Controle', {
            'fields': ('last_reset', 'created_at', 'updated_at')
        }),
    )


@admin.register(AICreditTransaction)
class AICreditTransactionAdmin(BaseModelAdmin, ExportMixin):
    export_fields = ['company', 'type', 'amount', 'balance_after', 'user', 'created_at', 'description']
    """Admin para transações de créditos"""
    list_display = [
        'company', 'type', 'amount_formatted', 'balance_after',
        'user', 'created_at'
    ]
    list_filter = ['type', 'created_at']
    search_fields = [
        'company__name', 'description', 'user__email',
        'payment_id'
    ]
    readonly_fields = [
        'company', 'type', 'amount', 'balance_before',
        'balance_after', 'user', 'conversation', 'message',
        'payment_id', 'created_at'
    ]
    
    def amount_formatted(self, obj):
        """Formata quantidade com cor"""
        color = 'green' if obj.amount > 0 else 'red'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            f"{obj.amount:+d}"
        )
    amount_formatted.short_description = 'Quantidade'
    
    fieldsets = (
        ('Transação', {
            'fields': (
                'company', 'type', 'amount', 'description'
            )
        }),
        ('Saldos', {
            'fields': ('balance_before', 'balance_after')
        }),
        ('Referências', {
            'fields': (
                'user', 'conversation', 'message', 'payment_id'
            )
        }),
        ('Metadados', {
            'fields': ('metadata', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Não permite adicionar manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Não permite editar"""
        return False


@admin.register(AIConversation)
class AIConversationAdmin(BaseModelAdmin):
    """Admin para conversas"""
    list_display = [
        'title', 'company', 'user', 'status', 'message_count',
        'total_credits_used', 'created_at', 'last_message_at'
    ]
    list_filter = ['status', 'created_at', 'last_message_at']
    search_fields = ['title', 'company__name', 'user__email']
    readonly_fields = [
        'message_count', 'total_credits_used', 'insights_generated',
        'created_at', 'updated_at', 'last_message_at'
    ]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('company', 'user', 'title', 'status')
        }),
        ('Métricas', {
            'fields': (
                'message_count', 'total_credits_used',
                'insights_generated'
            )
        }),
        ('Contexto', {
            'fields': ('financial_context', 'settings'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at', 'last_message_at'
            )
        }),
    )
    
    def get_queryset(self, request):
        """Otimiza queries"""
        return super().get_queryset(request).select_related(
            'company', 'user'
        )


class AIMessageInline(admin.TabularInline):
    """Inline para mensagens em conversas"""
    model = AIMessage
    extra = 0
    fields = ['role', 'type', 'content', 'credits_used', 'created_at']
    readonly_fields = fields
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AIMessage)
class AIMessageAdmin(BaseModelAdmin):
    """Admin para mensagens"""
    list_display = [
        'conversation', 'role', 'type', 'content_preview',
        'credits_used', 'helpful', 'created_at'
    ]
    list_filter = ['role', 'type', 'helpful', 'created_at']
    search_fields = ['content', 'conversation__title']
    readonly_fields = [
        'conversation', 'role', 'type', 'content',
        'credits_used', 'tokens_used', 'model_used',
        'structured_data', 'insights', 'created_at'
    ]
    
    def content_preview(self, obj):
        """Preview do conteúdo"""
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Conteúdo'
    
    fieldsets = (
        ('Mensagem', {
            'fields': (
                'conversation', 'role', 'type', 'content'
            )
        }),
        ('Uso de AI', {
            'fields': (
                'credits_used', 'tokens_used', 'model_used'
            )
        }),
        ('Dados Estruturados', {
            'fields': ('structured_data', 'insights'),
            'classes': ('collapse',)
        }),
        ('Feedback', {
            'fields': ('helpful', 'user_feedback')
        }),
        ('Metadados', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        """Não permite adicionar manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Permite apenas editar feedback"""
        return True


@admin.register(AIInsight)
class AIInsightAdmin(BaseModelAdmin, ExportMixin, StatusColorMixin):
    """Admin para insights"""
    list_display = [
        'title', 'company', 'type', 'priority_badge',
        'status_badge', 'potential_impact', 'action_taken',
        'created_at'
    ]
    list_filter = [
        'type', 'priority', 'status', 'action_taken',
        'is_automated', 'created_at'
    ]
    search_fields = ['title', 'description', 'company__name']
    readonly_fields = [
        'company', 'conversation', 'message', 'created_at',
        'viewed_at', 'action_taken_at'
    ]
    
    def priority_badge(self, obj):
        """Badge de prioridade"""
        colors = {
            'critical': 'red',
            'high': 'orange',
            'medium': 'blue',
            'low': 'gray'
        }
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 2px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.priority, 'gray'),
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Prioridade'
    
    def status_badge(self, obj):
        """Badge de status"""
        colors = {
            'new': 'blue',
            'viewed': 'gray',
            'in_progress': 'orange',
            'completed': 'green',
            'dismissed': 'red'
        }
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 2px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    fieldsets = (
        ('Identificação', {
            'fields': (
                'company', 'type', 'priority', 'status',
                'title', 'description'
            )
        }),
        ('Ações Sugeridas', {
            'fields': ('action_items',)
        }),
        ('Impacto', {
            'fields': (
                'potential_impact', 'impact_percentage',
                'actual_impact'
            )
        }),
        ('Contexto', {
            'fields': (
                'data_context', 'is_automated',
                'conversation', 'message'
            ),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': (
                'action_taken', 'action_taken_at',
                'user_feedback', 'created_at',
                'viewed_at', 'expires_at'
            )
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_dismissed']
    
    def mark_as_completed(self, request, queryset):
        """Marca insights como concluídos"""
        count = queryset.update(
            status='completed',
            action_taken=True,
            action_taken_at=timezone.now()
        )
        self.message_user(
            request,
            f'{count} insights marcados como concluídos.'
        )
    mark_as_completed.short_description = 'Marcar como concluído'
    
    def mark_as_dismissed(self, request, queryset):
        """Marca insights como descartados"""
        count = queryset.update(status='dismissed')
        self.message_user(
            request,
            f'{count} insights descartados.'
        )
    mark_as_dismissed.short_description = 'Descartar insights'
    
    def get_queryset(self, request):
        """Otimiza queries"""
        return super().get_queryset(request).select_related(
            'company', 'conversation'
        )