from django.contrib import admin
from .models import SubscriptionPlan, Subscription, PaymentMethod, Payment, UsageRecord


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'price_monthly', 'price_yearly', 'is_active']
    list_filter = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'display_name', 'is_active')
        }),
        ('Pricing', {
            'fields': ('price_monthly', 'price_yearly')
        }),
        ('Limits', {
            'fields': ('max_transactions', 'max_bank_accounts', 'max_ai_requests')
        }),
        ('Features', {
            'fields': ('features',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['company', 'plan', 'status', 'billing_period', 'trial_ends_at', 'current_period_end']
    list_filter = ['status', 'billing_period', 'plan']
    search_fields = ['company__name', 'stripe_subscription_id']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Company & Plan', {
            'fields': ('company', 'plan', 'billing_period')
        }),
        ('Status', {
            'fields': ('status', 'trial_ends_at', 'current_period_start', 
                      'current_period_end', 'cancelled_at')
        }),
        ('Payment Gateway', {
            'fields': ('stripe_subscription_id', 'stripe_customer_id')
                      # 'mercadopago_subscription_id' - Removed with MercadoPago integration
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['company', 'amount', 'currency', 'status', 'gateway', 'created_at']
    list_filter = ['status', 'gateway', 'currency']
    search_fields = ['company__name', 'description', 'stripe_payment_intent_id']
    readonly_fields = ['created_at', 'updated_at', 'paid_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Payment Info', {
            'fields': ('company', 'subscription', 'amount', 'currency', 
                      'status', 'description')
        }),
        ('Gateway Info', {
            'fields': ('gateway', 'payment_method', 'stripe_payment_intent_id',
                      'stripe_invoice_id')
                      # 'mercadopago_payment_id' - Removed with MercadoPago integration
        }),
        ('Metadata', {
            'fields': ('metadata', 'paid_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ['company', 'type', 'count', 'period_start', 'period_end']
    list_filter = ['type']
    search_fields = ['company__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'period_start'