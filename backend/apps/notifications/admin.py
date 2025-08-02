"""
Notifications app admin configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title_truncated', 'user', 'event',
        'is_critical', 'is_read', 'created_at'
    ]
    list_filter = [
        'event', 'is_critical', 'is_read',
        'delivery_status', 'created_at'
    ]
    search_fields = ['title', 'message', 'user__email']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Destinatário', {
            'fields': ('user', 'company')
        }),
        ('Conteúdo', {
            'fields': ('title', 'message', 'event', 'is_critical', 'action_url')
        }), 
        ('Dados Adicionais', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Status de Leitura', {
            'fields': ('is_read', 'read_at')
        }),
        ('Status de Envio', {
            'fields': (
                'delivery_status',
                'delivered_at',
                'retry_count',
                'last_retry_at'
            )
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = [
        'created_at', 'updated_at', 'read_at', 
        'delivered_at', 'last_retry_at'
    ]
    
    def title_truncated(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_truncated.short_description = 'Título'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'company')
    
    actions = ['mark_as_read', 'mark_as_unread', 'resend_notification']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notificações marcadas como lidas.')
    mark_as_read.short_description = 'Marcar como lida'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notificações marcadas como não lidas.')
    mark_as_unread.short_description = 'Marcar como não lida'
    
    def resend_notification(self, request, queryset):
        count = 0
        for notification in queryset:
            # Reset delivery status
            notification.delivery_status = 'pending'
            notification.delivered_at = None
            notification.retry_count = 0
            notification.save()
            count += 1
        self.message_user(request, f'{count} notificações preparadas para reenvio.')
    resend_notification.short_description = 'Reenviar notificação'

