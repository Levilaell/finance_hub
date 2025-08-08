from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'user', 'company', 'timestamp', 'success', 'ip_address']
    list_filter = ['event_type', 'success', 'timestamp', 'company']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'description', 'ip_address']
    readonly_fields = ['timestamp', 'content_object']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    # Security: Make all fields read-only since audit logs should not be editable
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete audit logs
