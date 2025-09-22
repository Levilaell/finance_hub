"""
Django Admin configuration for company models
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin interface for Companies"""
    list_display = (
        'name',
        'cnpj',
        'owner_email',
        'company_type',
        'business_sector',
        'is_active',
        'created_at'
    )
    list_filter = (
        'company_type',
        'business_sector',
        'is_active',
        'created_at'
    )
    search_fields = (
        'name',
        'cnpj',
        'owner__email',
        'owner__first_name',
        'owner__last_name'
    )
    raw_id_fields = ('owner',)
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        (_('Company Information'), {
            'fields': ('name', 'owner', 'cnpj', 'company_type', 'business_sector', 'is_active')
        }),
        (_('System Info'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_companies', 'deactivate_companies']
    
    def owner_email(self, obj):
        return obj.owner.email if obj.owner else '-'
    owner_email.short_description = _('Owner Email')
    owner_email.admin_order_field = 'owner__email'
    
    def activate_companies(self, request, queryset):
        """Activate selected companies"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} empresa(s) ativada(s) com sucesso.'
        )
    activate_companies.short_description = _('Activate selected companies')
    
    def deactivate_companies(self, request, queryset):
        """Deactivate selected companies"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} empresa(s) desativada(s) com sucesso.'
        )
    deactivate_companies.short_description = _('Deactivate selected companies')