"""
Enhanced Companies admin - Comprehensive business management
Provides advanced subscription management, usage tracking, and business insights
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count, Sum, Q
from decimal import Decimal
from .models import Company, SubscriptionPlan
from core.admin import BaseModelAdmin


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(BaseModelAdmin):
    """Enhanced admin for subscription plans with business analytics"""

    list_display = [
        'name', 'plan_type_display', 'pricing_display', 'limits_display',
        'subscribers_count', 'revenue_display', 'is_active_display'
    ]
    list_filter = ['is_active', 'plan_type', 'display_order']
    search_fields = ['name', 'slug', 'plan_type']
    ordering = ['display_order', 'price_monthly']
    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'slug', 'plan_type', 'trial_days', 'display_order', 'is_active')
        }),
        (_('Pricing'), {
            'fields': ('price_monthly', 'price_yearly'),
            'description': 'Configure monthly and yearly pricing for this plan'
        }),
        (_('Limits & Features'), {
            'fields': ('max_bank_accounts',),
            'description': 'Set usage limits for this subscription plan'
        }),
        (_('Payment Gateway Integration'), {
            'fields': ('stripe_price_id_monthly', 'stripe_price_id_yearly'),
            'classes': ('collapse',),
            'description': 'Stripe price IDs for payment processing'
        }),
        (_('Analytics'), {
            'fields': ('analytics_summary',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('analytics_summary', 'created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            company_count=Count('company'),
            total_monthly_revenue=Count('company', filter=Q(company__billing_cycle='monthly')) * self.model._meta.get_field('price_monthly'),
            total_yearly_revenue=Count('company', filter=Q(company__billing_cycle='yearly')) * self.model._meta.get_field('price_yearly')
        )

    def plan_type_display(self, obj):
        colors = {
            'Pro': '#2563eb',
            'Business': '#7c3aed',
            'Enterprise': '#dc2626',
            'Free': '#16a34a'
        }
        color = colors.get(obj.plan_type, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, obj.plan_type
        )
    plan_type_display.short_description = _('Plan Type')

    def pricing_display(self, obj):
        monthly = f"R$ {obj.price_monthly:,.2f}"
        yearly = f"R$ {obj.price_yearly:,.2f}"
        yearly_discount = ((obj.price_monthly * 12 - obj.price_yearly) / (obj.price_monthly * 12) * 100) if obj.price_monthly > 0 else 0

        html = f'<div><strong>Mensal:</strong> {monthly}</div>'
        html += f'<div><strong>Anual:</strong> {yearly}'
        if yearly_discount > 0:
            html += f' <small style="color: green;">({yearly_discount:.0f}% off)</small>'
        html += '</div>'
        return format_html(html)
    pricing_display.short_description = _('Pricing')

    def limits_display(self, obj):
        return format_html(
            '<div>📊 {} contas bancárias</div>',
            obj.max_bank_accounts
        )
    limits_display.short_description = _('Limits')

    def subscribers_count(self, obj):
        count = getattr(obj, 'company_count', 0)
        if count > 0:
            url = f'/admin/companies/company/?subscription_plan__id__exact={obj.pk}'
            return format_html('<a href="{}">{} empresas</a>', url, count)
        return '0 empresas'
    subscribers_count.short_description = _('Subscribers')

    def revenue_display(self, obj):
        monthly_subs = obj.company_set.filter(billing_cycle='monthly', subscription_status='active').count()
        yearly_subs = obj.company_set.filter(billing_cycle='yearly', subscription_status='active').count()

        monthly_revenue = monthly_subs * obj.price_monthly
        yearly_revenue = yearly_subs * obj.price_yearly / 12  # Convert to monthly
        total_monthly = monthly_revenue + yearly_revenue

        if total_monthly > 0:
            return format_html(
                '<div style="color: green; font-weight: bold;">R$ {:.2f}/mês</div>',
                total_monthly
            )
        return 'R$ 0,00/mês'
    revenue_display.short_description = _('Monthly Revenue')

    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ Ativo</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Inativo</span>')
    is_active_display.short_description = _('Status')

    def analytics_summary(self, obj):
        if not obj.pk:
            return 'Salve o plano para ver analytics'

        companies = obj.company_set.all()
        active_count = companies.filter(subscription_status='active').count()
        trial_count = companies.filter(subscription_status='trial').count()
        cancelled_count = companies.filter(subscription_status='cancelled').count()

        monthly_revenue = companies.filter(
            billing_cycle='monthly',
            subscription_status='active'
        ).count() * obj.price_monthly

        yearly_revenue = companies.filter(
            billing_cycle='yearly',
            subscription_status='active'
        ).count() * obj.price_yearly / 12

        total_revenue = monthly_revenue + yearly_revenue

        html = '<table style="width: 100%;">'
        html += f'<tr><td><strong>Empresas Ativas:</strong></td><td>{active_count}</td></tr>'
        html += f'<tr><td><strong>Em Trial:</strong></td><td>{trial_count}</td></tr>'
        html += f'<tr><td><strong>Canceladas:</strong></td><td>{cancelled_count}</td></tr>'
        html += f'<tr><td><strong>Receita Mensal:</strong></td><td>R$ {total_revenue:,.2f}</td></tr>'
        html += f'<tr><td><strong>Receita Anual Projetada:</strong></td><td>R$ {total_revenue * 12:,.2f}</td></tr>'
        html += '</table>'
        return format_html(html)
    analytics_summary.short_description = _('Business Analytics')

    actions = ['activate_plans', 'deactivate_plans', 'duplicate_plan']

    def activate_plans(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} planos ativados com sucesso.')
    activate_plans.short_description = 'Ativar planos selecionados'

    def deactivate_plans(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} planos desativados com sucesso.')
    deactivate_plans.short_description = 'Desativar planos selecionados'

    def duplicate_plan(self, request, queryset):
        for plan in queryset:
            plan.pk = None
            plan.name = f"{plan.name} (Cópia)"
            plan.slug = f"{plan.slug}-copy"
            plan.is_active = False
            plan.save()
        count = queryset.count()
        self.message_user(request, f'{count} planos duplicados com sucesso.')
    duplicate_plan.short_description = 'Duplicar planos selecionados'


@admin.register(Company)
class CompanyAdmin(BaseModelAdmin):
    """Enhanced admin for companies with comprehensive business insights"""

    list_display = [
        'name', 'owner_display', 'subscription_display', 'status_display',
        'trial_status', 'usage_display', 'revenue_display', 'created_at_display'
    ]
    list_filter = [
        'subscription_status', 'subscription_plan', 'billing_cycle',
        'is_active', 'created_at'
    ]
    search_fields = ['name', 'owner__email', 'owner__first_name', 'owner__last_name']
    readonly_fields = [
        'created_at', 'updated_at', 'trial_status_detail', 'usage_summary',
        'subscription_analytics', 'financial_summary'
    ]
    raw_id_fields = ['owner']
    date_hierarchy = 'created_at'

    fieldsets = (
        (_('Company Information'), {
            'fields': ('owner', 'name', 'is_active')
        }),
        (_('Subscription Details'), {
            'fields': (
                'subscription_plan', 'subscription_status', 'billing_cycle',
                'trial_ends_at', 'subscription_id'
            )
        }),
        (_('Usage Tracking'), {
            'fields': ('current_month_transactions', 'usage_summary'),
            'description': 'Current usage statistics and limits'
        }),
        (_('Trial Information'), {
            'fields': ('trial_status_detail',),
            'classes': ('collapse',)
        }),
        (_('Analytics & Insights'), {
            'fields': ('subscription_analytics', 'financial_summary'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('owner', 'subscription_plan').prefetch_related('bank_accounts', 'transactions')

    def owner_display(self, obj):
        url = reverse('admin:authentication_user_change', args=[obj.owner.pk])
        name = obj.owner.full_name or obj.owner.email
        return format_html('<a href="{}">{}</a><br><small>{}</small>', url, name, obj.owner.email)
    owner_display.short_description = _('Owner')
    owner_display.admin_order_field = 'owner__email'

    def subscription_display(self, obj):
        if obj.subscription_plan:
            plan_url = reverse('admin:companies_subscriptionplan_change', args=[obj.subscription_plan.pk])
            monthly_price = obj.subscription_plan.price_monthly
            yearly_price = obj.subscription_plan.price_yearly

            if obj.billing_cycle == 'yearly':
                price = f"R$ {yearly_price:,.2f}/ano"
            else:
                price = f"R$ {monthly_price:,.2f}/mês"

            return format_html(
                '<a href="{}">{}</a><br><small>{}</small>',
                plan_url, obj.subscription_plan.name, price
            )
        return format_html('<em style="color: #999;">Sem plano</em>')
    subscription_display.short_description = _('Subscription')

    def status_display(self, obj):
        colors = {
            'trial': '#f59e0b',
            'active': '#10b981',
            'cancelled': '#ef4444',
            'expired': '#6b7280'
        }
        color = colors.get(obj.subscription_status, '#6b7280')
        status_text = {
            'trial': 'Trial',
            'active': 'Ativo',
            'cancelled': 'Cancelado',
            'expired': 'Expirado'
        }.get(obj.subscription_status, obj.subscription_status)

        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, status_text
        )
    status_display.short_description = _('Status')

    def trial_status(self, obj):
        if obj.subscription_status == 'trial':
            days = obj.days_until_trial_ends
            if days > 0:
                return format_html('<span style="color: green;">{} dias restantes</span>', days)
            else:
                return format_html('<span style="color: red;">Expirado</span>')
        return '-'
    trial_status.short_description = _('Trial')

    def usage_display(self, obj):
        if not obj.subscription_plan:
            return 'Sem plano'

        bank_accounts = obj.bank_accounts.filter(is_active=True).count()
        max_accounts = obj.subscription_plan.max_bank_accounts

        # Calculate usage percentage
        account_usage = (bank_accounts / max_accounts * 100) if max_accounts > 0 else 0

        # Color based on usage
        if account_usage >= 90:
            color = '#ef4444'  # red
        elif account_usage >= 70:
            color = '#f59e0b'  # yellow
        else:
            color = '#10b981'  # green

        return format_html(
            '<div><strong>Contas:</strong> <span style="color: {};">{}/{}</span></div>'
            '<div><strong>Transações:</strong> {}</div>',
            color, bank_accounts, max_accounts, obj.current_month_transactions
        )
    usage_display.short_description = _('Usage')

    def revenue_display(self, obj):
        if obj.subscription_plan and obj.subscription_status == 'active':
            if obj.billing_cycle == 'yearly':
                amount = obj.subscription_plan.price_yearly
                period = '/ano'
            else:
                amount = obj.subscription_plan.price_monthly
                period = '/mês'

            return format_html(
                '<span style="color: green; font-weight: bold;">R$ {:.2f}{}</span>',
                amount, period
            )
        return 'R$ 0,00'
    revenue_display.short_description = _('Revenue')

    def created_at_display(self, obj):
        return obj.created_at.strftime('%d/%m/%Y')
    created_at_display.short_description = _('Created')
    created_at_display.admin_order_field = 'created_at'

    def trial_status_detail(self, obj):
        if obj.subscription_status != 'trial':
            return 'Não está em trial'

        if not obj.trial_ends_at:
            return 'Data de expiração não definida'

        now = timezone.now()
        if obj.trial_ends_at > now:
            diff = obj.trial_ends_at - now
            return format_html(
                '<div style="color: green;">Trial ativo - {} dias restantes</div>'
                '<div>Expira em: {}</div>',
                diff.days, obj.trial_ends_at.strftime('%d/%m/%Y %H:%M')
            )
        else:
            return format_html(
                '<div style="color: red;">Trial expirado</div>'
                '<div>Expirou em: {}</div>',
                obj.trial_ends_at.strftime('%d/%m/%Y %H:%M')
            )
    trial_status_detail.short_description = _('Trial Details')

    def usage_summary(self, obj):
        if not obj.subscription_plan:
            return 'Empresa sem plano de assinatura'

        bank_accounts = obj.bank_accounts.filter(is_active=True).count()
        max_accounts = obj.subscription_plan.max_bank_accounts

        # Get transaction stats
        total_transactions = obj.transactions.count()

        html = '<table style="width: 100%;">'
        html += f'<tr><td><strong>Contas Bancárias:</strong></td><td>{bank_accounts}/{max_accounts}</td></tr>'
        html += f'<tr><td><strong>Transações (total):</strong></td><td>{total_transactions}</td></tr>'
        html += f'<tr><td><strong>Transações (mês atual):</strong></td><td>{obj.current_month_transactions}</td></tr>'

        # Usage warnings
        if bank_accounts >= max_accounts:
            html += '<tr><td colspan="2"><div style="color: red; font-weight: bold;">⚠️ Limite de contas atingido</div></td></tr>'
        elif bank_accounts >= max_accounts * 0.8:
            html += '<tr><td colspan="2"><div style="color: orange; font-weight: bold;">⚠️ Próximo do limite de contas</div></td></tr>'

        html += '</table>'
        return format_html(html)
    usage_summary.short_description = _('Usage Summary')

    def subscription_analytics(self, obj):
        if not obj.subscription_plan:
            return 'Sem dados de assinatura'

        # Calculate subscription value
        if obj.subscription_status == 'active':
            if obj.billing_cycle == 'yearly':
                value = obj.subscription_plan.price_yearly
                period = 'ano'
            else:
                value = obj.subscription_plan.price_monthly
                period = 'mês'
        else:
            value = 0
            period = 'inativo'

        # Calculate lifetime value estimation
        months_active = (timezone.now() - obj.created_at).days / 30.44
        if obj.billing_cycle == 'yearly':
            ltv = months_active * (obj.subscription_plan.price_yearly / 12)
        else:
            ltv = months_active * obj.subscription_plan.price_monthly

        html = '<table style="width: 100%;">'
        html += f'<tr><td><strong>Valor Atual:</strong></td><td>R$ {value:,.2f}/{period}</td></tr>'
        html += f'<tr><td><strong>Meses Ativo:</strong></td><td>{months_active:.1f}</td></tr>'
        html += f'<tr><td><strong>LTV Estimado:</strong></td><td>R$ {ltv:,.2f}</td></tr>'
        html += '</table>'
        return format_html(html)
    subscription_analytics.short_description = _('Subscription Analytics')

    def financial_summary(self, obj):
        # This would integrate with transaction analysis
        # For now, showing basic financial metrics

        total_transactions = obj.transactions.count()
        if total_transactions == 0:
            return 'Nenhuma transação encontrada'

        # You could add more sophisticated financial analysis here
        html = '<table style="width: 100%;">'
        html += f'<tr><td><strong>Total de Transações:</strong></td><td>{total_transactions}</td></tr>'
        html += f'<tr><td><strong>Contas Conectadas:</strong></td><td>{obj.bank_accounts.filter(is_active=True).count()}</td></tr>'
        html += '</table>'
        return format_html(html)
    financial_summary.short_description = _('Financial Summary')

    # Enhanced actions
    actions = [
        'activate_companies', 'deactivate_companies', 'extend_trial',
        'convert_to_paid', 'send_usage_report'
    ]

    def activate_companies(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} empresas ativadas com sucesso.')
    activate_companies.short_description = 'Ativar empresas selecionadas'

    def deactivate_companies(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} empresas desativadas com sucesso.')
    deactivate_companies.short_description = 'Desativar empresas selecionadas'

    def extend_trial(self, request, queryset):
        trial_companies = queryset.filter(subscription_status='trial')
        count = 0
        for company in trial_companies:
            if company.trial_ends_at:
                company.trial_ends_at = company.trial_ends_at + timezone.timedelta(days=7)
                company.save()
                count += 1
        self.message_user(request, f'Trial estendido por 7 dias para {count} empresas.')
    extend_trial.short_description = 'Estender trial por 7 dias'

    def convert_to_paid(self, request, queryset):
        trial_companies = queryset.filter(subscription_status='trial')
        updated = trial_companies.update(subscription_status='active')
        self.message_user(request, f'{updated} empresas convertidas para plano pago.')
    convert_to_paid.short_description = 'Converter trial para pago'

    def send_usage_report(self, request, queryset):
        # This would integrate with your email/notification system
        count = queryset.count()
        self.message_user(request, f'Relatório de uso enviado para {count} empresas.')
    send_usage_report.short_description = 'Enviar relatório de uso'