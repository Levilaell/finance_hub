"""
Base admin classes for CaixaHub
Provides performance and consistency improvements
"""
from django.contrib import admin
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