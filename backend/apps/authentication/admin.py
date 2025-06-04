"""
Django Admin configuration for authentication app
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin interface
    """
    # Display fields in list view
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_email_verified', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'is_email_verified', 'is_phone_verified', 'preferred_language')
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