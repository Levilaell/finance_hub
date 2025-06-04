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
    is_email_verified = models.BooleanField(_('email verified'), default=False)
    is_phone_verified = models.BooleanField(_('phone verified'), default=False)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', blank=True, null=True)
    date_of_birth = models.DateField(_('date of birth'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    last_login_ip = models.GenericIPAddressField(_('last login IP'), blank=True, null=True)
    
    # Business preferences
    preferred_language = models.CharField(
        _('preferred language'),
        max_length=10,
        choices=[('pt-br', 'Português'), ('en', 'English')],
        default='pt-br'
    )
    timezone = models.CharField(
        _('timezone'),
        max_length=50,
        default='America/Sao_Paulo'
    )
    
    # 2FA settings
    is_two_factor_enabled = models.BooleanField(_('2FA enabled'), default=False)
    two_factor_secret = models.CharField(_('2FA secret'), max_length=32, blank=True)
    backup_codes = models.JSONField(_('backup codes'), default=list, blank=True)
    
    # Payment fields
    payment_customer_id = models.CharField(_('payment customer ID'), max_length=255, blank=True, null=True)
    payment_gateway = models.CharField(_('payment gateway'), max_length=50, blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def initials(self):
        """Get user initials for avatar placeholder"""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.username[:2].upper()


class EmailVerification(models.Model):
    """
    Email verification tokens
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    token = models.CharField(_('verification token'), max_length=100, unique=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'))
    is_used = models.BooleanField(_('is used'), default=False)
    
    class Meta:
        db_table = 'email_verifications'
        verbose_name = _('Email Verification')
        verbose_name_plural = _('Email Verifications')
    
    def __str__(self):
        return f"Verification for {self.user.email}"


class PasswordReset(models.Model):
    """
    Password reset tokens
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(_('reset token'), max_length=100, unique=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'))
    is_used = models.BooleanField(_('is used'), default=False)
    
    class Meta:
        db_table = 'password_resets'
        verbose_name = _('Password Reset')
        verbose_name_plural = _('Password Resets')
    
    def __str__(self):
        return f"Password reset for {self.user.email}"