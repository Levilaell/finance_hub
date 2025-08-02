"""
Base admin classes for Finance Hub
Provides security, performance, and consistency improvements
"""
from django.contrib import admin
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html
from django.db.models import Prefetch
import logging

logger = logging.getLogger(__name__)


class BaseModelAdmin(admin.ModelAdmin):
    """
    Base admin class with performance and UX improvements
    """
    # Pagination settings to prevent memory issues
    list_per_page = 100
    list_max_show_all = 500
    
    # UX improvements
    save_on_top = True
    save_as = True
    
    # Performance: Show IDs by default
    list_display_links = ['id']
    
    # Preserve filters after actions
    preserve_filters = True
    
    # Enable search help text
    search_help_text = "Search in the fields configured for this model"
    
    def get_list_display(self, request):
        """Ensure ID is always first in list display"""
        list_display = super().get_list_display(request)
        if 'id' not in list_display:
            return ['id'] + list(list_display)
        return list_display
    
    def log_addition(self, request, obj, message):
        """Enhanced logging for additions"""
        super().log_addition(request, obj, message)
        logger.info(f"Admin ADD: {request.user} added {obj.__class__.__name__} id={obj.pk}")
    
    def log_change(self, request, obj, message):
        """Enhanced logging for changes"""
        super().log_change(request, obj, message)
        logger.info(f"Admin CHANGE: {request.user} changed {obj.__class__.__name__} id={obj.pk}")
    
    def log_deletion(self, request, obj, object_repr):
        """Enhanced logging for deletions"""
        super().log_deletion(request, obj, object_repr)
        logger.info(f"Admin DELETE: {request.user} deleted {obj.__class__.__name__} {object_repr}")
    
    class Media:
        css = {
            'all': ('admin/css/custom-admin.css',)
        }
        js = ('admin/js/custom-admin.js',)


class SecureModelAdmin(BaseModelAdmin):
    """
    Secure admin base class with additional security features
    """
    # Sensitive fields that should never be displayed
    sensitive_fields = [
        'password', 'secret', 'token', 'key', 'hash',
        'two_factor_secret', 'backup_codes', 'api_key',
        'private_key', 'payment_customer_id'
    ]
    
    def get_fields(self, request, obj=None):
        """Remove sensitive fields from display"""
        fields = super().get_fields(request, obj)
        return [f for f in fields if not any(
            sensitive in f.lower() for sensitive in self.sensitive_fields
        )]
    
    def get_readonly_fields(self, request, obj=None):
        """Make audit fields always readonly"""
        readonly = list(super().get_readonly_fields(request, obj))
        audit_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
        for field in audit_fields:
            if hasattr(self.model, field) and field not in readonly:
                readonly.append(field)
        return readonly
    
    def has_delete_permission(self, request, obj=None):
        """Restrict deletion to superusers only"""
        if not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)
    
    def get_queryset(self, request):
        """Apply row-level security"""
        qs = super().get_queryset(request)
        
        # If model has company field and user is not superuser
        if hasattr(self.model, 'company') and not request.user.is_superuser:
            # Filter by user's company
            if hasattr(request.user, 'company'):
                qs = qs.filter(company=request.user.company)
            else:
                # User without company sees nothing
                qs = qs.none()
        
        return qs


class ReadOnlyModelAdmin(BaseModelAdmin):
    """
    Read-only admin for audit and log models
    """
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


class AuditLogAdmin(ReadOnlyModelAdmin):
    """
    Admin for viewing audit logs
    """
    list_display = ['action_time', 'user', 'content_type', 'object_repr', 'action_flag', 'change_message']
    list_filter = ['action_time', 'user', 'content_type', 'action_flag']
    search_fields = ['object_repr', 'change_message', 'user__email']
    date_hierarchy = 'action_time'
    
    def has_module_permission(self, request):
        """Only superusers can view audit logs"""
        return request.user.is_superuser


# Register the audit log admin
admin.site.register(LogEntry, AuditLogAdmin)