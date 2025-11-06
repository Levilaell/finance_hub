from django.contrib import admin
from .models import AIInsightConfig, AIInsight


@admin.register(AIInsightConfig)
class AIInsightConfigAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_enabled', 'enabled_at', 'last_generated_at']
    list_filter = ['is_enabled', 'enabled_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ['user', 'health_score', 'health_status', 'period_start', 'period_end', 'generated_at', 'has_error']
    list_filter = ['health_status', 'has_error', 'generated_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['generated_at', 'tokens_used', 'model_version', 'analysis_data']

    fieldsets = (
        ('User & Period', {
            'fields': ('user', 'period_start', 'period_end')
        }),
        ('Health Analysis', {
            'fields': ('health_score', 'health_status', 'summary')
        }),
        ('Insights', {
            'fields': ('alerts', 'opportunities', 'predictions', 'recommendations')
        }),
        ('Metadata', {
            'fields': ('generated_at', 'tokens_used', 'model_version', 'has_error', 'error_message')
        }),
        ('Analysis Data', {
            'fields': ('analysis_data',),
            'classes': ('collapse',)
        })
    )
