"""
Notifications app models
User notifications and alerts system
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


# NotificationTemplate model removed


class Notification(models.Model):
    """
    User notifications
    """
    NOTIFICATION_TYPES = [
        ('low_balance', 'Saldo Baixo'),
        ('large_transaction', 'Transação Grande'),
        ('recurring_payment', 'Pagamento Recorrente'),
        ('sync_error', 'Erro de Sincronização'),
        ('report_ready', 'Relatório Pronto'),
        ('subscription_expiring', 'Assinatura Expirando'),
        ('user_invited', 'Usuário Convidado'),
        ('budget_exceeded', 'Orçamento Excedido'),
        ('ai_insight', 'Insight IA'),
        ('custom', 'Personalizado'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    # Recipient
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='notifications',
        blank=True,
        null=True
    )
    
    # Notification content
    notification_type = models.CharField(_('notification type'), max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(_('title'), max_length=200)
    message = models.TextField(_('message'))
    
    # Additional data
    data = models.JSONField(_('additional data'), default=dict)
    action_url = models.CharField(_('action URL'), max_length=500, blank=True)
    
    # Status
    priority = models.CharField(_('priority'), max_length=10, choices=PRIORITY_LEVELS, default='medium')
    is_read = models.BooleanField(_('is read'), default=False)
    read_at = models.DateTimeField(_('read at'), blank=True, null=True)
    
    # Delivery status
    email_sent = models.BooleanField(_('email sent'), default=False)
    email_sent_at = models.DateTimeField(_('email sent at'), blank=True, null=True)
    push_sent = models.BooleanField(_('push sent'), default=False)
    push_sent_at = models.DateTimeField(_('push sent at'), blank=True, null=True)
    sms_sent = models.BooleanField(_('SMS sent'), default=False)
    sms_sent_at = models.DateTimeField(_('SMS sent at'), blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'), blank=True, null=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"


class NotificationPreference(models.Model):
    """
    User notification preferences
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Global settings
    email_enabled = models.BooleanField(_('email notifications'), default=True)
    push_enabled = models.BooleanField(_('push notifications'), default=True)
    sms_enabled = models.BooleanField(_('SMS notifications'), default=False)
    
    # Notification type preferences (JSON with notification_type as key)
    type_preferences = models.JSONField(_('type preferences'), default=dict)
    
    # Schedule preferences
    quiet_hours_start = models.TimeField(_('quiet hours start'), blank=True, null=True)
    quiet_hours_end = models.TimeField(_('quiet hours end'), blank=True, null=True)
    
    # Email digest settings
    send_daily_digest = models.BooleanField(_('send daily digest'), default=False)
    send_weekly_digest = models.BooleanField(_('send weekly digest'), default=True)
    digest_time = models.TimeField(_('digest time'), default='09:00')
    
    # Thresholds
    low_balance_threshold = models.DecimalField(
        _('low balance threshold'),
        max_digits=15,
        decimal_places=2,
        default=1000.00
    )
    large_transaction_threshold = models.DecimalField(
        _('large transaction threshold'),
        max_digits=15,
        decimal_places=2,
        default=5000.00
    )
    
    # Metadata
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
        verbose_name = _('Notification Preference')
        verbose_name_plural = _('Notification Preferences')
    
    def __str__(self):
        return f"Preferences for {self.user.email}"


# NotificationLog model removed