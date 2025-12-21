"""
Subscription models
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.authentication.models import User


class AcquisitionTracking(models.Model):
    """
    Rastreia aquisições de assinaturas com o ângulo de marketing.
    Criado automaticamente quando uma subscription é criada via webhook.
    """
    ACQUISITION_ANGLES = [
        ('time', 'Tempo - Economia de horas'),
        ('price', 'Preço - Custo-benefício'),
        ('delay', 'Atraso - Evitar multas'),
        ('visibility', 'Visibilidade - Controle financeiro'),
        ('organic', 'Orgânico - Sem campanha'),
        ('unknown', 'Desconhecido'),
    ]

    SUBSCRIPTION_STATUS = [
        ('trialing', 'Trial'),
        ('active', 'Ativa'),
        ('past_due', 'Atrasada'),
        ('canceled', 'Cancelada'),
        ('unpaid', 'Não paga'),
        ('incomplete', 'Incompleta'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='acquisition_tracking'
    )

    # Dados capturados no momento da aquisição
    acquisition_angle = models.CharField(
        _('ângulo de aquisição'),
        max_length=50,
        choices=ACQUISITION_ANGLES,
        default='unknown',
        db_index=True
    )
    signup_price_id = models.CharField(
        _('price ID do signup'),
        max_length=100,
        blank=True,
        null=True
    )

    # Status atual da assinatura (sincronizado)
    subscription_status = models.CharField(
        _('status da assinatura'),
        max_length=20,
        choices=SUBSCRIPTION_STATUS,
        default='trialing',
        db_index=True
    )
    stripe_subscription_id = models.CharField(
        _('Stripe subscription ID'),
        max_length=100,
        blank=True,
        null=True
    )

    # Datas importantes
    trial_started_at = models.DateTimeField(_('início do trial'), null=True, blank=True)
    trial_ended_at = models.DateTimeField(_('fim do trial'), null=True, blank=True)
    converted_at = models.DateTimeField(_('data da conversão'), null=True, blank=True, help_text='Quando passou de trial para ativa')
    canceled_at = models.DateTimeField(_('data do cancelamento'), null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('atualizado em'), auto_now=True)

    class Meta:
        db_table = 'acquisition_tracking'
        verbose_name = _('Rastreamento de Aquisição')
        verbose_name_plural = _('Rastreamentos de Aquisição')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['acquisition_angle', 'subscription_status']),
            models.Index(fields=['subscription_status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_acquisition_angle_display()} ({self.get_subscription_status_display()})"

    @property
    def is_converted(self):
        """Retorna True se o usuário converteu de trial para pago"""
        return self.converted_at is not None

    @property
    def is_active(self):
        """Retorna True se a assinatura está ativa ou em trial"""
        return self.subscription_status in ['trialing', 'active']


class TrialUsageTracking(models.Model):
    """Track if user has already used trial period"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='trial_tracking'
    )
    has_used_trial = models.BooleanField(default=False)
    first_trial_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'trial_usage_tracking'

    def __str__(self):
        return f"{self.user.email} - Trial used: {self.has_used_trial}"
