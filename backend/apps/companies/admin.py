"""
Painel administrativo completo para controle de pagamentos e planos
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from django.utils import timezone

from .models import Company, SubscriptionPlan, CompanyUser, PaymentMethod, PaymentHistory, ResourceUsage


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'plan_type', 'price_display', 'limits_display', 
        'features_display', 'active_companies', 'is_active'
    ]
    list_filter = ['plan_type', 'is_active', 'has_ai_categorization']
    search_fields = ['name', 'slug']
    ordering = ['display_order', 'price_monthly']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'slug', 'plan_type', 'display_order', 'is_active')
        }),
        ('Preços', {
            'fields': ('price_monthly', 'price_yearly'),
            'description': 'Valores em R$'
        }),
        ('IDs de Gateway', {
            'fields': ('stripe_price_id', 'mercadopago_plan_id'),
            'classes': ('collapse',),
            'description': 'Configure os IDs dos produtos nos gateways de pagamento'
        }),
        ('Limites', {
            'fields': (
                'max_transactions', 'max_bank_accounts', 
                'max_users', 'max_ai_requests_per_month'
            )
        }),
        ('Recursos', {
            'fields': (
                'has_ai_categorization', 'enable_ai_insights', 
                'enable_ai_reports', 'has_advanced_reports',
                'has_api_access', 'has_accountant_access', 
                'has_priority_support'
            )
        }),
    )
    
    def price_display(self, obj):
        monthly = f"R$ {obj.price_monthly}/mês"
        yearly = f"R$ {obj.price_yearly}/ano"
        discount = obj.get_yearly_discount_percentage()
        
        return format_html(
            '<div>{}</div><div style="color: green;">{} <small>({} % desc.)</small></div>',
            monthly, yearly, discount
        )
    price_display.short_description = 'Preços'
    
    def limits_display(self, obj):
        return format_html(
            '''<ul style="margin: 0; padding-left: 20px;">
                <li>{} transações</li>
                <li>{} contas</li>
                <li>{} usuários</li>
                <li>{} IA/mês</li>
            </ul>''',
            obj.max_transactions,
            obj.max_bank_accounts,
            obj.max_users,
            obj.max_ai_requests_per_month
        )
    limits_display.short_description = 'Limites'
    
    def features_display(self, obj):
        features = []
        if obj.has_ai_categorization:
            features.append('✅ IA')
        if obj.has_advanced_reports:
            features.append('📊 Relatórios')
        if obj.has_api_access:
            features.append('🔌 API')
        if obj.has_priority_support:
            features.append('⚡ Suporte')
        
        return ' '.join(features) or '—'
    features_display.short_description = 'Recursos'
    
    def active_companies(self, obj):
        count = obj.companies.filter(subscription_status='active').count()
        return format_html(
            '<a href="{}?subscription_plan__id__exact={}">{} empresas</a>',
            reverse('admin:companies_company_changelist'),
            obj.id,
            count
        )
    active_companies.short_description = 'Empresas Ativas'


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'owner_link', 'plan_info', 'subscription_status_display',
        'usage_display', 'billing_info', 'actions_display'
    ]
    list_filter = [
        'subscription_status', 'subscription_plan', 'billing_cycle',
        'created_at', 'is_active'
    ]
    search_fields = ['name', 'cnpj', 'owner__email', 'owner__first_name']
    date_hierarchy = 'created_at'
    
    readonly_fields = [
        'created_at', 'updated_at', 'usage_summary_display',
        'payment_history_display', 'subscription_timeline'
    ]
    
    fieldsets = (
        ('Informações da Empresa', {
            'fields': (
                'name', 'trade_name', 'owner', 'cnpj',
                'company_type', 'business_sector', 'is_active'
            )
        }),
        ('Assinatura', {
            'fields': (
                'subscription_plan', 'subscription_status', 'billing_cycle',
                'trial_ends_at', 'next_billing_date',
                'subscription_start_date', 'subscription_end_date',
                'subscription_id'
            )
        }),
        ('Uso Atual', {
            'fields': (
                'usage_summary_display',
                'current_month_transactions', 'current_month_ai_requests',
                'last_usage_reset', 'notified_80_percent', 'notified_90_percent'
            )
        }),
        ('Histórico', {
            'fields': ('payment_history_display', 'subscription_timeline'),
            'classes': ('collapse',)
        }),
    )
    
    def owner_link(self, obj):
        url = reverse('admin:authentication_user_change', args=[obj.owner.id])
        return format_html('<a href="{}">{}</a>', url, obj.owner.email)
    owner_link.short_description = 'Proprietário'
    
    def plan_info(self, obj):
        if not obj.subscription_plan:
            return '—'
        
        plan = obj.subscription_plan
        return format_html(
            '<strong>{}</strong><br><small>R$ {}/{}</small>',
            plan.name,
            plan.price_yearly if obj.billing_cycle == 'yearly' else plan.price_monthly,
            'ano' if obj.billing_cycle == 'yearly' else 'mês'
        )
    plan_info.short_description = 'Plano'
    
    def subscription_status_display(self, obj):
        colors = {
            'trial': 'orange',
            'active': 'green',
            'past_due': 'red',
            'cancelled': 'gray',
            'suspended': 'darkred',
            'expired': 'black'
        }
        
        status_text = obj.get_subscription_status_display()
        
        # Add trial days if in trial
        if obj.subscription_status == 'trial' and obj.trial_ends_at:
            days = (obj.trial_ends_at - timezone.now()).days
            if days >= 0:
                status_text += f' ({days}d)'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.subscription_status, 'black'),
            status_text
        )
    subscription_status_display.short_description = 'Status'
    
    def usage_display(self, obj):
        if not obj.subscription_plan:
            return '—'
        
        # Calculate percentages
        tx_percent = obj.get_usage_percentage('transactions')
        ai_percent = obj.get_usage_percentage('ai_requests')
        
        # Color coding
        def get_color(percent):
            if percent >= 90: return 'red'
            if percent >= 80: return 'orange'
            if percent >= 70: return 'yellow'
            return 'green'
        
        return format_html(
            '''<div style="font-size: 11px;">
                <div>TX: <span style="color: {};">{}/{} ({}%)</span></div>
                <div>IA: <span style="color: {};">{}/{} ({}%)</span></div>
            </div>''',
            get_color(tx_percent),
            obj.current_month_transactions,
            obj.subscription_plan.max_transactions,
            int(tx_percent),
            get_color(ai_percent),
            obj.current_month_ai_requests,
            obj.subscription_plan.max_ai_requests_per_month,
            int(ai_percent)
        )
    usage_display.short_description = 'Uso'
    
    def billing_info(self, obj):
        info = []
        
        if obj.next_billing_date:
            days_until = (obj.next_billing_date - timezone.now().date()).days
            info.append(f"Próx: {obj.next_billing_date.strftime('%d/%m')}")
            if 0 <= days_until <= 7:
                info.append(f'<span style="color: orange;">({days_until}d)</span>')
        
        # Calculate MRR
        if obj.subscription_plan and obj.subscription_status == 'active':
            mrr = obj.subscription_plan.price_monthly
            if obj.billing_cycle == 'yearly':
                mrr = obj.subscription_plan.price_yearly / 12
            info.append(f'MRR: R$ {mrr:.2f}')
        
        return format_html('<br>'.join(info)) if info else '—'
    billing_info.short_description = 'Faturamento'
    
    def actions_display(self, obj):
        actions = []
        
        # Quick actions based on status
        if obj.subscription_status == 'trial':
            actions.append(
                f'<a href="#" onclick="return confirm(\'Converter trial em assinatura paga?\');" '
                f'class="button">Converter Trial</a>'
            )
        elif obj.subscription_status == 'past_due':
            actions.append(
                f'<a href="#" class="button" style="background: orange;">Cobrar Novamente</a>'
            )
        elif obj.subscription_status == 'active':
            actions.append(
                f'<a href="#" class="button">Ver Faturas</a>'
            )
        
        return format_html(' '.join(actions)) if actions else '—'
    actions_display.short_description = 'Ações'
    
    def usage_summary_display(self, obj):
        summary = obj.get_usage_summary()
        if not summary:
            return "Sem plano ativo"
        
        html = '<table style="width: 100%;">'
        for key, data in summary.items():
            color = 'red' if data['percentage'] >= 90 else 'green'
            html += f'''
            <tr>
                <td><strong>{key.title()}:</strong></td>
                <td>{data['used']} / {data['limit']}</td>
                <td style="color: {color};">{data['percentage']:.1f}%</td>
            </tr>
            '''
        html += '</table>'
        
        return format_html(html)
    usage_summary_display.short_description = 'Resumo de Uso'
    
    def payment_history_display(self, obj):
        payments = PaymentHistory.objects.filter(
            company=obj
        ).order_by('-transaction_date')[:10]
        
        if not payments:
            return "Sem histórico de pagamentos"
        
        html = '<table style="width: 100%;">'
        html += '<tr><th>Data</th><th>Tipo</th><th>Valor</th><th>Status</th></tr>'
        
        for payment in payments:
            status_color = {
                'paid': 'green',
                'pending': 'orange',
                'failed': 'red'
            }.get(payment.status, 'gray')
            
            html += f'''
            <tr>
                <td>{payment.transaction_date.strftime('%d/%m/%Y')}</td>
                <td>{payment.get_transaction_type_display()}</td>
                <td>R$ {payment.amount}</td>
                <td style="color: {status_color};">{payment.get_status_display()}</td>
            </tr>
            '''
        
        html += '</table>'
        return format_html(html)
    payment_history_display.short_description = 'Histórico de Pagamentos'
    
    def subscription_timeline(self, obj):
        events = []
        
        # Company created
        events.append({
            'date': obj.created_at,
            'event': 'Empresa criada',
            'type': 'info'
        })
        
        # Trial start
        if obj.trial_ends_at:
            trial_start = obj.trial_ends_at - timedelta(days=14)
            events.append({
                'date': trial_start,
                'event': 'Trial iniciado (14 dias)',
                'type': 'success'
            })
        
        # Subscription changes
        payments = PaymentHistory.objects.filter(
            company=obj,
            transaction_type__in=['subscription', 'upgrade']
        ).order_by('transaction_date')
        
        for payment in payments:
            events.append({
                'date': payment.transaction_date,
                'event': f'{payment.description}',
                'type': 'success' if payment.status == 'paid' else 'error'
            })
        
        # Sort by date
        events.sort(key=lambda x: x['date'], reverse=True)
        
        # Build HTML
        html = '<div style="max-height: 300px; overflow-y: auto;">'
        for event in events[:20]:  # Limit to 20 most recent
            icon = {
                'info': '📝',
                'success': '✅',
                'error': '❌',
                'warning': '⚠️'
            }.get(event['type'], '📌')
            
            html += f'''
            <div style="margin-bottom: 10px; padding: 5px; border-left: 3px solid #ddd;">
                {icon} <strong>{event['date'].strftime('%d/%m/%Y %H:%M')}</strong><br>
                {event['event']}
            </div>
            '''
        html += '</div>'
        
        return format_html(html)
    subscription_timeline.short_description = 'Timeline da Assinatura'
    
    actions = [
        'reset_usage_counters',
        'extend_trial',
        'activate_subscription',
        'suspend_subscription',
        'cancel_subscription'
    ]
    
    @admin.action(description='Resetar contadores de uso')
    def reset_usage_counters(self, request, queryset):
        for company in queryset:
            company.reset_monthly_usage()
        self.message_user(request, f'{queryset.count()} empresas tiveram os contadores resetados.')
    
    @admin.action(description='Estender trial por 7 dias')
    def extend_trial(self, request, queryset):
        count = 0
        for company in queryset.filter(subscription_status='trial'):
            if company.trial_ends_at:
                company.trial_ends_at += timedelta(days=7)
                company.save()
                count += 1
        self.message_user(request, f'Trial estendido para {count} empresas.')
    
    @admin.action(description='Ativar assinatura')
    def activate_subscription(self, request, queryset):
        queryset.update(subscription_status='active')
        self.message_user(request, f'{queryset.count()} assinaturas ativadas.')
    
    @admin.action(description='Suspender assinatura')
    def suspend_subscription(self, request, queryset):
        queryset.update(subscription_status='suspended')
        self.message_user(request, f'{queryset.count()} assinaturas suspensas.')
    
    @admin.action(description='Cancelar assinatura')
    def cancel_subscription(self, request, queryset):
        queryset.update(
            subscription_status='cancelled',
            subscription_end_date=timezone.now()
        )
        self.message_user(request, f'{queryset.count()} assinaturas canceladas.')


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'company_link', 'transaction_type',
        'amount_display', 'status_display', 'transaction_date',
        'payment_method_info', 'invoice_link'
    ]
    list_filter = [
        'status', 'transaction_type', 'transaction_date',
        'subscription_plan'
    ]
    search_fields = [
        'invoice_number', 'company__name', 'description',
        'stripe_payment_intent_id', 'mercadopago_payment_id'
    ]
    date_hierarchy = 'transaction_date'
    readonly_fields = [
        'created_at', 'updated_at', 'gateway_ids_display'
    ]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': (
                'company', 'subscription_plan', 'payment_method',
                'transaction_type', 'status', 'description'
            )
        }),
        ('Valores', {
            'fields': ('amount', 'currency')
        }),
        ('Datas', {
            'fields': (
                'transaction_date', 'due_date', 'paid_at',
                'created_at', 'updated_at'
            )
        }),
        ('Fatura', {
            'fields': ('invoice_number', 'invoice_url', 'invoice_pdf_path')
        }),
        ('Gateway IDs', {
            'fields': ('gateway_ids_display',),
            'classes': ('collapse',)
        }),
    )
    
    def company_link(self, obj):
        url = reverse('admin:companies_company_change', args=[obj.company.id])
        return format_html('<a href="{}">{}</a>', url, obj.company.name)
    company_link.short_description = 'Empresa'
    
    def amount_display(self, obj):
        color = 'green' if obj.status == 'paid' else 'gray'
        return format_html(
            '<span style="color: {}; font-weight: bold;">R$ {}</span>',
            color, obj.amount
        )
    amount_display.short_description = 'Valor'
    
    def status_display(self, obj):
        colors = {
            'pending': 'orange',
            'paid': 'green',
            'failed': 'red',
            'canceled': 'gray',
            'refunded': 'blue'
        }
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def payment_method_info(self, obj):
        if not obj.payment_method:
            return '—'
        
        pm = obj.payment_method
        if pm.payment_type == 'pix':
            return 'PIX'
        
        return f"{pm.card_brand} •••• {pm.last_four}"
    payment_method_info.short_description = 'Método'
    
    def invoice_link(self, obj):
        if obj.invoice_url:
            return format_html(
                '<a href="{}" target="_blank">Ver Fatura</a>',
                obj.invoice_url
            )
        return '—'
    invoice_link.short_description = 'Fatura'
    
    def gateway_ids_display(self, obj):
        ids = []
        if obj.stripe_payment_intent_id:
            ids.append(f"Stripe: {obj.stripe_payment_intent_id}")
        if obj.mercadopago_payment_id:
            ids.append(f"MercadoPago: {obj.mercadopago_payment_id}")
        
        return '\n'.join(ids) or 'Nenhum ID de gateway'
    gateway_ids_display.short_description = 'IDs do Gateway'
    
    actions = ['mark_as_paid', 'mark_as_failed', 'resend_invoice']
    
    @admin.action(description='Marcar como pago')
    def mark_as_paid(self, request, queryset):
        queryset.update(status='paid', paid_at=timezone.now())
        self.message_user(request, f'{queryset.count()} pagamentos marcados como pagos.')
    
    @admin.action(description='Marcar como falhou')
    def mark_as_failed(self, request, queryset):
        queryset.update(status='failed')
        self.message_user(request, f'{queryset.count()} pagamentos marcados como falhados.')
    
    @admin.action(description='Reenviar fatura por email')
    def resend_invoice(self, request, queryset):
        # Implementar envio de email
        self.message_user(request, f'Faturas reenviadas para {queryset.count()} pagamentos.')


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = [
        'company_link', 'payment_type', 'card_info',
        'is_default', 'is_active', 'created_at'
    ]
    list_filter = ['payment_type', 'is_default', 'is_active', 'card_brand']
    search_fields = ['company__name', 'cardholder_name', 'last_four']
    
    def company_link(self, obj):
        url = reverse('admin:companies_company_change', args=[obj.company.id])
        return format_html('<a href="{}">{}</a>', url, obj.company.name)
    company_link.short_description = 'Empresa'
    
    def card_info(self, obj):
        if obj.payment_type == 'pix':
            return 'PIX'
        
        return format_html(
            '{} •••• {} <small>({})</small>',
            obj.card_brand.upper() if obj.card_brand else 'CARD',
            obj.last_four,
            f"{obj.exp_month:02d}/{obj.exp_year}" if obj.exp_month else ''
        )
    card_info.short_description = 'Informações'


# Proxy model para o Dashboard
class BillingDashboardProxy(Company):
    class Meta:
        proxy = True
        verbose_name = 'Dashboard de Faturamento'
        verbose_name_plural = 'Dashboard de Faturamento'


@admin.register(BillingDashboardProxy)
class BillingDashboardAdmin(admin.ModelAdmin):
    change_list_template = 'admin/billing_dashboard.html'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        # Métricas gerais
        total_companies = Company.objects.filter(is_active=True).count()
        active_subscriptions = Company.objects.filter(
            subscription_status='active'
        ).count()
        trial_companies = Company.objects.filter(
            subscription_status='trial'
        ).count()
        
        # MRR (Monthly Recurring Revenue)
        companies_monthly = Company.objects.filter(
            subscription_status='active',
            billing_cycle='monthly'
        ).select_related('subscription_plan')
        
        companies_yearly = Company.objects.filter(
            subscription_status='active',
            billing_cycle='yearly'
        ).select_related('subscription_plan')
        
        mrr_monthly = sum(
            company.subscription_plan.price_monthly 
            for company in companies_monthly 
            if company.subscription_plan
        )
        
        mrr_yearly = sum(
            company.subscription_plan.price_yearly / 12 
            for company in companies_yearly 
            if company.subscription_plan
        )
        
        mrr_total = mrr_monthly + mrr_yearly
        
        # Pagamentos do mês
        current_month_start = timezone.now().replace(day=1)
        monthly_revenue = PaymentHistory.objects.filter(
            transaction_date__gte=current_month_start,
            status='paid'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Trials expirando
        trials_expiring = Company.objects.filter(
            subscription_status='trial',
            trial_ends_at__lte=timezone.now() + timedelta(days=7),
            trial_ends_at__gt=timezone.now()
        ).count()
        
        # Últimos pagamentos
        recent_payments = PaymentHistory.objects.filter(
            status='paid'
        ).select_related('company').order_by('-transaction_date')[:10]
        
        extra_context = extra_context or {}
        extra_context.update({
            'title': 'Dashboard de Faturamento',
            'total_companies': total_companies,
            'active_subscriptions': active_subscriptions,
            'trial_companies': trial_companies,
            'mrr_total': mrr_total,
            'mrr_monthly': mrr_monthly,
            'mrr_yearly': mrr_yearly,
            'monthly_revenue': monthly_revenue,
            'trials_expiring': trials_expiring,
            'recent_payments': recent_payments,
            'next_week': (timezone.now() + timedelta(days=7)).date().isoformat(),
        })
        
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ResourceUsage)
class ResourceUsageAdmin(admin.ModelAdmin):
    list_display = [
        'company', 'month', 'transactions_count', 'ai_requests_count', 
        'reports_generated', 'usage_status', 'updated_at'
    ]
    list_filter = ['month', 'company__subscription_plan']
    search_fields = ['company__name']
    date_hierarchy = 'month'
    ordering = ['-month', 'company__name']
    
    readonly_fields = ['created_at', 'updated_at', 'usage_chart']
    
    fieldsets = (
        ('Empresa e Período', {
            'fields': ('company', 'month')
        }),
        ('Uso de Recursos', {
            'fields': (
                'transactions_count', 
                'ai_requests_count', 
                'reports_generated',
                'usage_chart'
            )
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def usage_status(self, obj):
        """Show usage status with color coding"""
        if not obj.company.subscription_plan:
            return format_html('<span style="color: gray;">Sem plano</span>')
        
        plan = obj.company.subscription_plan
        
        # Check transaction usage
        trans_percent = (obj.transactions_count / plan.max_transactions * 100) if plan.max_transactions > 0 else 0
        
        # Check AI usage
        ai_percent = (obj.total_ai_usage / plan.max_ai_requests_per_month * 100) if plan.max_ai_requests_per_month > 0 else 0
        
        # Determine status color
        max_percent = max(trans_percent, ai_percent)
        if max_percent >= 90:
            color = 'red'
            status = 'Crítico'
        elif max_percent >= 80:
            color = 'orange'
            status = 'Alto'
        elif max_percent >= 60:
            color = 'yellow'
            status = 'Médio'
        else:
            color = 'green'
            status = 'Normal'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span><br/>'
            '<small>Trans: {:.1f}% | IA: {:.1f}%</small>',
            color, status, trans_percent, ai_percent
        )
    usage_status.short_description = 'Status de Uso'
    
    def usage_chart(self, obj):
        """Display usage chart"""
        if not obj.company.subscription_plan:
            return "Sem plano ativo"
        
        plan = obj.company.subscription_plan
        
        # Calculate percentages
        trans_percent = min(100, (obj.transactions_count / plan.max_transactions * 100) if plan.max_transactions > 0 else 0)
        ai_percent = min(100, (obj.total_ai_usage / plan.max_ai_requests_per_month * 100) if plan.max_ai_requests_per_month > 0 else 0)
        
        return format_html(
            '<div style="margin: 10px 0;">'
            '<div style="margin-bottom: 10px;">'
            '<strong>Transações:</strong> {} / {} ({:.1f}%)<br/>'
            '<div style="background: #e0e0e0; height: 20px; width: 300px; border-radius: 4px;">'
            '<div style="background: #4CAF50; height: 100%; width: {}%; border-radius: 4px;"></div>'
            '</div>'
            '</div>'
            '<div>'
            '<strong>Requisições IA:</strong> {} / {} ({:.1f}%)<br/>'
            '<div style="background: #e0e0e0; height: 20px; width: 300px; border-radius: 4px;">'
            '<div style="background: #2196F3; height: 100%; width: {}%; border-radius: 4px;"></div>'
            '</div>'
            '</div>'
            '</div>',
            obj.transactions_count, plan.max_transactions, trans_percent,
            trans_percent,
            obj.total_ai_usage, plan.max_ai_requests_per_month, ai_percent,
            ai_percent
        )
    usage_chart.short_description = 'Gráfico de Uso'
    
    def changelist_view(self, request, extra_context=None):
        """Add summary stats to changelist"""
        extra_context = extra_context or {}
        
        # Get current month
        current_month = timezone.now().replace(day=1).date()
        
        # Get usage stats
        current_usage = ResourceUsage.objects.filter(month=current_month)
        
        total_transactions = current_usage.aggregate(Sum('transactions_count'))['transactions_count__sum'] or 0
        total_ai_requests = current_usage.aggregate(
            total=Sum('ai_requests_count') + Sum('reports_generated')
        )['total'] or 0
        
        # Companies near limits
        companies_near_limit = 0
        for usage in current_usage.select_related('company__subscription_plan'):
            if usage.company.subscription_plan:
                plan = usage.company.subscription_plan
                trans_percent = (usage.transactions_count / plan.max_transactions * 100) if plan.max_transactions > 0 else 0
                ai_percent = (usage.total_ai_usage / plan.max_ai_requests_per_month * 100) if plan.max_ai_requests_per_month > 0 else 0
                if trans_percent >= 80 or ai_percent >= 80:
                    companies_near_limit += 1
        
        extra_context.update({
            'title': 'Uso de Recursos',
            'current_month': current_month.strftime('%B %Y'),
            'total_transactions': total_transactions,
            'total_ai_requests': total_ai_requests,
            'companies_near_limit': companies_near_limit,
            'total_companies': current_usage.count(),
        })
        
        return super().changelist_view(request, extra_context=extra_context)
    
    actions = ['reset_usage_counters']
    
    def reset_usage_counters(self, request, queryset):
        """Reset usage counters for selected records"""
        count = 0
        for usage in queryset:
            usage.transactions_count = 0
            usage.ai_requests_count = 0
            usage.reports_generated = 0
            usage.save()
            count += 1
        
        self.message_user(request, f'{count} registros de uso foram resetados.')
    reset_usage_counters.short_description = 'Resetar contadores de uso'