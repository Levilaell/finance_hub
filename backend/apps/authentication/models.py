"""
User authentication models
Custom user model with enhanced features for financial SaaS
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

    payment_gateway = models.CharField(
        _('payment gateway'),
        max_length=50,
        choices=[
            ('stripe', 'Stripe'),
            ('mercadopago', 'MercadoPago'),
        ],
        blank=True,
        null=True,
        help_text='Gateway de pagamento utilizado'
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