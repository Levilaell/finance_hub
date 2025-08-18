"""
Simplified Companies admin - Essential functionality only
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Company, SubscriptionPlan, ResourceUsage, EarlyAccessInvite
from core.admin import BaseModelAdmin


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(BaseModelAdmin):
    list_display = ['name', 'price_monthly', 'price_yearly', 'max_transactions', 'max_bank_accounts', 'is_active']
    list_filter = ['is_active']
    ordering = ['display_order', 'price_monthly']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'plan_type', 'trial_days', 'display_order', 'is_active')
        }),
        ('Pricing', {
            'fields': ('price_monthly', 'price_yearly')
        }),
        ('Limits', {
            'fields': ('max_transactions', 'max_bank_accounts', 'max_ai_requests_per_month')
        }),
        ('Features', {
            'fields': ('has_ai_categorization', 'enable_ai_insights', 'enable_ai_reports', 
                      'has_advanced_reports', 'has_api_access', 'has_accountant_access', 
                      'has_priority_support')
        }),
        ('Payment Gateway', {
            'fields': ('stripe_price_id_monthly', 'stripe_price_id_yearly', 'mercadopago_plan_id'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Company)
class CompanyAdmin(BaseModelAdmin):
    list_display = ['name', 'owner_email', 'subscription_plan', 'subscription_status', 'is_early_access', 'trial_days', 'created_at']
    list_filter = ['subscription_status', 'subscription_plan', 'is_early_access', 'created_at']
    search_fields = ['name', 'owner__email', 'used_invite_code']
    readonly_fields = ['created_at', 'trial_days', 'usage_summary']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('owner', 'name', 'is_active')
        }),
        ('Subscription', {
            'fields': ('subscription_plan', 'subscription_status', 'billing_cycle', 'trial_ends_at', 'subscription_id')
        }),
        ('Early Access', {
            'fields': ('is_early_access', 'early_access_expires_at', 'used_invite_code'),
            'classes': ('collapse',)
        }),
        ('Usage', {
            'fields': ('current_month_transactions', 'current_month_ai_requests', 'usage_summary')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def owner_email(self, obj):
        return obj.owner.email
    owner_email.short_description = 'Owner Email'
    owner_email.admin_order_field = 'owner__email'
    
    def trial_days(self, obj):
        if obj.is_early_access and obj.early_access_expires_at:
            days = obj.days_until_trial_ends
            if days > 0:
                return format_html('<span style="color: purple;">Early Access: {} days</span>', days)
            else:
                return format_html('<span style="color: red;">Early Access Expired</span>')
        
        days = obj.days_until_trial_ends
        if days > 0:
            return format_html('<span style="color: green;">{} days</span>', days)
        elif obj.subscription_status == 'trial':
            return format_html('<span style="color: red;">Expired</span>')
        return '-'
    trial_days.short_description = 'Trial/Early Access Days'
    
    def usage_summary(self, obj):
        if not obj.subscription_plan:
            return 'No plan'
        
        html = '<table style="width: 100%;">'
        html += f'<tr><td>Transactions:</td><td>{obj.current_month_transactions}/{obj.subscription_plan.max_transactions}</td></tr>'
        html += f'<tr><td>AI Requests:</td><td>{obj.current_month_ai_requests}/{obj.subscription_plan.max_ai_requests_per_month}</td></tr>'
        html += '</table>'
        return format_html(html)
    usage_summary.short_description = 'Current Month Usage'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('owner', 'subscription_plan')


@admin.register(EarlyAccessInvite)
class EarlyAccessInviteAdmin(BaseModelAdmin):
    list_display = ['invite_code', 'is_used', 'used_by_email', 'expires_at', 'days_remaining', 'created_at']
    list_filter = ['is_used', 'expires_at', 'created_at']
    search_fields = ['invite_code', 'used_by__email', 'notes']
    readonly_fields = ['used_at', 'created_at', 'days_remaining']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Convite', {
            'fields': ('invite_code', 'expires_at', 'notes')
        }),
        ('Status', {
            'fields': ('is_used', 'used_by', 'used_at', 'days_remaining')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def used_by_email(self, obj):
        if obj.used_by:
            return obj.used_by.email
        return '-'
    used_by_email.short_description = 'Used By'
    used_by_email.admin_order_field = 'used_by__email'
    
    def days_remaining(self, obj):
        days = obj.days_until_expiry
        if obj.is_used:
            return format_html('<span style="color: orange;">Used</span>')
        elif days > 0:
            return format_html('<span style="color: green;">{} days</span>', days)
        else:
            return format_html('<span style="color: red;">Expired</span>')
    days_remaining.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('used_by', 'created_by')


@admin.register(ResourceUsage)
class ResourceUsageAdmin(BaseModelAdmin):
    list_display = ['company', 'month', 'transactions_count', 'ai_requests_count', 'created_at']
    list_filter = ['month', 'created_at']
    search_fields = ['company__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'month'