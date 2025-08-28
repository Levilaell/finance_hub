"""
Simplified notification system models
Focused on reliability, scalability, and essential functionality
"""
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import logging

from .constants import (
    MAX_NOTIFICATION_RETRIES,
    RETRY_DELAY_MINUTES,
    UNREAD_COUNT_CACHE_TIMEOUT,
    RECENT_NOTIFICATIONS_CACHE_TIMEOUT,
    RECENT_NOTIFICATIONS_LIMIT,
    CRITICAL_EVENTS
)

User = get_user_model()
logger = logging.getLogger(__name__)


class Notification(models.Model):
    """
    Simplified notification model with reliability and scalability features
    """
    # Core notification events - mapped to is_critical flag
    NOTIFICATION_EVENTS = [
        # Critical events (is_critical=True)
        ('account_sync_failed', _('Account Sync Failed')),
        ('payment_failed', _('Payment Failed')),
        ('low_balance', _('Low Balance Alert')),
        ('security_alert', _('Security Alert')),
        
        # Normal events (is_critical=False)
        ('account_connected', _('Account Connected')),
        ('large_transaction', _('Large Transaction')),
        ('report_ready', _('Report Ready')),
        ('payment_success', _('Payment Successful')),
        ('sync_completed', _('Sync Completed')),
    ]
    
    # Simplified delivery status
    DELIVERY_STATUS = [
        ('pending', _('Pending')),
        ('delivered', _('Delivered')),
        ('failed', _('Failed')),
    ]
    
    # Core relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True
    )
    
    # Event-based notification system
    event = models.CharField(
        _('event'),
        max_length=50,
        choices=NOTIFICATION_EVENTS,
        default='sync_completed',  # Add default for migration
        db_index=True,
        help_text='The event that triggered this notification'
    )
    is_critical = models.BooleanField(
        _('is critical'),
        default=False,
        db_index=True,
        help_text='Critical notifications require immediate attention'
    )
    title = models.CharField(_('title'), max_length=200)
    message = models.TextField(_('message'))
    
    # Deduplication and tracking
    event_key = models.CharField(
        _('event key'),
        max_length=255,
        unique=True,
        blank=True,
        null=True,  # Allow null temporarily for migration
        help_text='Unique key for deduplication (event:id:user)'
    )
    
    # Simplified context
    metadata = models.JSONField(
        _('metadata'),
        default=dict,
        help_text='Event-specific metadata'
    )
    action_url = models.URLField(
        _('action URL'),
        max_length=500,
        blank=True,
        help_text='URL for user action'
    )
    
    # Status tracking
    is_read = models.BooleanField(_('is read'), default=False, db_index=True)
    read_at = models.DateTimeField(_('read at'), blank=True, null=True)
    
    # Delivery reliability
    delivery_status = models.CharField(
        _('delivery status'),
        max_length=20,
        choices=DELIVERY_STATUS,
        default='pending',
        db_index=True
    )
    delivered_at = models.DateTimeField(_('delivered at'), blank=True, null=True)
    retry_count = models.PositiveSmallIntegerField(_('retry count'), default=0)
    last_retry_at = models.DateTimeField(_('last retry at'), blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            # Optimized for common queries
            models.Index(fields=['company', 'user', 'is_read', '-created_at']),
            models.Index(fields=['company', 'user', 'delivery_status']),
            models.Index(fields=['is_critical', 'is_read', '-created_at']),
            models.Index(fields=['event', 'created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['event_key'],
                name='unique_notification_event_key'
            )
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def mark_as_read(self):
        """Mark notification as read with cache invalidation."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])
            self._invalidate_cache()
    
    def mark_as_delivered(self):
        """Mark notification as successfully delivered."""
        self.delivery_status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['delivery_status', 'delivered_at', 'updated_at'])
    
    def mark_as_failed(self):
        """Mark notification delivery as failed."""
        self.delivery_status = 'failed'
        self.save(update_fields=['delivery_status', 'updated_at'])
    
    def increment_retry(self):
        """Increment retry count for failed deliveries."""
        self.retry_count += 1
        self.last_retry_at = timezone.now()
        self.save(update_fields=['retry_count', 'last_retry_at', 'updated_at'])
    
    def should_retry(self):
        """Check if notification should be retried."""
        if self.retry_count >= MAX_NOTIFICATION_RETRIES:
            return False
        
        if self.last_retry_at:
            time_since_retry = timezone.now() - self.last_retry_at
            if time_since_retry.total_seconds() < (RETRY_DELAY_MINUTES * 60):
                return False
        
        return self.delivery_status == 'failed'
    
    def _invalidate_cache(self):
        """Invalidate related caches."""
        cache_keys = [
            f'notifications:unread_count:{self.company_id}:{self.user_id}',
            f'notifications:recent:{self.company_id}:{self.user_id}',
        ]
        cache.delete_many(cache_keys)
    
    @classmethod
    def create_from_event(cls, event_name, company, user, title=None, message=None, 
                         metadata=None, action_url=None, event_id=None):
        """
        Factory method to create notifications from events with deduplication.
        """
        # Use critical events from constants
        
        # Default messages if not provided
        DEFAULT_MESSAGES = {
            'account_sync_failed': (_('Account Sync Failed'), _('Failed to sync your account')),
            'payment_failed': (_('Payment Failed'), _('Your payment could not be processed')),
            'low_balance': (_('Low Balance Alert'), _('Your account balance is below the threshold')),
            'security_alert': (_('Security Alert'), _('Unusual activity detected')),
            'account_connected': (_('Account Connected'), _('New account successfully connected')),
            'large_transaction': (_('Large Transaction'), _('A large transaction was detected')),
            'report_ready': (_('Report Ready'), _('Your report is ready for download')),
            'payment_success': (_('Payment Successful'), _('Payment processed successfully')),
            'sync_completed': (_('Sync Completed'), _('Account sync completed')),
        }
        
        # Generate unique event key for deduplication
        event_key = f"{event_name}:{event_id or 'none'}:{user.id}:{company.id}"
        
        # Get default title/message if not provided
        if not title or not message:
            default_title, default_message = DEFAULT_MESSAGES.get(
                event_name, 
                (_('Notification'), _('You have a new notification'))
            )
            title = title or default_title
            message = message or default_message
        
        # Atomic get_or_create to prevent race condition constraint violations
        try:
            notification, created = cls.objects.get_or_create(
                event_key=event_key,
                defaults={
                    'company': company,
                    'user': user,
                    'event': event_name,
                    'is_critical': event_name in CRITICAL_EVENTS,
                    'title': str(title),
                    'message': str(message),
                    'metadata': metadata or {},
                    'action_url': action_url or '',
                }
            )
            
            if created:
                logger.info(f"Notification created for event key: {event_key}")
                return notification
            else:
                logger.info(f"Notification already exists for event key: {event_key}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            return None
    
    @classmethod
    def get_unread_count(cls, company, user):
        """Get unread notification count with caching."""
        cache_key = f'notifications:unread_count:{company.id}:{user.id}'
        count = cache.get(cache_key)
        
        if count is None:
            count = cls.objects.filter(
                company=company,
                user=user,
                is_read=False
            ).count()
            cache.set(cache_key, count, timeout=UNREAD_COUNT_CACHE_TIMEOUT)
        
        return count
    
    @classmethod
    def get_recent_notifications(cls, company, user, limit=10):
        """Get recent notifications with caching."""
        cache_key = f'notifications:recent:{company.id}:{user.id}'
        notifications = cache.get(cache_key)
        
        if notifications is None:
            notifications = list(cls.objects.filter(
                company=company,
                user=user
            ).select_related('company', 'user')[:limit])
            cache.set(cache_key, notifications, timeout=RECENT_NOTIFICATIONS_CACHE_TIMEOUT)
        
        return notifications