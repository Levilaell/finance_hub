"""
Django Admin configuration for user authentication models
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import User, PasswordReset, UserActivityLog


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
        'acquisition_angle',
        'is_staff',
        'is_active',
        'created_at'
    )

    # Fields to filter by in the right sidebar
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'acquisition_angle',
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
        (_('Acquisition tracking'), {
            'fields': ('signup_price_id', 'acquisition_angle'),
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
    readonly_fields = ('last_login', 'date_joined', 'created_at', 'updated_at', 'last_login_ip', 'signup_price_id', 'acquisition_angle')


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


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    """
    Admin interface for UserActivityLog model
    """
    list_display = ('user', 'event_type_colored', 'ip_address', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('user__email', 'user__username', 'ip_address', 'user_agent')
    readonly_fields = ('user', 'event_type', 'ip_address', 'user_agent', 'metadata', 'created_at', 'metadata_formatted')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    # Custom display for event type with color coding
    def event_type_colored(self, obj):
        colors = {
            'login': '#10b981',  # green
            'logout': '#6b7280',  # gray
            'bank_connection_created': '#3b82f6',  # blue
            'bank_connection_updated': '#f59e0b',  # amber
            'bank_connection_deleted': '#ef4444',  # red
            'sync_started': '#8b5cf6',  # purple
            'sync_completed': '#10b981',  # green
            'sync_failed': '#ef4444',  # red
            'password_reset_requested': '#f59e0b',  # amber
            'password_changed': '#10b981',  # green
            'profile_updated': '#3b82f6',  # blue
        }
        color = colors.get(obj.event_type, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_event_type_display()
        )
    event_type_colored.short_description = 'Event Type'

    # Format metadata for better readability
    def metadata_formatted(self, obj):
        if not obj.metadata:
            return '-'
        import json
        formatted_json = json.dumps(obj.metadata, indent=2, ensure_ascii=False)
        return format_html('<pre style="margin: 0;">{}</pre>', formatted_json)
    metadata_formatted.short_description = 'Metadata (Formatted)'

    # Disable add and change permissions (logs should be created programmatically)
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False