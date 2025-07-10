"""
Notifications app admin configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import NotificationTemplate, Notification, NotificationPreference, NotificationLog


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'notification_type', 'send_email', 
        'send_push', 'send_sms', 'is_active'
    ]
    list_filter = ['notification_type', 'send_email', 'send_push', 'send_sms', 'is_active']
    search_fields = ['name', 'title_template', 'message_template']
    ordering = ['notification_type', 'name']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'notification_type')
        }),
        ('Conteúdo', {
            'fields': ('title_template', 'message_template')
        }),
        ('Canais de Notificação', {
            'fields': ('send_email', 'send_push', 'send_sms')
        }),
        ('Configurações', {
            'fields': ('is_active', 'is_system'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_system:
            return self.readonly_fields + ['notification_type', 'is_system']
        return self.readonly_fields


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title_truncated', 'user', 'notification_type',
        'priority', 'is_read', 'created_at'
    ]
    list_filter = [
        'notification_type', 'priority', 'is_read',
        'email_sent', 'push_sent', 'created_at'
    ]
    search_fields = ['title', 'message', 'user__email']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Destinatário', {
            'fields': ('user', 'company')
        }),
        ('Conteúdo', {
            'fields': ('title', 'message', 'notification_type', 'priority', 'action_url')
        }),
        ('Template e Dados', {
            'fields': ('template', 'data'),
            'classes': ('collapse',)
        }),
        ('Status de Leitura', {
            'fields': ('is_read', 'read_at')
        }),
        ('Status de Envio', {
            'fields': (
                ('email_sent', 'email_sent_at'),
                ('push_sent', 'push_sent_at'),
                ('sms_sent', 'sms_sent_at')
            )
        }),
        ('Metadados', {
            'fields': ('created_at', 'expires_at')
        }),
    )
    
    readonly_fields = [
        'created_at', 'read_at', 'email_sent_at', 
        'push_sent_at', 'sms_sent_at'
    ]
    
    def title_truncated(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_truncated.short_description = 'Título'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'company', 'template')
    
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
            # Reset send status
            notification.email_sent = False
            notification.push_sent = False
            notification.sms_sent = False
            notification.save()
            count += 1
        self.message_user(request, f'{count} notificações preparadas para reenvio.')
    resend_notification.short_description = 'Reenviar notificação'


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'email_enabled', 'push_enabled', 
        'sms_enabled', 'send_daily_digest', 'send_weekly_digest'
    ]
    list_filter = [
        'email_enabled', 'push_enabled', 'sms_enabled',
        'send_daily_digest', 'send_weekly_digest'
    ]
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user',)
        }),
        ('Canais de Notificação', {
            'fields': ('email_enabled', 'push_enabled', 'sms_enabled')
        }),
        ('Preferências de Tipo', {
            'fields': ('type_preferences',),
            'classes': ('collapse',)
        }),
        ('Horários', {
            'fields': ('quiet_hours_start', 'quiet_hours_end')
        }),
        ('Resumos por Email', {
            'fields': ('send_daily_digest', 'send_weekly_digest', 'digest_time')
        }),
        ('Limites', {
            'fields': ('low_balance_threshold', 'large_transaction_threshold')
        }),
    )
    
    readonly_fields = ['updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        'notification_display', 'channel', 'success_status',
        'attempted_at', 'error_truncated'
    ]
    list_filter = ['channel', 'success', 'attempted_at']
    search_fields = ['notification__title', 'recipient', 'error_message']
    date_hierarchy = 'attempted_at'
    ordering = ['-attempted_at']
    
    fieldsets = (
        ('Notificação', {
            'fields': ('notification',)
        }),
        ('Tentativa de Envio', {
            'fields': ('channel', 'recipient', 'success', 'error_message')
        }),
        ('Informações do Provedor', {
            'fields': ('provider', 'provider_message_id'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('attempted_at',)
        }),
    )
    
    readonly_fields = ['attempted_at', 'notification']
    
    def notification_display(self, obj):
        return f"{obj.notification.title[:40]}..."
    notification_display.short_description = 'Notificação'
    
    def success_status(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓ Sucesso</span>')
        return format_html('<span style="color: red;">✗ Falha</span>')
    success_status.short_description = 'Status'
    
    def error_truncated(self, obj):
        if obj.error_message:
            return obj.error_message[:50] + '...' if len(obj.error_message) > 50 else obj.error_message
        return '-'
    error_truncated.short_description = 'Erro'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('notification', 'notification__user')
    
    def has_add_permission(self, request):
        # Logs são criados automaticamente
        return False
    
    def has_change_permission(self, request, obj=None):
        # Logs não devem ser editados
        return False