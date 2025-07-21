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
    file_format = models.CharField(_('file format'), max_length=10, choices=FILE_FORMATS, default='pdf')
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


class AIAnalysis(models.Model):
    """
    AI-generated financial analyses
    """
    ANALYSIS_TYPES = [
        ('financial_health', 'Saúde Financeira'),
        ('cash_flow_prediction', 'Previsão de Fluxo de Caixa'),
        ('expense_optimization', 'Otimização de Gastos'),
        ('revenue_analysis', 'Análise de Receita'),
        ('risk_assessment', 'Avaliação de Riscos'),
        ('investment_advice', 'Consultoria de Investimento'),
        ('custom_query', 'Consulta Personalizada'),
        ('general_insights', 'Insights Gerais'),
    ]
    
    # Identification
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='ai_analyses'
    )
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    
    # Analysis type
    analysis_type = models.CharField(
        _('analysis type'), 
        max_length=30, 
        choices=ANALYSIS_TYPES,
        default='general_insights'
    )
    
    # Analysis period
    period_start = models.DateField(_('period start'))
    period_end = models.DateField(_('period end'))
    
    # Configuration
    analysis_config = models.JSONField(_('analysis configuration'), default=dict)
    input_parameters = models.JSONField(_('input parameters'), default=dict)
    filters = models.JSONField(_('filters'), default=dict)
    
    # AI Results
    ai_response = models.JSONField(_('AI response'), default=dict)
    insights = models.JSONField(_('insights'), default=list)
    recommendations = models.JSONField(_('recommendations'), default=list)
    predictions = models.JSONField(_('predictions'), default=dict)
    summary = models.JSONField(_('summary'), default=dict)
    
    # Metrics and Scores
    confidence_score = models.FloatField(_('confidence score'), default=0.0)
    health_score = models.FloatField(_('health score'), null=True, blank=True)
    risk_score = models.FloatField(_('risk score'), null=True, blank=True)
    
    # Status and control
    is_processed = models.BooleanField(_('is processed'), default=False)
    processing_time = models.IntegerField(_('processing time (seconds)'), default=0)
    error_message = models.TextField(_('error message'), blank=True)
    
    # Cache and invalidation
    cache_key = models.CharField(_('cache key'), max_length=255, blank=True)
    expires_at = models.DateTimeField(_('expires at'), null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_ai_analyses'
    )
    
    # Access and sharing
    is_public = models.BooleanField(_('is public'), default=False)
    is_favorite = models.BooleanField(_('is favorite'), default=False)
    tags = models.JSONField(_('tags'), default=list)
    
    class Meta:
        db_table = 'ai_analyses'
        verbose_name = _('AI Analysis')
        verbose_name_plural = _('AI Analyses')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'analysis_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['cache_key']),
            models.Index(fields=['is_favorite']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.period_start} - {self.period_end})"


class AIAnalysisTemplate(models.Model):
    """
    Templates for reusable AI analyses
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='ai_analysis_templates'
    )
    name = models.CharField(_('template name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    
    # Template configuration
    analysis_type = models.CharField(
        _('analysis type'), 
        max_length=30, 
        choices=AIAnalysis.ANALYSIS_TYPES
    )
    template_config = models.JSONField(_('template configuration'), default=dict)
    prompt_template = models.TextField(_('prompt template'))
    default_parameters = models.JSONField(_('default parameters'), default=dict)
    default_filters = models.JSONField(_('default filters'), default=dict)
    
    # Output configuration
    output_format = models.JSONField(_('output format'), default=dict)
    visualization_config = models.JSONField(_('visualization configuration'), default=list)
    
    # Control
    is_active = models.BooleanField(_('is active'), default=True)
    is_public = models.BooleanField(_('is public'), default=False)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_ai_templates'
    )
    
    class Meta:
        db_table = 'ai_analysis_templates'
        verbose_name = _('AI Analysis Template')
        verbose_name_plural = _('AI Analysis Templates')
        ordering = ['name']
    
    def __str__(self):
        return self.name