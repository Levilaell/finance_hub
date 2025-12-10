"""
User authentication models
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom user model with additional fields for business owners
    """
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(_('phone number'), max_length=20, blank=True)
    last_login_ip = models.GenericIPAddressField(_('last login IP'), blank=True, null=True)
    
    # Timestamps - standardized naming
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    timezone = models.CharField(
        _('timezone'),
        max_length=50,
        default='America/Sao_Paulo'
    )

    # Price ID para teste A/B - salvo no registro para usar no checkout
    signup_price_id = models.CharField(
        _('signup price ID'),
        max_length=100,
        blank=True,
        null=True,
        help_text='Stripe Price ID da landing page onde o usuário se cadastrou'
    )

    class Meta:
        db_table = 'users'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def has_active_subscription(self):
        """
        Check if user has an active subscription via dj-stripe
        Returns True if subscription status is 'trialing', 'active', or 'past_due'

        Note: 'past_due' is included to give users grace period during payment retry attempts
        """
        try:
            from djstripe.models import Subscription
            return Subscription.objects.filter(
                customer__subscriber=self,
                status__in=['trialing', 'active', 'past_due']
            ).exists()
        except Exception:
            # If dj-stripe is not configured or error occurs, return False
            return False


class PasswordReset(models.Model):
    """
    Password reset tokens
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(_('reset token'), max_length=100, unique=True, db_index=True)
    is_used = models.BooleanField(_('is used'), default=False)

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'))

    class Meta:
        db_table = 'password_resets'
        verbose_name = _('Password Reset')
        verbose_name_plural = _('Password Resets')
        indexes = [
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Password reset for {self.user.email}"


class UserActivityLog(models.Model):
    """
    Tracks user login and activity events
    """
    EVENT_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('bank_connection_created', 'Bank Connection Created'),
        ('bank_connection_updated', 'Bank Connection Updated'),
        ('bank_connection_deleted', 'Bank Connection Deleted'),
        ('sync_started', 'Sync Started'),
        ('sync_completed', 'Sync Completed'),
        ('sync_failed', 'Sync Failed'),
        ('password_reset_requested', 'Password Reset Requested'),
        ('password_changed', 'Password Changed'),
        ('profile_updated', 'Profile Updated'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    event_type = models.CharField(_('event type'), max_length=50, choices=EVENT_TYPES, db_index=True)
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)

    # Additional context for the event
    metadata = models.JSONField(_('metadata'), default=dict, blank=True, help_text='Additional event data')

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'user_activity_logs'
        verbose_name = _('User Activity Log')
        verbose_name_plural = _('User Activity Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['user', 'event_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_event_type_display()} at {self.created_at}"

    @classmethod
    def log_event(cls, user, event_type, ip_address=None, user_agent=None, **metadata):
        """
        Convenience method to log an event

        Usage:
            UserActivityLog.log_event(
                user=request.user,
                event_type='login',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                success=True
            )
        """
        return cls.objects.create(
            user=user,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )


class UserSettings(models.Model):
    """
    User automation and behavior settings.
    Each user has one settings record (created automatically via signal).
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='settings',
        primary_key=True
    )

    # Automation settings
    auto_match_transactions = models.BooleanField(
        _('auto match transactions'),
        default=True,
        help_text='Automatically link transactions to bills when values match'
    )

    # Future automation settings (placeholders)
    # auto_categorize_transactions = models.BooleanField(default=True)
    # notify_overdue_bills = models.BooleanField(default=True)
    # notify_large_transactions = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'user_settings'
        verbose_name = _('User Settings')
        verbose_name_plural = _('User Settings')

    def __str__(self):
        return f"Settings for {self.user.email}"

    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create settings for a user."""
        settings, created = cls.objects.get_or_create(user=user)
        return settings