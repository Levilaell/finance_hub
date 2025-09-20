"""
Reports app models
Financial reporting and analytics
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()


class Report(models.Model):
    """
    Generated financial reports
    """
    REPORT_TYPES = [
        ('monthly_summary', 'Resumo Mensal'),
        ('quarterly_report', 'Relatório Trimestral'),
        ('annual_report', 'Relatório Anual'),
        ('cash_flow', 'Fluxo de Caixa'),
        ('profit_loss', 'DRE - Demonstração de Resultados'),
        ('category_analysis', 'Análise por Categoria'),
        ('custom', 'Personalizado'),
    ]
    
    FILE_FORMATS = [
        ('pdf', 'PDF'),
        ('xlsx', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    # Report identification
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='reports'
    )
    report_type = models.CharField(_('report type'), max_length=20, choices=REPORT_TYPES)
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    
    # Report period
    period_start = models.DateField(_('period start'))
    period_end = models.DateField(_('period end'))
    
    # Report parameters
    parameters = models.JSONField(_('parameters'), default=dict)
    filters = models.JSONField(_('filters'), default=dict)
    
    # Generated file
    file = models.FileField(_('report file'), upload_to='reports/%Y/%m/', null=True, blank=True)
    file_format = models.CharField(_('file format'), max_length=10, choices=FILE_FORMATS, default='pdf')
    file_size = models.IntegerField(_('file size'), default=0)
    
    # Status
    is_generated = models.BooleanField(_('is generated'), default=False)
    error_message = models.TextField(_('error message'), blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_reports'
    )
    
    class Meta:
        db_table = 'reports'
        verbose_name = _('Report')
        verbose_name_plural = _('Reports')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'report_type', 'created_at']),
            models.Index(fields=['period_start', 'period_end']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.company.name}"
    
    def clean(self):
        """Validate report data"""
        if self.period_start and self.period_end:
            if self.period_start > self.period_end:
                raise ValidationError({
                    'period_end': _('End date must be after start date.')
                })
            
            if self.period_end > timezone.now().date():
                raise ValidationError({
                    'period_end': _('End date cannot be in the future.')
                })
            
            # Validate period is not too long (1 year max)
            delta = self.period_end - self.period_start
            if delta.days > 365:
                raise ValidationError({
                    'period_end': _('Report period cannot exceed 1 year.')
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ReportTemplate(models.Model):
    """
    Custom report templates
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='report_templates'
    )
    
    name = models.CharField(_('template name'), max_length=200, db_index=True)
    description = models.TextField(_('description'), blank=True)
    
    # Template configuration
    report_type = models.CharField(_('report type'), max_length=20, default='custom')
    template_config = models.JSONField(_('template configuration'), default=dict)
    
    # Chart and visualization settings
    charts = models.JSONField(_('charts configuration'), default=list)
    
    # Default parameters
    default_parameters = models.JSONField(_('default parameters'), default=dict)
    default_filters = models.JSONField(_('default filters'), default=dict)
    
    # Settings
    is_public = models.BooleanField(_('is public'), default=False)
    is_active = models.BooleanField(_('is active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_templates'
    )
    
    class Meta:
        db_table = 'report_templates'
        verbose_name = _('Report Template')
        verbose_name_plural = _('Report Templates')
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['report_type', 'is_public']),
        ]
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate template data"""
        if not self.template_config:
            self.template_config = {}
        
        if not self.charts:
            self.charts = []
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)



