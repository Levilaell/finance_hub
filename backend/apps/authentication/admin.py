"""
Django Admin configuration for authentication app
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from .models import User, EmailVerification, PasswordReset


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin interface
    """
    # Display fields in list view
    list_display = (
        'email', 'full_name_display', 'company_display',
        'is_active', 'is_staff', 'is_email_verified',
        'two_fa_status', 'created_at'
    )
    list_filter = (
        'is_active', 'is_staff', 'is_superuser',
        'is_email_verified', 'is_phone_verified',
        'is_two_factor_enabled', 'preferred_language',
        'payment_gateway'
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
            'fields': ('is_email_verified', 'is_phone_verified'),
        }),
        (_('Preferences'), {
            'fields': ('preferred_language', 'timezone'),
        }),
        (_('Two Factor Authentication'), {
            'fields': ('is_two_factor_enabled', 'two_factor_secret', 'backup_codes'),
            'classes': ('collapse',),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',),
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
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    
    # Filter horizontal for many-to-many fields
    filter_horizontal = ('groups', 'user_permissions')
    
    # Actions
    actions = ['make_active', 'make_inactive', 'verify_email']
    
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
        updated = queryset.update(is_email_verified=True)
        self.message_user(request, f'{updated} users\' emails marked as verified.')
    verify_email.short_description = "Mark selected users' emails as verified"
    
    # Custom display methods
    def full_name_display(self, obj):
        """Display user's full name"""
        return obj.get_full_name() or obj.email
    full_name_display.short_description = 'Nome completo'
    
    def company_display(self, obj):
        """Display user's companies"""
        company_links = []
        
        # Check if user is owner of a company
        if hasattr(obj, 'company'):
            url = reverse('admin:companies_company_change', args=[obj.company.id])
            link = format_html('<a href="{}">{} (Proprietário)</a>', url, obj.company.name)
            company_links.append(link)
        
        # Check if user is member of other companies
        companies = obj.company_memberships.filter(is_active=True).select_related('company')
        for cu in companies[:3]:  # Show max 3 companies
            if not hasattr(obj, 'company') or cu.company.id != obj.company.id:
                url = reverse('admin:companies_company_change', args=[cu.company.id])
                role = cu.role.capitalize() if hasattr(cu, 'role') else 'Membro'
                link = format_html('<a href="{}">{} ({})</a>', url, cu.company.name, role)
                company_links.append(link)
        
        if companies.count() > 3:
            company_links.append(f'... (+{companies.count() - 3})')
        
        if company_links:
            return format_html(', '.join(company_links))
        return format_html('<span style="color: gray;">Sem empresa</span>')
    company_display.short_description = 'Empresas'
    
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


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    """
    Admin interface for email verifications
    """
    list_display = [
        'user_email', 'token_display', 'is_used',
        'created_at', 'expires_at_display'
    ]
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email', 'token']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    readonly_fields = ['token', 'created_at']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email do Usuário'
    
    def token_display(self, obj):
        # Show only first and last 2 chars for security
        if len(obj.token) > 4:
            return f"{obj.token[:2]}...{obj.token[-2:]}"
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
    
    actions = ['mark_as_used']
    
    def mark_as_used(self, request, queryset):
        count = 0
        for verification in queryset.filter(is_used=False):
            verification.is_used = True
            verification.user.is_email_verified = True
            verification.save()
            verification.user.save()
            count += 1
        self.message_user(request, f'{count} verificações marcadas como usadas.')
    mark_as_used.short_description = 'Marcar como usado'


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