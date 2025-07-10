"""
Reports app admin configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import Report, ReportSchedule, ReportTemplate


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'company', 'report_type', 'period_display',
        'generation_status', 'created_by', 'created_at'
    ]
    list_filter = [
        'report_type', 'file_format', 'is_generated',
        'created_at'
    ]
    search_fields = ['title', 'company__name', 'created_by__email']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('company', 'title', 'description', 'report_type')
        }),
        ('Período', {
            'fields': ('period_start', 'period_end')
        }),
        ('Parâmetros e Filtros', {
            'fields': ('parameters', 'filters'),
            'classes': ('collapse',)
        }),
        ('Arquivo Gerado', {
            'fields': ('file_format', 'file', 'file_size', 'is_generated', 
                      'generation_time', 'error_message')
        }),
        ('Metadados', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'file_size', 'generation_time']
    
    def period_display(self, obj):
        return f"{obj.period_start.strftime('%d/%m/%Y')} - {obj.period_end.strftime('%d/%m/%Y')}"
    period_display.short_description = 'Período'
    
    def generation_status(self, obj):
        if obj.is_generated:
            return format_html(
                '<span style="color: green;">✓ Gerado</span>'
            )
        elif obj.error_message:
            return format_html(
                '<span style="color: red;">✗ Erro</span>'
            )
        else:
            return format_html(
                '<span style="color: orange;">⏳ Pendente</span>'
            )
    generation_status.short_description = 'Status'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company', 'created_by')
    
    actions = ['regenerate_reports', 'download_reports']
    
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
        # Implementar lógica de download múltiplo
        count = queryset.filter(is_generated=True).count()
        self.message_user(request, f'{count} relatórios disponíveis para download.')
    download_reports.short_description = 'Download relatórios'


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'company', 'report_type', 'frequency',
        'is_active', 'last_run_display', 'next_run_display'
    ]
    list_filter = ['frequency', 'is_active', 'report_type']
    search_fields = ['company__name']
    
    fieldsets = (
        ('Configuração', {
            'fields': ('company', 'report_type', 'frequency', 'is_active')
        }),
        ('Entrega', {
            'fields': ('send_email', 'email_recipients', 'file_format')
        }),
        ('Parâmetros', {
            'fields': ('parameters', 'filters'),
            'classes': ('collapse',)
        }),
        ('Execução', {
            'fields': ('next_run_at', 'last_run_at')
        }),
        ('Metadados', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['last_run_at', 'created_at']
    
    def last_run_display(self, obj):
        if obj.last_run_at:
            return obj.last_run_at.strftime('%d/%m/%Y %H:%M')
        return 'Nunca executado'
    last_run_display.short_description = 'Última execução'
    
    def next_run_display(self, obj):
        if obj.next_run_at:
            return obj.next_run_at.strftime('%d/%m/%Y %H:%M')
        return 'N/A'
    next_run_display.short_description = 'Próxima execução'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company', 'created_by')
    
    actions = ['activate_schedules', 'deactivate_schedules', 'run_now']
    
    def activate_schedules(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} agendamentos ativados.')
    activate_schedules.short_description = 'Ativar agendamentos'
    
    def deactivate_schedules(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} agendamentos desativados.')
    deactivate_schedules.short_description = 'Desativar agendamentos'
    
    def run_now(self, request, queryset):
        count = 0
        for schedule in queryset.filter(is_active=True):
            # Trigger report generation task
            count += 1
        self.message_user(request, f'{count} relatórios agendados para execução imediata.')
    run_now.short_description = 'Executar agora'


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'company', 'report_type',
        'is_active', 'is_public', 'created_at'
    ]
    list_filter = ['report_type', 'is_active', 'is_public']
    search_fields = ['name', 'description', 'company__name']
    ordering = ['company', 'name']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('company', 'name', 'description', 'report_type')
        }),
        ('Configuração do Template', {
            'fields': ('template_config', 'charts')
        }),
        ('Parâmetros Padrão', {
            'fields': ('default_parameters', 'default_filters'),
            'classes': ('collapse',)
        }),
        ('Controle de Acesso', {
            'fields': ('is_active', 'is_public')
        }),
        ('Metadados', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company', 'created_by')
    
    actions = ['duplicate_template', 'make_public', 'make_private']
    
    def duplicate_template(self, request, queryset):
        count = 0
        for template in queryset:
            template.pk = None
            template.name = f"{template.name} (Cópia)"
            template.is_public = False
            template.save()
            count += 1
        self.message_user(request, f'{count} templates duplicados.')
    duplicate_template.short_description = 'Duplicar templates'
    
    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} templates tornados públicos.')
    make_public.short_description = 'Tornar público'
    
    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} templates tornados privados.')
    make_private.short_description = 'Tornar privado'