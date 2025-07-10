"""
Companies app admin configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import SubscriptionPlan, Company, CompanyUser


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'slug', 'plan_type', 
        'price_monthly', 'price_yearly',
        'max_users', 'max_bank_accounts', 'max_transactions',
        'has_ai_categorization', 'has_advanced_reports',
        'is_active'
    ]
    list_filter = ['plan_type', 'is_active', 'has_ai_categorization', 'has_advanced_reports']
    search_fields = ['name', 'slug']
    ordering = ['price_monthly']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'slug', 'plan_type', 'is_active')
        }),
        ('Preços', {
            'fields': ('price_monthly', 'price_yearly')
        }),
        ('Limites', {
            'fields': ('max_users', 'max_bank_accounts', 'max_transactions')
        }),
        ('Funcionalidades', {
            'fields': (
                'has_ai_categorization',
                'has_advanced_reports',
                'has_api_access',
                'has_accountant_access'
            )
        }),
    )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'owner_link', 'cnpj', 'subscription_plan',
        'subscription_status', 'trial_ends_at_display',
        'created_at'
    ]
    list_filter = [
        'subscription_status', 'subscription_plan',
        'company_type', 'business_sector', 'created_at'
    ]
    search_fields = ['name', 'cnpj', 'trade_name', 'owner__email', 'owner__first_name']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informações da Empresa', {
            'fields': (
                'owner', 'name', 'trade_name', 'cnpj',
                'company_type', 'business_sector'
            )
        }),
        ('Assinatura', {
            'fields': (
                'subscription_plan', 'subscription_status',
                'trial_ends_at', 'subscription_end_date'
            )
        }),
        ('Contato', {
            'fields': ('email', 'phone', 'website')
        }),
        ('Endereço', {
            'fields': (
                'address_street', 'address_number', 'address_complement',
                'address_neighborhood', 'address_city', 'address_state',
                'address_country', 'address_zip_code'
            ),
            'classes': ('collapse',)
        }),
        ('Configurações', {
            'fields': ('preferences', 'is_test_company'),
            'classes': ('collapse',)
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def owner_link(self, obj):
        url = reverse('admin:authentication_user_change', args=[obj.owner.pk])
        return format_html('<a href="{}">{}</a>', url, obj.owner.email)
    owner_link.short_description = 'Proprietário'
    
    def trial_ends_at_display(self, obj):
        if obj.trial_ends_at:
            days_left = (obj.trial_ends_at - timezone.now()).days
            if days_left > 0:
                return format_html(
                    '<span style="color: green;">{} ({} dias restantes)</span>',
                    obj.trial_ends_at.strftime('%d/%m/%Y'),
                    days_left
                )
            else:
                return format_html(
                    '<span style="color: red;">{} (expirado)</span>',
                    obj.trial_ends_at.strftime('%d/%m/%Y')
                )
        return '-'
    trial_ends_at_display.short_description = 'Trial expira em'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('owner', 'subscription_plan')


@admin.register(CompanyUser)
class CompanyUserAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'company_name', 'role', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'joined_at']
    search_fields = ['user__email', 'user__first_name', 'company__name']
    date_hierarchy = 'joined_at'
    ordering = ['-joined_at']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Usuário'
    
    def company_name(self, obj):
        return obj.company.name
    company_name.short_description = 'Empresa'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'company')