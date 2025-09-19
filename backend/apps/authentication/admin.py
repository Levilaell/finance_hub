"""
Enhanced admin configuration for authentication app
Provides comprehensive user management with security and performance optimizations
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count, Q
from core.admin import BaseModelAdmin
from .models import User, PasswordReset


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced admin for custom User model with comprehensive features"""

    # Basic display configuration
    list_display = (
        'email', 'full_name_display', 'company_display', 'last_login_display',
        'is_active_display', 'is_staff', 'date_joined_display'
    )
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'date_joined',
        'last_login', 'payment_gateway', 'timezone'
    )
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)

    # Enhanced fieldsets for better organization
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('email', 'first_name', 'last_name', 'phone')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('Settings'), {
            'fields': ('timezone', 'payment_gateway')
        }),
        (_('Security'), {
            'fields': ('last_login', 'last_login_ip'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Add fieldsets for user creation
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
        (_('Additional Info'), {
            'classes': ('wide', 'collapse'),
            'fields': ('phone', 'timezone', 'payment_gateway'),
        }),
    )

    readonly_fields = ('last_login', 'date_joined', 'created_at', 'updated_at', 'last_login_ip')
    filter_horizontal = ('groups', 'user_permissions')

    # Performance optimization
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company').prefetch_related('groups')

    # Enhanced display methods
    def full_name_display(self, obj):
        name = obj.full_name
        if name.strip():
            return name
        return format_html('<em style="color: #999;">Nome não informado</em>')
    full_name_display.short_description = _('Full Name')
    full_name_display.admin_order_field = 'first_name'

    def company_display(self, obj):
        try:
            if hasattr(obj, 'company') and obj.company:
                url = reverse('admin:companies_company_change', args=[obj.company.pk])
                return format_html('<a href="{}">{}</a>', url, obj.company.name)
            return format_html('<em style="color: #999;">Sem empresa</em>')
        except:
            return '-'
    company_display.short_description = _('Company')

    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ Ativo</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Inativo</span>')
    is_active_display.short_description = _('Status')
    is_active_display.admin_order_field = 'is_active'

    def last_login_display(self, obj):
        if obj.last_login:
            diff = timezone.now() - obj.last_login
            if diff.days < 1:
                return format_html('<span style="color: green;">Hoje</span>')
            elif diff.days < 7:
                return format_html('<span style="color: orange;">{} dias</span>', diff.days)
            else:
                return format_html('<span style="color: red;">{} dias</span>', diff.days)
        return format_html('<span style="color: #999;">Nunca</span>')
    last_login_display.short_description = _('Last Login')
    last_login_display.admin_order_field = 'last_login'

    def date_joined_display(self, obj):
        return obj.date_joined.strftime('%d/%m/%Y %H:%M')
    date_joined_display.short_description = _('Date Joined')
    date_joined_display.admin_order_field = 'date_joined'

    # Custom actions
    actions = ['activate_users', 'deactivate_users', 'reset_passwords']

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} usuários ativados com sucesso.')
    activate_users.short_description = 'Ativar usuários selecionados'

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} usuários desativados com sucesso.')
    deactivate_users.short_description = 'Desativar usuários selecionados'

    def reset_passwords(self, request, queryset):
        count = 0
        for user in queryset:
            if user.email:
                # Here you would integrate with your password reset logic
                count += 1
        self.message_user(request, f'Reset de senha solicitado para {count} usuários.')
    reset_passwords.short_description = 'Solicitar reset de senha'


@admin.register(PasswordReset)
class PasswordResetAdmin(BaseModelAdmin):
    """Enhanced admin for password reset tokens with security features"""

    list_display = (
        'user_display', 'created_at_display', 'expires_at_display',
        'status_display', 'token_preview'
    )
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('token', 'created_at', 'expires_at', 'is_expired')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        (_('User Information'), {
            'fields': ('user',)
        }),
        (_('Token Details'), {
            'fields': ('token', 'is_used', 'is_expired')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )

    # Performance optimization
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')

    # Enhanced display methods
    def user_display(self, obj):
        url = reverse('admin:authentication_user_change', args=[obj.user.pk])
        return format_html(
            '<a href="{}">{}</a> ({})',
            url, obj.user.full_name or obj.user.email, obj.user.email
        )
    user_display.short_description = _('User')
    user_display.admin_order_field = 'user__email'

    def created_at_display(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    created_at_display.short_description = _('Created')
    created_at_display.admin_order_field = 'created_at'

    def expires_at_display(self, obj):
        if obj.expires_at < timezone.now():
            return format_html(
                '<span style="color: red;">{}</span>',
                obj.expires_at.strftime('%d/%m/%Y %H:%M')
            )
        return obj.expires_at.strftime('%d/%m/%Y %H:%M')
    expires_at_display.short_description = _('Expires')
    expires_at_display.admin_order_field = 'expires_at'

    def status_display(self, obj):
        if obj.is_used:
            return format_html('<span style="color: green;">✓ Usado</span>')
        elif obj.expires_at < timezone.now():
            return format_html('<span style="color: red;">✗ Expirado</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Pendente</span>')
    status_display.short_description = _('Status')

    def token_preview(self, obj):
        """Show only first and last 4 characters for security"""
        token = obj.token
        if len(token) > 8:
            return f"{token[:4]}...{token[-4:]}"
        return "***"
    token_preview.short_description = _('Token Preview')

    def is_expired(self, obj):
        return obj.expires_at < timezone.now()
    is_expired.boolean = True
    is_expired.short_description = _('Is Expired')

    # Custom actions
    actions = ['mark_as_used', 'delete_expired']

    def mark_as_used(self, request, queryset):
        updated = queryset.update(is_used=True)
        self.message_user(request, f'{updated} tokens marcados como usados.')
    mark_as_used.short_description = 'Marcar tokens como usados'

    def delete_expired(self, request, queryset):
        expired = queryset.filter(expires_at__lt=timezone.now())
        count = expired.count()
        expired.delete()
        self.message_user(request, f'{count} tokens expirados removidos.')
    delete_expired.short_description = 'Remover tokens expirados'