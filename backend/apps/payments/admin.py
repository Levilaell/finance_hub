"""
Payments app admin configuration
"""
from django.contrib import admin
from django.utils.html import format_html

# Como o app payments não tem models.py próprio (usa models de outros apps),
# vamos criar uma interface administrativa para visualizar informações de pagamento

from apps.companies.models import Company, SubscriptionPlan
from apps.authentication.models import User


class PaymentInfoInline(admin.TabularInline):
    """
    Inline para mostrar informações de pagamento nas empresas
    """
    model = Company
    fields = ['subscription_plan', 'subscription_status', 'trial_ends_at', 'subscription_end_date']
    readonly_fields = fields
    can_delete = False
    max_num = 0
    
    def has_add_permission(self, request, obj=None):
        return False


# Registrar filtros personalizados para facilitar a gestão de pagamentos
class SubscriptionStatusFilter(admin.SimpleListFilter):
    title = 'Status da Assinatura'
    parameter_name = 'subscription_status'
    
    def lookups(self, request, model_admin):
        return [
            ('trial_expiring', 'Trial expirando (7 dias)'),
            ('trial_expired', 'Trial expirado'),
            ('active_paid', 'Assinatura ativa (paga)'),
            ('cancelled', 'Cancelada'),
            ('all_active', 'Todas ativas'),
        ]
    
    def queryset(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        
        if self.value() == 'trial_expiring':
            return queryset.filter(
                subscription_status='trial',
                trial_ends_at__lte=timezone.now() + timedelta(days=7),
                trial_ends_at__gt=timezone.now()
            )
        elif self.value() == 'trial_expired':
            return queryset.filter(
                subscription_status='trial',
                trial_ends_at__lt=timezone.now()
            )
        elif self.value() == 'active_paid':
            return queryset.filter(
                subscription_status='active',
                subscription_plan__price_monthly__gt=0
            )
        elif self.value() == 'cancelled':
            return queryset.filter(subscription_status='cancelled')
        elif self.value() == 'all_active':
            return queryset.filter(subscription_status__in=['trial', 'active'])
        
        return queryset


# Personalizar o admin de Company para incluir informações de pagamento
def get_company_admin():
    """
    Retorna uma versão modificada do CompanyAdmin com informações de pagamento
    """
    from apps.companies.admin import CompanyAdmin
    
    class PaymentCompanyAdmin(CompanyAdmin):
        list_display = CompanyAdmin.list_display + ['payment_info']
        list_filter = [SubscriptionStatusFilter] + CompanyAdmin.list_filter
        
        fieldsets = CompanyAdmin.fieldsets + (
            ('Informações de Pagamento', {
                'fields': ('payment_gateway', 'payment_customer_id'),
                'classes': ('collapse',)
            }),
        )
        
        def payment_info(self, obj):
            if obj.owner.payment_gateway and obj.owner.payment_customer_id:
                gateway = obj.owner.payment_gateway
                customer_id = obj.owner.payment_customer_id[:10] + '...' if len(obj.owner.payment_customer_id) > 10 else obj.owner.payment_customer_id
                
                color = 'green' if gateway == 'stripe' else 'blue'
                return format_html(
                    '<span style="color: {};">{}: {}</span>',
                    color, gateway.title(), customer_id
                )
            return format_html('<span style="color: gray;">Sem pagamento</span>')
        payment_info.short_description = 'Gateway de Pagamento'
        
        def get_queryset(self, request):
            qs = super().get_queryset(request)
            return qs.select_related('owner')
    
    return PaymentCompanyAdmin


# Proxy model para criar uma seção específica de gestão de assinaturas
class SubscriptionManagement(Company):
    """
    Proxy model para gestão de assinaturas no admin
    """
    class Meta:
        proxy = True
        verbose_name = 'Gestão de Assinatura'
        verbose_name_plural = 'Gestão de Assinaturas'


@admin.register(SubscriptionManagement)
class SubscriptionManagementAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'owner_email', 'plan_display',
        'status_display', 'trial_status', 'mrr_display',
        'next_billing_date'
    ]
    list_filter = [
        SubscriptionStatusFilter,
        'subscription_plan',
        'created_at'
    ]
    search_fields = ['name', 'owner__email', 'cnpj']
    date_hierarchy = 'created_at'
    
    readonly_fields = [
        'name', 'owner', 'subscription_plan',
        'subscription_status', 'trial_ends_at',
        'subscription_end_date'
    ]
    
    fieldsets = (
        ('Empresa', {
            'fields': ('name', 'owner')
        }),
        ('Assinatura Atual', {
            'fields': (
                'subscription_plan', 'subscription_status',
                'trial_ends_at', 'subscription_end_date'
            )
        }),
    )
    
    def owner_email(self, obj):
        return obj.owner.email
    owner_email.short_description = 'Email do Proprietário'
    
    def plan_display(self, obj):
        plan = obj.subscription_plan
        return f"{plan.name} (R$ {plan.price_monthly}/mês)"
    plan_display.short_description = 'Plano'
    
    def status_display(self, obj):
        colors = {
            'trial': 'orange',
            'active': 'green',
            'cancelled': 'red',
            'expired': 'gray'
        }
        color = colors.get(obj.subscription_status, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.get_subscription_status_display()
        )
    status_display.short_description = 'Status'
    
    def trial_status(self, obj):
        if obj.subscription_status == 'trial' and obj.trial_ends_at:
            from django.utils import timezone
            days_left = (obj.trial_ends_at - timezone.now()).days
            
            if days_left > 7:
                color = 'green'
            elif days_left > 0:
                color = 'orange'
            else:
                color = 'red'
                
            return format_html(
                '<span style="color: {};">{} dias</span>',
                color, max(0, days_left)
            )
        return '-'
    trial_status.short_description = 'Dias de Trial'
    
    def mrr_display(self, obj):
        if obj.subscription_status == 'active':
            return f"R$ {obj.subscription_plan.price_monthly}"
        return 'R$ 0'
    mrr_display.short_description = 'MRR'
    
    def next_billing_date(self, obj):
        if obj.subscription_status == 'active' and obj.subscription_end_date:
            return obj.subscription_end_date.strftime('%d/%m/%Y')
        return '-'
    next_billing_date.short_description = 'Próxima Cobrança'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('owner', 'subscription_plan')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    actions = ['upgrade_to_pro', 'upgrade_to_enterprise', 'cancel_subscription']
    
    def upgrade_to_pro(self, request, queryset):
        pro_plan = SubscriptionPlan.objects.filter(slug='professional').first()
        if pro_plan:
            count = queryset.update(
                subscription_plan=pro_plan,
                subscription_status='active'
            )
            self.message_user(request, f'{count} empresas atualizadas para o plano Profissional.')
    upgrade_to_pro.short_description = 'Fazer upgrade para Profissional'
    
    def upgrade_to_enterprise(self, request, queryset):
        enterprise_plan = SubscriptionPlan.objects.filter(slug='enterprise').first()
        if enterprise_plan:
            count = queryset.update(
                subscription_plan=enterprise_plan,
                subscription_status='active'
            )
            self.message_user(request, f'{count} empresas atualizadas para o plano Empresarial.')
    upgrade_to_enterprise.short_description = 'Fazer upgrade para Empresarial'
    
    def cancel_subscription(self, request, queryset):
        count = queryset.update(subscription_status='cancelled')
        self.message_user(request, f'{count} assinaturas canceladas.')
    cancel_subscription.short_description = 'Cancelar assinatura'