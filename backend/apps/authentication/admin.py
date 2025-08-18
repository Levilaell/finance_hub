"""
Django Admin configuration for authentication app
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from .models import User, PasswordReset  # EmailVerification will be implemented in the future
from django.contrib.admin import SimpleListFilter
from core.admin import SecureModelAdmin


class SubscriptionPlanFilter(SimpleListFilter):
    title = 'Plano de Assinatura'
    parameter_name = 'subscription_plan'
    
    def lookups(self, request, model_admin):
        # Import here to avoid circular imports
        from apps.companies.models import SubscriptionPlan
        
        plans = SubscriptionPlan.objects.filter(is_active=True).values_list('id', 'name')
        lookups = list(plans)
        lookups.append(('none', 'Sem Plano'))
        return lookups
    
    def queryset(self, request, queryset):
        if self.value() == 'none':
            return queryset.filter(company__isnull=True)
        elif self.value():
            return queryset.filter(company__subscription_plan_id=self.value())
        return queryset


class SubscriptionStatusFilter(SimpleListFilter):
    title = 'Status da Assinatura'
    parameter_name = 'subscription_status'
    
    def lookups(self, request, model_admin):
        return [
            ('trial', 'Período de Teste'),
            ('active', 'Ativo'),
            ('past_due', 'Em Atraso'),
            ('cancelled', 'Cancelado'),
            ('suspended', 'Suspenso'),
            ('expired', 'Expirado'),
            ('none', 'Sem Empresa'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'none':
            return queryset.filter(company__isnull=True)
        elif self.value():
            return queryset.filter(company__subscription_status=self.value())
        return queryset


class TrialExpiringFilter(SimpleListFilter):
    title = 'Trial Expirando'
    parameter_name = 'trial_expiring'
    
    def lookups(self, request, model_admin):
        return [
            ('3', 'Próximos 3 dias'),
            ('7', 'Próximos 7 dias'),
            ('expired', 'Expirado'),
        ]
    
    def queryset(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        
        if self.value() == '3':
            end_date = timezone.now() + timedelta(days=3)
            return queryset.filter(
                company__subscription_status='trial',
                company__trial_ends_at__lte=end_date,
                company__trial_ends_at__gt=timezone.now()
            )
        elif self.value() == '7':
            end_date = timezone.now() + timedelta(days=7)
            return queryset.filter(
                company__subscription_status='trial',
                company__trial_ends_at__lte=end_date,
                company__trial_ends_at__gt=timezone.now()
            )
        elif self.value() == 'expired':
            return queryset.filter(
                company__subscription_status='trial',
                company__trial_ends_at__lt=timezone.now()
            )
        return queryset


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin interface
    """
    # Display fields in list view
    list_display = (
        'email', 'full_name_display', 'company_display',
        'plan_display', 'subscription_status_display', 'trial_info',
        'is_active', 'two_fa_status', 'created_at'  # is_email_verified will be added when implemented
    )
    list_filter = (
        'is_active', 'is_staff', 'is_superuser',
        # 'is_email_verified',  # Will be added when email verification is implemented
        'is_phone_verified',
        'is_two_factor_enabled', 'preferred_language',
        'payment_gateway',
        SubscriptionPlanFilter,
        SubscriptionStatusFilter,
        TrialExpiringFilter,
    )
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)
    
    # Fieldsets for the detail view
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar', 'date_of_birth')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Verification'), {
            'fields': ('is_phone_verified',),  # is_email_verified will be added when implemented
        }),
        (_('Preferences'), {
            'fields': ('preferred_language', 'timezone'),
        }),
        (_('Two Factor Authentication'), {
            'fields': ('is_two_factor_enabled',),
            'classes': ('collapse',),
            'description': 'Two-factor authentication status. Secret keys are not displayed for security.',
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
        (_('Subscription Info'), {
            'fields': ('get_subscription_info',),
            'classes': ('wide',),
        }),
    )
    
    # Fieldsets for adding new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    
    # Read-only fields
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'get_subscription_info')
    
    # Filter horizontal for many-to-many fields
    filter_horizontal = ('groups', 'user_permissions')
    
    # Actions
    actions = ['make_active', 'make_inactive', 'verify_email', 'show_subscription_summary']
    
    def make_active(self, request, queryset):
        """Mark selected users as active"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users marked as active.')
    make_active.short_description = "Mark selected users as active"
    
    def make_inactive(self, request, queryset):
        """Mark selected users as inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users marked as inactive.')
    make_inactive.short_description = "Mark selected users as inactive"
    
    def verify_email(self, request, queryset):
        """Mark selected users' emails as verified"""
        # Email verification will be implemented in the future
        # updated = queryset.update(is_email_verified=True)
        updated = 0  # Temporary until email verification is implemented
        self.message_user(request, f'{updated} users\' emails marked as verified.')
    verify_email.short_description = "Mark selected users' emails as verified"
    
    def show_subscription_summary(self, request, queryset):
        """Show subscription summary for selected users"""
        from django.contrib import messages
        
        summary = {
            'total': queryset.count(),
            'with_company': 0,
            'without_company': 0,
            'by_plan': {},
            'by_status': {},
            'trial_expiring': 0,
        }
        
        from django.utils import timezone
        from datetime import timedelta
        
        for user in queryset.select_related('company', 'company__subscription_plan'):
            if hasattr(user, 'company'):
                summary['with_company'] += 1
                
                # Count by plan
                plan_name = user.company.subscription_plan.name if user.company.subscription_plan else 'Sem Plano'
                summary['by_plan'][plan_name] = summary['by_plan'].get(plan_name, 0) + 1
                
                # Count by status
                status = user.company.get_subscription_status_display()
                summary['by_status'][status] = summary['by_status'].get(status, 0) + 1
                
                # Check trial expiring
                if (user.company.subscription_status == 'trial' and 
                    user.company.trial_ends_at and
                    user.company.trial_ends_at <= timezone.now() + timedelta(days=7)):
                    summary['trial_expiring'] += 1
            else:
                summary['without_company'] += 1
        
        # Build message
        msg_parts = [
            f"Resumo de {summary['total']} usuário(s):",
            f"• Com empresa: {summary['with_company']}",
            f"• Sem empresa: {summary['without_company']}",
            "",
            "Por plano:"
        ]
        
        for plan, count in summary['by_plan'].items():
            msg_parts.append(f"  • {plan}: {count}")
        
        msg_parts.append("")
        msg_parts.append("Por status:")
        
        for status, count in summary['by_status'].items():
            msg_parts.append(f"  • {status}: {count}")
        
        if summary['trial_expiring'] > 0:
            msg_parts.append("")
            msg_parts.append(f"⚠️ {summary['trial_expiring']} usuário(s) com trial expirando em 7 dias")
        
        messages.info(request, '\n'.join(msg_parts))
    
    show_subscription_summary.short_description = "Mostrar resumo de assinaturas"
    
    # Custom display methods
    def full_name_display(self, obj):
        """Display user's full name"""
        return obj.get_full_name() or obj.email
    full_name_display.short_description = 'Nome completo'
    
    def company_display(self, obj):
        """Display user's company"""
        # Check if user is owner of a company
        if hasattr(obj, 'company'):
            url = reverse('admin:companies_company_change', args=[obj.company.id])
            return format_html('<a href="{}">{} (Proprietário)</a>', url, obj.company.name)
        
        return format_html('<span style="color: gray;">Sem empresa</span>')
    company_display.short_description = 'Empresa'
    
    def two_fa_status(self, obj):
        """Display 2FA status with visual indicator"""
        if obj.is_two_factor_enabled:
            return format_html(
                '<span style="color: green;">✓ Ativado</span>'
            )
        return format_html(
            '<span style="color: gray;">✗ Desativado</span>'
        )
    two_fa_status.short_description = '2FA'
    
    def plan_display(self, obj):
        """Display user's subscription plan"""
        if hasattr(obj, 'company') and obj.company.subscription_plan:
            plan = obj.company.subscription_plan
            color = {
                'starter': 'blue',
                'professional': 'green',
                'enterprise': 'purple'
            }.get(plan.plan_type, 'gray')
            
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
                color,
                plan.name
            )
        return format_html('<span style="color: gray;">—</span>')
    plan_display.short_description = 'Plano'
    
    def subscription_status_display(self, obj):
        """Display subscription status with color coding"""
        if hasattr(obj, 'company'):
            status = obj.company.subscription_status
            status_config = {
                'trial': ('Teste', 'orange'),
                'active': ('Ativo', 'green'),
                'past_due': ('Atrasado', 'red'),
                'cancelled': ('Cancelado', 'gray'),
                'suspended': ('Suspenso', 'red'),
                'expired': ('Expirado', 'darkred')
            }
            
            label, color = status_config.get(status, (status, 'gray'))
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color,
                label
            )
        return format_html('<span style="color: gray;">—</span>')
    subscription_status_display.short_description = 'Status'
    
    def trial_info(self, obj):
        """Display trial information"""
        if hasattr(obj, 'company'):
            company = obj.company
            if company.subscription_status == 'trial' and company.trial_ends_at:
                from django.utils import timezone
                from datetime import timedelta
                
                now = timezone.now()
                trial_end = company.trial_ends_at
                
                if trial_end > now:
                    days_left = (trial_end - now).days
                    if days_left <= 3:
                        color = 'red'
                    elif days_left <= 7:
                        color = 'orange'
                    else:
                        color = 'green'
                    
                    return format_html(
                        '<span style="color: {};">{} dias restantes</span>',
                        color,
                        days_left
                    )
                else:
                    return format_html('<span style="color: red;">Expirado</span>')
            elif company.subscription_status == 'active':
                if company.next_billing_date:
                    return format_html(
                        '<span style="color: gray;">Próx. cobrança: {}</span>',
                        company.next_billing_date.strftime('%d/%m/%Y')
                    )
        return format_html('<span style="color: gray;">—</span>')
    trial_info.short_description = 'Trial/Cobrança'
    
    def get_subscription_info(self, obj):
        """Display detailed subscription information"""
        if not hasattr(obj, 'company'):
            return format_html('<p style="color: gray;">Usuário sem empresa associada</p>')
        
        company = obj.company
        plan = company.subscription_plan
        
        info_html = []
        info_html.append('<div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">')
        
        # Basic Info
        info_html.append(f'<h4 style="margin-top: 0;">Informações da Assinatura</h4>')
        info_html.append(f'<p><strong>Empresa:</strong> {company.name} (CNPJ: {company.cnpj or "Não informado"})</p>')
        
        if plan:
            info_html.append(f'<p><strong>Plano:</strong> {plan.name} ({plan.plan_type})</p>')
            info_html.append(f'<p><strong>Preço:</strong> R$ {plan.price_monthly}/mês ou R$ {plan.price_yearly}/ano</p>')
        else:
            info_html.append('<p><strong>Plano:</strong> <span style="color: red;">Nenhum plano selecionado</span></p>')
        
        # Status
        status_color = {
            'trial': 'orange',
            'active': 'green',
            'past_due': 'red',
            'cancelled': 'gray',
            'suspended': 'red',
            'expired': 'darkred'
        }.get(company.subscription_status, 'gray')
        
        info_html.append(f'<p><strong>Status:</strong> <span style="color: {status_color}; font-weight: bold;">{company.get_subscription_status_display()}</span></p>')
        
        # Dates
        if company.trial_ends_at:
            info_html.append(f'<p><strong>Trial expira em:</strong> {company.trial_ends_at.strftime("%d/%m/%Y %H:%M")}</p>')
        if company.subscription_start_date:
            info_html.append(f'<p><strong>Início da assinatura:</strong> {company.subscription_start_date.strftime("%d/%m/%Y")}</p>')
        if company.next_billing_date:
            info_html.append(f'<p><strong>Próxima cobrança:</strong> {company.next_billing_date.strftime("%d/%m/%Y")}</p>')
        
        # Usage
        info_html.append('<h4>Uso Atual</h4>')
        info_html.append(f'<p><strong>Transações este mês:</strong> {company.current_month_transactions}</p>')
        info_html.append(f'<p><strong>Requisições IA este mês:</strong> {company.current_month_ai_requests}</p>')
        
        if hasattr(company, 'bank_accounts'):
            active_accounts = company.bank_accounts.filter(is_active=True).count()
            info_html.append(f'<p><strong>Contas bancárias ativas:</strong> {active_accounts}</p>')
        
        # Payment Info
        if obj.payment_customer_id:
            info_html.append('<h4>Informações de Pagamento</h4>')
            info_html.append(f'<p><strong>Gateway:</strong> {obj.payment_gateway or "Não configurado"}</p>')
            # Customer ID hidden for security - only show payment gateway
            info_html.append(f'<p><strong>Payment Configured:</strong> ✓ {obj.payment_gateway or "Not configured"}</p>')
        
        info_html.append('</div>')
        
        return format_html(''.join(info_html))
    get_subscription_info.short_description = 'Detalhes da Assinatura'
    
    def get_queryset(self, request):
        """Optimize queries to prevent N+1 issues"""
        qs = super().get_queryset(request)
        # Prefetch related company and subscription data
        return qs.select_related(
            'company',
            'company__subscription_plan'
        )


# Email verification will be implemented in the future
# @admin.register(EmailVerification)
# class EmailVerificationAdmin(admin.ModelAdmin):
#     """
#     Admin interface for email verifications
#     """
#     list_display = [
#         'user_email', 'token_display', 'is_used',
#         'created_at', 'expires_at_display'
#     ]
#     list_filter = ['is_used', 'created_at']
#     search_fields = ['user__email', 'token']
#     date_hierarchy = 'created_at'
#     ordering = ['-created_at']
#     
#     readonly_fields = ['token', 'created_at']
#     
#     def user_email(self, obj):
#         return obj.user.email
#     user_email.short_description = 'Email do Usuário'
#     
#     def token_display(self, obj):
#         # Show only first and last 2 chars for security
#         if len(obj.token) > 4:
#             return f"{obj.token[:2]}...{obj.token[-2:]}"
#         return obj.token
#     token_display.short_description = 'Token'
#     
#     def expires_at_display(self, obj):
#         from django.utils import timezone
#         if obj.expires_at > timezone.now():
#             time_left = obj.expires_at - timezone.now()
#             hours = time_left.total_seconds() // 3600
#             minutes = (time_left.total_seconds() % 3600) // 60
#             return format_html(
#                 '<span style="color: green;">{}h {}m</span>',
#                 int(hours), int(minutes)
#             )
#         return format_html('<span style="color: red;">Expirado</span>')
#     expires_at_display.short_description = 'Expira em'
#     
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         return qs.select_related('user')
#     
#     actions = ['mark_as_used']
#     
#     def mark_as_used(self, request, queryset):
#         count = 0
#         for verification in queryset.filter(is_used=False):
#             verification.is_used = True
#             verification.user.is_email_verified = True
#             verification.save()
#             verification.user.save()
#             count += 1
#         self.message_user(request, f'{count} verificações marcadas como usadas.')
#     mark_as_used.short_description = 'Marcar como usado'


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    """
    Admin interface for password reset tokens
    """
    list_display = [
        'user_email', 'token_display', 'is_used',
        'created_at', 'expires_at_display'
    ]
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    readonly_fields = ['token', 'created_at']
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user',)
        }),
        ('Token', {
            'fields': ('token', 'is_used')
        }),
        ('Validade', {
            'fields': ('created_at', 'expires_at')
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def token_display(self, obj):
        # Show only first and last 4 chars for security
        if len(obj.token) > 8:
            return f"{obj.token[:4]}...{obj.token[-4:]}"
        return obj.token
    token_display.short_description = 'Token'
    
    def expires_at_display(self, obj):
        from django.utils import timezone
        if obj.expires_at > timezone.now():
            time_left = obj.expires_at - timezone.now()
            hours = time_left.total_seconds() // 3600
            minutes = (time_left.total_seconds() % 3600) // 60
            return format_html(
                '<span style="color: green;">{}h {}m</span>',
                int(hours), int(minutes)
            )
        return format_html('<span style="color: red;">Expirado</span>')
    expires_at_display.short_description = 'Expira em'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')
    
    def has_add_permission(self, request):
        # Prevent manual creation of tokens
        return False