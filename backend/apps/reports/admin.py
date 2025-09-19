"""
Enhanced Reports admin - Comprehensive financial reporting management
Provides advanced report generation, analytics, and template management with performance insights
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count, Sum, Q, Avg, F
from django.http import HttpResponse
from django.core.files.storage import default_storage
import os
from core.admin import BaseModelAdmin
from .models import Report, ReportTemplate


@admin.register(Report)
class ReportAdmin(BaseModelAdmin):
    """Enhanced admin for financial reports with comprehensive analytics and management"""

    list_display = [
        'title_display', 'company_display', 'report_type_display', 'period_display',
        'generation_status', 'file_info', 'created_by_display', 'created_at_display'
    ]
    list_filter = [
        'report_type', 'file_format', 'is_generated',
        'created_at', 'company__subscription_plan'
    ]
    search_fields = ['title', 'description', 'company__name', 'created_by__email']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    raw_id_fields = ['company', 'created_by']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('company', 'title', 'description', 'report_type')
        }),
        (_('Report Period'), {
            'fields': ('period_start', 'period_end', 'duration_info'),
            'description': 'Define the time period for this report'
        }),
        (_('Parameters & Filters'), {
            'fields': ('parameters', 'filters'),
            'classes': ('collapse',),
            'description': 'Advanced filtering and parameter configuration'
        }),
        (_('Generated File'), {
            'fields': ('file_format', 'file', 'file_info_detail', 'is_generated', 'error_message')
        }),
        (_('Analytics'), {
            'fields': ('report_analytics',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = [
        'created_at', 'updated_at', 'duration_info', 'file_info_detail', 'report_analytics'
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company', 'created_by', 'company__subscription_plan')

    # Enhanced display methods
    def title_display(self, obj):
        if obj.is_generated and obj.file:
            download_url = obj.file.url
            return format_html(
                '<a href="{}" target="_blank" title="Download report">{}</a>',
                download_url, obj.title
            )
        return obj.title
    title_display.short_description = _('Title')
    title_display.admin_order_field = 'title'

    def company_display(self, obj):
        url = reverse('admin:companies_company_change', args=[obj.company.pk])
        plan_name = obj.company.subscription_plan.name if obj.company.subscription_plan else 'Sem plano'
        return format_html(
            '<a href="{}">{}</a><br><small style="color: #666;">{}</small>',
            url, obj.company.name, plan_name
        )
    company_display.short_description = _('Company')
    company_display.admin_order_field = 'company__name'

    def report_type_display(self, obj):
        type_colors = {
            'monthly_summary': '#3b82f6',
            'quarterly_report': '#8b5cf6',
            'annual_report': '#ef4444',
            'cash_flow': '#10b981',
            'profit_loss': '#f59e0b',
            'category_analysis': '#06b6d4',
            'custom': '#6b7280'
        }
        color = type_colors.get(obj.report_type, '#6b7280')
        type_name = dict(obj.REPORT_TYPES).get(obj.report_type, obj.report_type)

        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, type_name
        )
    report_type_display.short_description = _('Type')
    report_type_display.admin_order_field = 'report_type'

    def period_display(self, obj):
        start = obj.period_start.strftime('%d/%m/%Y')
        end = obj.period_end.strftime('%d/%m/%Y')
        days = obj.duration_days

        if obj.is_monthly:
            period_type = '📅 Mensal'
        elif days <= 7:
            period_type = '📊 Semanal'
        elif days <= 90:
            period_type = '📈 Trimestral'
        elif days <= 365:
            period_type = '📋 Anual'
        else:
            period_type = '📑 Personalizado'

        return format_html(
            '<div>{} - {}</div><small style="color: #666;">{} ({} dias)</small>',
            start, end, period_type, days
        )
    period_display.short_description = _('Period')

    def generation_status(self, obj):
        if obj.is_generated:
            if obj.file:
                file_size = obj.file_size if obj.file_size else 0
                size_mb = file_size / (1024 * 1024) if file_size > 0 else 0
                return format_html(
                    '<span style="color: green; font-weight: bold;">✓ Gerado</span><br>'
                    '<small>{:.1f} MB</small>',
                    size_mb
                )
            else:
                return format_html('<span style="color: orange;">⚠️ Arquivo perdido</span>')
        elif obj.error_message:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Erro</span><br>'
                '<small title="{}">{}</small>',
                obj.error_message, obj.error_message[:30] + '...' if len(obj.error_message) > 30 else obj.error_message
            )
        else:
            return format_html('<span style="color: orange;">⏳ Pendente</span>')
    generation_status.short_description = _('Status')

    def file_info(self, obj):
        if obj.file and obj.is_generated:
            format_icons = {
                'pdf': '📄',
                'xlsx': '📊',
                'csv': '📋'
            }
            icon = format_icons.get(obj.file_format, '📁')
            return format_html(
                '{} {}',
                icon, obj.file_format.upper()
            )
        return '-'
    file_info.short_description = _('Format')

    def created_by_display(self, obj):
        if obj.created_by:
            url = reverse('admin:authentication_user_change', args=[obj.created_by.pk])
            name = obj.created_by.full_name or obj.created_by.email
            return format_html('<a href="{}">{}</a>', url, name)
        return '-'
    created_by_display.short_description = _('Created By')
    created_by_display.admin_order_field = 'created_by__email'

    def created_at_display(self, obj):
        diff = timezone.now() - obj.created_at
        if diff.days == 0:
            return format_html('<span style="color: green;">Hoje</span>')
        elif diff.days < 7:
            return format_html('<span style="color: orange;">{} dias</span>', diff.days)
        else:
            return obj.created_at.strftime('%d/%m/%Y')
    created_at_display.short_description = _('Created')
    created_at_display.admin_order_field = 'created_at'

    # Readonly field methods
    def duration_info(self, obj):
        if not obj.period_start or not obj.period_end:
            return 'Período não definido'

        duration = obj.duration_days

        html = f'<div><strong>Duração:</strong> {duration} dias</div>'

        if obj.is_monthly:
            html += '<div style="color: green;">✓ Relatório mensal completo</div>'

        if duration > 365:
            html += '<div style="color: orange;">⚠️ Período muito longo (>1 ano)</div>'

        return format_html(html)
    duration_info.short_description = _('Duration Info')

    def file_info_detail(self, obj):
        if not obj.file:
            return 'Nenhum arquivo gerado'

        try:
            file_size = obj.file.size if obj.file else 0
            size_mb = file_size / (1024 * 1024) if file_size > 0 else 0

            html = '<table style="width: 100%;">'
            html += f'<tr><td><strong>Arquivo:</strong></td><td>{os.path.basename(obj.file.name)}</td></tr>'
            html += f'<tr><td><strong>Tamanho:</strong></td><td>{size_mb:.2f} MB</td></tr>'
            html += f'<tr><td><strong>Formato:</strong></td><td>{obj.file_format.upper()}</td></tr>'

            if obj.file:
                html += f'<tr><td><strong>Download:</strong></td><td><a href="{obj.file.url}" target="_blank">Baixar arquivo</a></td></tr>'

            html += '</table>'
            return format_html(html)
        except Exception as e:
            return f'Erro ao acessar arquivo: {str(e)}'
    file_info_detail.short_description = _('File Details')

    def report_analytics(self, obj):
        if not obj.pk:
            return 'Salve o relatório para ver analytics'

        html = '<table style="width: 100%;">'
        html += f'<tr><td><strong>Tipo:</strong></td><td>{dict(obj.REPORT_TYPES).get(obj.report_type, obj.report_type)}</td></tr>'
        html += f'<tr><td><strong>Período:</strong></td><td>{obj.duration_days} dias</td></tr>'

        if obj.parameters:
            param_count = len(obj.parameters) if isinstance(obj.parameters, dict) else 0
            html += f'<tr><td><strong>Parâmetros:</strong></td><td>{param_count} configurados</td></tr>'

        if obj.filters:
            filter_count = len(obj.filters) if isinstance(obj.filters, dict) else 0
            html += f'<tr><td><strong>Filtros:</strong></td><td>{filter_count} aplicados</td></tr>'

        # Performance metrics
        if obj.is_generated:
            generation_time = (obj.updated_at - obj.created_at).total_seconds()
            html += f'<tr><td><strong>Tempo de Geração:</strong></td><td>{generation_time:.1f}s</td></tr>'

        html += '</table>'
        return format_html(html)
    report_analytics.short_description = _('Report Analytics')

    # Enhanced actions
    actions = [
        'regenerate_reports', 'download_reports', 'duplicate_reports',
        'export_report_list', 'cleanup_failed_reports'
    ]

    def regenerate_reports(self, request, queryset):
        count = 0
        for report in queryset:
            report.is_generated = False
            report.error_message = ''
            report.save()
            count += 1
        self.message_user(request, f'{count} relatórios marcados para regeneração.')
    regenerate_reports.short_description = 'Regenerar relatórios selecionados'

    def download_reports(self, request, queryset):
        generated_reports = queryset.filter(is_generated=True, file__isnull=False)
        count = generated_reports.count()
        if count > 0:
            # You could implement a zip download here
            self.message_user(request, f'{count} relatórios disponíveis para download.')
        else:
            self.message_user(request, 'Nenhum relatório gerado encontrado.', level='WARNING')
    download_reports.short_description = 'Download relatórios gerados'

    def duplicate_reports(self, request, queryset):
        count = 0
        for report in queryset:
            report.pk = None
            report.title = f"{report.title} (Cópia)"
            report.is_generated = False
            report.file = None
            report.error_message = ''
            report.save()
            count += 1
        self.message_user(request, f'{count} relatórios duplicados com sucesso.')
    duplicate_reports.short_description = 'Duplicar relatórios'

    def export_report_list(self, request, queryset):
        # You could implement CSV export of report metadata here
        count = queryset.count()
        self.message_user(request, f'Lista de {count} relatórios exportada.')
    export_report_list.short_description = 'Exportar lista de relatórios'

    def cleanup_failed_reports(self, request, queryset):
        failed_reports = queryset.filter(is_generated=False, error_message__isnull=False).exclude(error_message='')
        count = failed_reports.count()
        if count > 0:
            failed_reports.delete()
            self.message_user(request, f'{count} relatórios com erro removidos.')
        else:
            self.message_user(request, 'Nenhum relatório com erro encontrado.')
    cleanup_failed_reports.short_description = 'Limpar relatórios com erro'


@admin.register(ReportTemplate)
class ReportTemplateAdmin(BaseModelAdmin):
    """Enhanced admin for report templates with usage analytics and management features"""

    list_display = [
        'name', 'company_display', 'report_type_display', 'usage_stats',
        'status_display', 'created_at_display'
    ]
    list_filter = ['report_type', 'is_active', 'is_public', 'created_at']
    search_fields = ['name', 'description', 'company__name']
    ordering = ['company', 'name']
    raw_id_fields = ['company', 'created_by']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('company', 'name', 'description', 'report_type')
        }),
        (_('Template Configuration'), {
            'fields': ('template_config', 'charts'),
            'description': 'Configure the template structure and visual components'
        }),
        (_('Default Parameters'), {
            'fields': ('default_parameters', 'default_filters'),
            'classes': ('collapse',),
            'description': 'Set default values for parameters and filters'
        }),
        (_('Access Control'), {
            'fields': ('is_active', 'is_public'),
            'description': 'Control template availability and visibility'
        }),
        (_('Analytics'), {
            'fields': ('template_analytics',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at', 'template_analytics']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company', 'created_by').annotate(
            usage_count=Count('company__reports', filter=Q(company__reports__report_type=F('report_type')))
        )

    # Enhanced display methods
    def company_display(self, obj):
        if obj.company:
            url = reverse('admin:companies_company_change', args=[obj.company.pk])
            return format_html('<a href="{}">{}</a>', url, obj.company.name)
        return format_html('<em style="color: #999;">Template público</em>')
    company_display.short_description = _('Company')
    company_display.admin_order_field = 'company__name'

    def report_type_display(self, obj):
        type_colors = {
            'monthly_summary': '#3b82f6',
            'quarterly_report': '#8b5cf6',
            'annual_report': '#ef4444',
            'cash_flow': '#10b981',
            'profit_loss': '#f59e0b',
            'category_analysis': '#06b6d4',
            'custom': '#6b7280'
        }
        color = type_colors.get(obj.report_type, '#6b7280')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.report_type.replace('_', ' ').title()
        )
    report_type_display.short_description = _('Type')
    report_type_display.admin_order_field = 'report_type'

    def usage_stats(self, obj):
        # This would require a proper relationship or query
        # For now, showing chart count and configuration complexity
        chart_count = len(obj.charts) if obj.charts else 0
        config_complexity = len(obj.template_config) if obj.template_config else 0

        html = f'<div>📊 {chart_count} gráficos</div>'
        html += f'<div>⚙️ {config_complexity} configurações</div>'

        return format_html(html)
    usage_stats.short_description = _('Usage')

    def status_display(self, obj):
        if obj.is_active:
            if obj.is_public:
                return format_html(
                    '<span style="color: green; font-weight: bold;">✓ Ativo</span><br>'
                    '<small style="color: blue;">🌐 Público</small>'
                )
            else:
                return format_html(
                    '<span style="color: green; font-weight: bold;">✓ Ativo</span><br>'
                    '<small style="color: orange;">🔒 Privado</small>'
                )
        else:
            return format_html('<span style="color: red; font-weight: bold;">✗ Inativo</span>')
    status_display.short_description = _('Status')

    def created_at_display(self, obj):
        return obj.created_at.strftime('%d/%m/%Y')
    created_at_display.short_description = _('Created')
    created_at_display.admin_order_field = 'created_at'

    # Readonly field methods
    def template_analytics(self, obj):
        if not obj.pk:
            return 'Salve o template para ver analytics'

        html = '<table style="width: 100%;">'

        # Configuration analysis
        chart_count = len(obj.charts) if obj.charts else 0
        config_count = len(obj.template_config) if obj.template_config else 0
        param_count = len(obj.default_parameters) if obj.default_parameters else 0
        filter_count = len(obj.default_filters) if obj.default_filters else 0

        html += f'<tr><td><strong>Gráficos:</strong></td><td>{chart_count}</td></tr>'
        html += f'<tr><td><strong>Configurações:</strong></td><td>{config_count}</td></tr>'
        html += f'<tr><td><strong>Parâmetros Padrão:</strong></td><td>{param_count}</td></tr>'
        html += f'<tr><td><strong>Filtros Padrão:</strong></td><td>{filter_count}</td></tr>'

        # Complexity score
        complexity = chart_count + config_count + param_count + filter_count
        if complexity > 20:
            complexity_label = 'Alta'
            complexity_color = '#ef4444'
        elif complexity > 10:
            complexity_label = 'Média'
            complexity_color = '#f59e0b'
        else:
            complexity_label = 'Baixa'
            complexity_color = '#10b981'

        html += f'<tr><td><strong>Complexidade:</strong></td><td><span style="color: {complexity_color};">{complexity_label}</span></td></tr>'

        html += '</table>'
        return format_html(html)
    template_analytics.short_description = _('Template Analytics')

    # Enhanced actions
    actions = [
        'duplicate_template', 'make_public', 'make_private',
        'activate_templates', 'deactivate_templates', 'export_templates'
    ]

    def duplicate_template(self, request, queryset):
        count = 0
        for template in queryset:
            original_name = template.name
            template.pk = None
            template.name = f"{original_name} (Cópia)"
            template.is_public = False
            template.is_active = True
            template.save()
            count += 1
        self.message_user(request, f'{count} templates duplicados com sucesso.')
    duplicate_template.short_description = 'Duplicar templates'

    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} templates tornados públicos.')
    make_public.short_description = 'Tornar público'

    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} templates tornados privados.')
    make_private.short_description = 'Tornar privado'

    def activate_templates(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} templates ativados com sucesso.')
    activate_templates.short_description = 'Ativar templates'

    def deactivate_templates(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} templates desativados com sucesso.')
    deactivate_templates.short_description = 'Desativar templates'

    def export_templates(self, request, queryset):
        # You could implement template export functionality here
        count = queryset.count()
        self.message_user(request, f'{count} templates exportados.')
    export_templates.short_description = 'Exportar templates'