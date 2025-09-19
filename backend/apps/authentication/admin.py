"""
Django Admin configuration for user authentication models
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, PasswordReset


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for User model
    """
    # Display fields in list view
    list_display = (
        'username', 
        'email', 
        'first_name', 
        'last_name', 
        'is_staff', 
        'is_active',
        'created_at'
    )
    
    # Fields to filter by in the right sidebar
    list_filter = (
        'is_staff', 
        'is_superuser', 
        'is_active', 
        'created_at'
    )
    
    # Fields to search
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    
    # Default ordering
    ordering = ('-created_at',)
    
    # Date hierarchy navigation
    date_hierarchy = 'created_at'
    
    # Fields to display when editing a user
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Additional info'), {
            'fields': ('timezone', 'last_login_ip'),
        }),
    )
    
    # Fields to display when creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone')}),
        (_('Additional info'), {'fields': ('timezone')}),
    )
    
    # Read-only fields
    readonly_fields = ('last_login', 'date_joined', 'created_at', 'updated_at', 'last_login_ip')


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    """
    Admin interface for PasswordReset model
    """
    list_display = ('user', 'token', 'is_used', 'created_at', 'expires_at')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'user__username', 'token')
    readonly_fields = ('token', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    # Disable add permission (password resets should be created programmatically)
    def has_add_permission(self, request):
        return False