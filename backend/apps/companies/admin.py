"""
Django Admin configuration for company models
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import SubscriptionPlan, Company


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """Admin interface for Subscription Plans"""
    list_display = (
        'name',
        'plan_type',
        'price_monthly_formatted',
        'price_yearly_formatted',
        'trial_days',
        'max_bank_accounts',
        'is_active',
        'display_order'
    )
    list_filter = (
        'plan_type',
        'is_active',
        'trial_days',
        'created_at'
    )
    search_fields = ('name', 'slug', 'plan_type')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'price_monthly']
    list_editable = ('display_order', 'is_active')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'slug', 'plan_type', 'trial_days')
        }),
        (_('Pricing'), {
            'fields': ('price_monthly', 'price_yearly')
        }),
        (_('Limits'), {
            'fields': ('max_bank_accounts',)
        }),
        (_('Payment Gateway Integration'), {
            'fields': ('stripe_price_id_monthly', 'stripe_price_id_yearly'),
            'classes': ('collapse',),
            'description': 'Stripe Price IDs for payment processing'
        }),
        (_('Display Settings'), {
            'fields': ('display_order', 'is_active')
        }),
        (_('System Info'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def price_monthly_formatted(self, obj):
        return f"R$ {obj.price_monthly:,.2f}"
    price_monthly_formatted.short_description = _('Monthly Price')
    price_monthly_formatted.admin_order_field = 'price_monthly'
    
    def price_yearly_formatted(self, obj):
        return f"R$ {obj.price_yearly:,.2f}"
    price_yearly_formatted.short_description = _('Yearly Price')
    price_yearly_formatted.admin_order_field = 'price_yearly'


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin interface for Companies"""
    list_display = (
        'name',
        'owner_email',
        'subscription_plan',
        'subscription_status_display',
        'billing_cycle',
        'trial_status',
        'current_month_transactions',
        'bank_accounts_count',
        'is_active',
        'created_at'
    )
    list_filter = (
        'subscription_status',
        'billing_cycle',
        'subscription_plan',
        'is_active',
        'created_at',
        'trial_ends_at'
    )
    search_fields = (
        'name',
        'owner__email',
        'owner__first_name',
        'owner__last_name',
        'subscription_id'
    )
    raw_id_fields = ('owner',)
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = (
        'created_at',
        'updated_at',
        'trial_status_info',
        'subscription_details',
        'usage_statistics',
        'bank_accounts_info'
    )
    
    fieldsets = (
        (_('Company Information'), {
            'fields': ('name', 'owner', 'is_active')
        }),
        (_('Subscription'), {
            'fields': (
                'subscription_plan',
                'subscription_status',
                'billing_cycle',
                'subscription_id',
                'subscription_details'
            )
        }),
        (_('Trial Information'), {
            'fields': ('trial_ends_at', 'trial_status_info'),
            'classes': ('collapse',)
        }),
        (_('Usage & Limits'), {
            'fields': (
                'current_month_transactions',
                'usage_statistics',
                'bank_accounts_info'
            )
        }),
        (_('System Info'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_companies', 'deactivate_companies', 'reset_monthly_usage']
    
    def owner_email(self, obj):
        return obj.owner.email if obj.owner else '-'
    owner_email.short_description = _('Owner Email')
    owner_email.admin_order_field = 'owner__email'
    
    def subscription_status_display(self, obj):
        status_colors = {
            'trial': '#FFA500',  # Orange
            'active': '#008000',  # Green
            'cancelled': '#FF0000',  # Red
            'expired': '#808080',  # Gray
        }
        color = status_colors.get(obj.subscription_status, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_subscription_status_display()
        )
    subscription_status_display.short_description = _('Status')
    subscription_status_display.admin_order_field = 'subscription_status'
    
    def trial_status(self, obj):
        if obj.subscription_status != 'trial':
            return '-'
        
        if obj.is_trial_active:
            days_left = obj.days_until_trial_ends
            if days_left <= 3:
                color = '#FF0000'  # Red for urgent
            elif days_left <= 7:
                color = '#FFA500'  # Orange for warning
            else:
                color = '#008000'  # Green for ok
            
            return format_html(
                '<span style="color: {};">{} days left</span>',
                color,
                days_left
            )
        else:
            return format_html(
                '<span style="color: #FF0000;">Expired</span>'
            )
    trial_status.short_description = _('Trial Status')
    
    def trial_status_info(self, obj):
        if obj.subscription_status != 'trial':
            return 'Not in trial'
        
        if obj.is_trial_active:
            return f"Active - {obj.days_until_trial_ends} days remaining (ends {obj.trial_ends_at.strftime('%Y-%m-%d %H:%M')})"
        else:
            return f"Expired on {obj.trial_ends_at.strftime('%Y-%m-%d %H:%M')}" if obj.trial_ends_at else "No trial set"
    trial_status_info.short_description = _('Trial Details')
    
    def bank_accounts_count(self, obj):
        active_count = obj.bank_accounts.filter(is_active=True).count()
        total_count = obj.bank_accounts.count()
        max_allowed = obj.subscription_plan.max_bank_accounts if obj.subscription_plan else 0
        
        if active_count >= max_allowed and max_allowed > 0:
            color = '#FF0000'  # Red if at limit
        else:
            color = '#008000'  # Green if under limit
        
        return format_html(
            '<span style="color: {};">{}/{} (max: {})</span>',
            color,
            active_count,
            total_count,
            max_allowed
        )
    bank_accounts_count.short_description = _('Bank Accounts')
    
    def subscription_details(self, obj):
        if not obj.subscription_plan:
            return "No plan selected"
        
        plan = obj.subscription_plan
        if obj.billing_cycle == 'monthly':
            price = f"R$ {plan.price_monthly:,.2f}/month"
        else:
            price = f"R$ {plan.price_yearly:,.2f}/year"
        
        details = f"Plan: {plan.name}\n"
        details += f"Price: {price}\n"
        details += f"Max Bank Accounts: {plan.max_bank_accounts}\n"
        
        if obj.subscription_id:
            details += f"Stripe ID: {obj.subscription_id}"
        
        return details
    subscription_details.short_description = _('Subscription Details')
    
    def usage_statistics(self, obj):
        stats = f"Transactions this month: {obj.current_month_transactions:,}\n"
        
        # Add more usage stats if available
        active_accounts = obj.bank_accounts.filter(is_active=True).count()
        stats += f"Active bank accounts: {active_accounts}\n"
        
        if hasattr(obj, 'pluggy_items'):
            active_items = obj.pluggy_items.filter(status='UPDATED').count()
            stats += f"Active Pluggy connections: {active_items}"
        
        return stats
    usage_statistics.short_description = _('Usage Statistics')
    
    def bank_accounts_info(self, obj):
        accounts = obj.bank_accounts.filter(is_active=True)
        if not accounts.exists():
            return "No active bank accounts"
        
        info = []
        for account in accounts[:5]:  # Show max 5 accounts
            info.append(f"• {account.display_name} ({account.type})")
        
        if accounts.count() > 5:
            info.append(f"... and {accounts.count() - 5} more")
        
        return "\n".join(info)
    bank_accounts_info.short_description = _('Active Bank Accounts')
    
    def activate_companies(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} companies activated.')
    activate_companies.short_description = _('Activate selected companies')
    
    def deactivate_companies(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} companies deactivated.')
    deactivate_companies.short_description = _('Deactivate selected companies')
    
    def reset_monthly_usage(self, request, queryset):
        updated = queryset.update(current_month_transactions=0)
        self.message_user(request, f'Monthly usage reset for {updated} companies.')
    reset_monthly_usage.short_description = _('Reset monthly transaction count')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Optimize queries with select_related and prefetch_related
        return qs.select_related('owner', 'subscription_plan').prefetch_related('bank_accounts')