"""
Admin interface for subscriptions management
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from djstripe.models import Customer, Subscription, Price, Product
from apps.authentication.models import User
from .models import TrialUsageTracking

# Desregistrar os admins padrão do dj-stripe
admin.site.unregister(Customer)
admin.site.unregister(Subscription)
admin.site.unregister(Product)
admin.site.unregister(Price)


@admin.register(TrialUsageTracking)
class TrialUsageTrackingAdmin(admin.ModelAdmin):
    """Admin for trial usage tracking"""
    list_display = ['user_email', 'has_used_trial', 'first_trial_at', 'created_at']
    list_filter = ['has_used_trial', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['user', 'has_used_trial', 'first_trial_at', 'created_at']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    def has_add_permission(self, request):
        return False


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Custom admin for Stripe Customers"""
    list_display = ['id', 'subscriber_link', 'email', 'has_active_subscription', 'balance_display', 'created']
    list_filter = ['livemode', 'created']
    search_fields = ['id', 'email', 'subscriber__email', 'subscriber__name']
    readonly_fields = ['id', 'created', 'stripe_dashboard_link']

    def subscriber_link(self, obj):
        if obj.subscriber:
            url = reverse('admin:authentication_user_change', args=[obj.subscriber.id])
            return format_html('<a href="{}">{}</a>', url, obj.subscriber.email)
        return '-'
    subscriber_link.short_description = 'Usuário'

    def has_active_subscription(self, obj):
        from djstripe.models import Subscription
        active = Subscription.objects.filter(
            customer=obj,
            status__in=['active', 'trialing']
        ).exists()
        if active:
            return format_html('<span style="color: green;">✓ Ativa</span>')
        return format_html('<span style="color: red;">✗ Inativa</span>')
    has_active_subscription.short_description = 'Assinatura'

    def balance_display(self, obj):
        balance = obj.balance / 100 if obj.balance else 0
        color = 'red' if balance < 0 else 'green'
        balance_str = f'{balance:.2f}'
        return format_html('<span style="color: {};">R$ {}</span>', color, balance_str)
    balance_display.short_description = 'Saldo'

    def stripe_dashboard_link(self, obj):
        mode = '' if obj.livemode else 'test/'
        url = f'https://dashboard.stripe.com/{mode}customers/{obj.id}'
        return format_html('<a href="{}" target="_blank">Ver no Stripe Dashboard →</a>', url)
    stripe_dashboard_link.short_description = 'Stripe'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Custom admin for Stripe Subscriptions"""
    list_display = ['id', 'customer_link', 'status_badge', 'plan_display', 'trial_display', 'current_period_display', 'created']
    list_filter = ['status', 'livemode', 'cancel_at_period_end', 'created']
    search_fields = ['id', 'customer__email', 'customer__subscriber__email']
    readonly_fields = ['id', 'created', 'stripe_dashboard_link', 'cancel_url_display']

    def customer_link(self, obj):
        url = reverse('admin:djstripe_customer_change', args=[obj.customer.id])
        email = obj.customer.subscriber.email if obj.customer.subscriber else obj.customer.email
        return format_html('<a href="{}">{}</a>', url, email)
    customer_link.short_description = 'Cliente'

    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'trialing': 'blue',
            'past_due': 'orange',
            'canceled': 'red',
            'unpaid': 'red',
            'incomplete': 'gray',
        }
        labels = {
            'active': 'Ativa',
            'trialing': 'Trial',
            'past_due': 'Atrasada',
            'canceled': 'Cancelada',
            'unpaid': 'Não paga',
            'incomplete': 'Incompleta',
        }
        color = colors.get(obj.status, 'gray')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, label
        )
    status_badge.short_description = 'Status'

    def plan_display(self, obj):
        if obj.plan:
            amount = obj.plan.amount / 100 if obj.plan.amount else 0
            interval = {'month': 'mês', 'year': 'ano', 'week': 'semana', 'day': 'dia'}.get(obj.plan.interval, obj.plan.interval)
            return f'R$ {amount:.2f}/{interval}'
        return '-'
    plan_display.short_description = 'Plano'

    def trial_display(self, obj):
        if obj.trial_end:
            from django.utils import timezone
            now = timezone.now()
            if obj.trial_end > now:
                days = (obj.trial_end - now).days
                return format_html('<span style="color: blue;">Trial ({} dias)</span>', days)
            return format_html('<span style="color: gray;">Trial expirado</span>')
        return '-'
    trial_display.short_description = 'Trial'

    def current_period_display(self, obj):
        if obj.current_period_start and obj.current_period_end:
            return f'{obj.current_period_start.strftime("%d/%m/%Y")} → {obj.current_period_end.strftime("%d/%m/%Y")}'
        return '-'
    current_period_display.short_description = 'Período atual'

    def stripe_dashboard_link(self, obj):
        mode = '' if obj.livemode else 'test/'
        url = f'https://dashboard.stripe.com/{mode}subscriptions/{obj.id}'
        return format_html('<a href="{}" target="_blank">Ver no Stripe Dashboard →</a>', url)
    stripe_dashboard_link.short_description = 'Stripe'

    def cancel_url_display(self, obj):
        if obj.status in ['active', 'trialing']:
            return format_html(
                '<a href="#" onclick="alert(\'Use o Customer Portal ou Stripe Dashboard para cancelar\');" style="color: red;">Cancelar assinatura</a>'
            )
        return '-'
    cancel_url_display.short_description = 'Ações'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Custom admin for Stripe Products"""
    list_display = ['id', 'name', 'type', 'active_badge', 'prices_count', 'created']
    list_filter = ['active', 'type', 'livemode', 'created']
    search_fields = ['id', 'name', 'description']
    readonly_fields = ['id', 'created', 'stripe_dashboard_link']

    def active_badge(self, obj):
        if obj.active:
            return format_html('<span style="color: green;">✓ Ativo</span>')
        return format_html('<span style="color: red;">✗ Inativo</span>')
    active_badge.short_description = 'Status'

    def prices_count(self, obj):
        from djstripe.models import Price
        count = Price.objects.filter(product=obj).count()
        return f'{count} preço(s)'
    prices_count.short_description = 'Preços'

    def stripe_dashboard_link(self, obj):
        mode = '' if obj.livemode else 'test/'
        url = f'https://dashboard.stripe.com/{mode}products/{obj.id}'
        return format_html('<a href="{}" target="_blank">Ver no Stripe Dashboard →</a>', url)
    stripe_dashboard_link.short_description = 'Stripe'


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    """Custom admin for Stripe Prices"""
    list_display = ['id', 'product_link', 'amount_display', 'interval_display', 'active_badge', 'created']
    list_filter = ['active', 'type', 'livemode', 'created']
    search_fields = ['id', 'product__name', 'nickname']
    readonly_fields = ['id', 'created', 'stripe_dashboard_link']

    def product_link(self, obj):
        if obj.product:
            url = reverse('admin:djstripe_product_change', args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', url, obj.product.name)
        return '-'
    product_link.short_description = 'Produto'

    def amount_display(self, obj):
        if obj.unit_amount:
            amount = obj.unit_amount / 100
            return f'R$ {amount:.2f}'
        return '-'
    amount_display.short_description = 'Valor'

    def interval_display(self, obj):
        if obj.recurring:
            interval = obj.recurring.get('interval', '-')
            interval_count = obj.recurring.get('interval_count', 1)
            intervals = {'month': 'mês', 'year': 'ano', 'week': 'semana', 'day': 'dia'}
            interval_pt = intervals.get(interval, interval)
            if interval_count > 1:
                return f'a cada {interval_count} {interval_pt}(es)'
            return f'por {interval_pt}'
        return 'Pagamento único'
    interval_display.short_description = 'Recorrência'

    def active_badge(self, obj):
        if obj.active:
            return format_html('<span style="color: green;">✓ Ativo</span>')
        return format_html('<span style="color: red;">✗ Inativo</span>')
    active_badge.short_description = 'Status'

    def stripe_dashboard_link(self, obj):
        mode = '' if obj.livemode else 'test/'
        url = f'https://dashboard.stripe.com/{mode}prices/{obj.id}'
        return format_html('<a href="{}" target="_blank">Ver no Stripe Dashboard →</a>', url)
    stripe_dashboard_link.short_description = 'Stripe'


# Customizar o admin do User para mostrar info de assinatura
class SubscriptionInline(admin.TabularInline):
    model = Subscription
    fk_name = 'customer'
    extra = 0
    can_delete = False
    readonly_fields = ['id', 'status', 'plan', 'current_period_start', 'current_period_end']
    fields = ['id', 'status', 'plan', 'current_period_start', 'current_period_end']

    def has_add_permission(self, request, obj=None):
        return False

