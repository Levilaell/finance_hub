"""
AI Insights Models
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class AIInsightConfig(models.Model):
    """
    Configuration for AI Insights per user.
    Stores whether the feature is enabled and when it was activated.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='ai_insight_config'
    )
    is_enabled = models.BooleanField(default=False)
    enabled_at = models.DateTimeField(null=True, blank=True)

    # Last generation tracking
    last_generated_at = models.DateTimeField(null=True, blank=True)
    next_scheduled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_insight_configs'
        verbose_name = 'AI Insight Configuration'
        verbose_name_plural = 'AI Insight Configurations'

    def __str__(self):
        return f"AI Config for {self.user.email} - {'Enabled' if self.is_enabled else 'Disabled'}"


class AIInsight(models.Model):
    """
    Stores generated AI insights for a user's financial data.
    """
    STATUS_CHOICES = [
        ('excellent', 'Excelente'),
        ('good', 'Bom'),
        ('regular', 'Regular'),
        ('poor', 'Ruim'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_insights'
    )

    # Health Score (0-10)
    health_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        help_text='Financial health score from 0 to 10'
    )
    health_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES
    )
    summary = models.TextField(help_text='Executive summary of the analysis')

    # Period analyzed
    period_start = models.DateField()
    period_end = models.DateField()

    # Structured insights (JSON)
    alerts = models.JSONField(
        default=list,
        help_text='List of alerts: [{type, severity, title, description, recommendation}]'
    )
    opportunities = models.JSONField(
        default=list,
        help_text='List of opportunities: [{type, severity, title, description, recommendation}]'
    )
    predictions = models.JSONField(
        default=dict,
        help_text='Predictions: {next_month_cash_flow, confidence, reasoning}'
    )
    recommendations = models.JSONField(
        default=list,
        help_text='Top recommendations as list of strings'
    )

    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    tokens_used = models.IntegerField(
        default=0,
        help_text='Number of tokens consumed by OpenAI API'
    )
    model_version = models.CharField(
        max_length=50,
        default='gpt-4o-mini',
        help_text='OpenAI model version used'
    )

    # Analysis data snapshot (for audit)
    analysis_data = models.JSONField(
        help_text='Snapshot of the data sent to AI for analysis'
    )

    # Error tracking
    has_error = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = 'ai_insights'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['user', '-generated_at']),
            models.Index(fields=['user', 'period_start', 'period_end']),
        ]

    def __str__(self):
        return f"Insight for {self.user.email} - {self.period_start} to {self.period_end}"

    @property
    def score_change(self):
        """
        Calculate score change compared to previous insight.
        Returns None if no previous insight exists.
        """
        previous = AIInsight.objects.filter(
            user=self.user,
            generated_at__lt=self.generated_at
        ).first()

        if previous:
            return self.health_score - previous.health_score
        return None

    @property
    def is_recent(self):
        """Check if insight is less than 7 days old."""
        return (timezone.now() - self.generated_at).days < 7
