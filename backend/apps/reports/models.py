"""
Reports app models
Financial reporting and analytics
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

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
        ('tax_report', 'Relatório Fiscal'),
        ('custom', 'Personalizado'),
    ]
    
    FILE_FORMATS = [
        ('pdf', 'PDF'),
        ('xlsx', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
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
    
    # Generated files
    file_format = models.CharField(_('file format'), max_length=10, choices=FILE_FORMATS)
    file = models.FileField(_('report file'), upload_to='reports/%Y/%m/', blank=True, null=True)
    file_size = models.IntegerField(_('file size'), default=0)
    
    # Status
    is_generated = models.BooleanField(_('is generated'), default=False)
    generation_time = models.IntegerField(_('generation time (seconds)'), default=0)
    error_message = models.TextField(_('error message'), blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
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
    
    def __str__(self):
        return f"{self.title} ({self.period_start} - {self.period_end})"


class ReportSchedule(models.Model):
    """
    Scheduled report generation
    """
    FREQUENCY_CHOICES = [
        ('daily', 'Diário'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensal'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual'),
    ]
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='report_schedules'
    )
    
    # Schedule configuration
    report_type = models.CharField(_('report type'), max_length=20, choices=Report.REPORT_TYPES)
    frequency = models.CharField(_('frequency'), max_length=20, choices=FREQUENCY_CHOICES)
    
    # Delivery settings
    send_email = models.BooleanField(_('send by email'), default=True)
    email_recipients = models.JSONField(_('email recipients'), default=list)
    file_format = models.CharField(_('file format'), max_length=10, choices=Report.FILE_FORMATS, default='pdf')
    
    # Schedule settings
    is_active = models.BooleanField(_('is active'), default=True)
    next_run_at = models.DateTimeField(_('next run at'))
    last_run_at = models.DateTimeField(_('last run at'), blank=True, null=True)
    
    # Report parameters
    parameters = models.JSONField(_('parameters'), default=dict)
    filters = models.JSONField(_('filters'), default=dict)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_schedules'
    )
    
    class Meta:
        db_table = 'report_schedules'
        verbose_name = _('Report Schedule')
        verbose_name_plural = _('Report Schedules')
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.get_frequency_display()}"


class ReportTemplate(models.Model):
    """
    Custom report templates
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='report_templates'
    )
    
    name = models.CharField(_('template name'), max_length=200)
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
    
    def __str__(self):
        return self.name