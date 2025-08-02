"""
Admin mixins for enhanced functionality
"""
import csv
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.template.response import TemplateResponse
import json


class ExportMixin:
    """
    Mixin to add export functionality to admin classes
    """
    export_fields = None  # Override to specify fields to export
    
    def get_export_fields(self):
        """Get fields to export, defaults to list_display"""
        if self.export_fields:
            return self.export_fields
        return self.get_list_display(None)
    
    @admin.action(description='Export selected items to CSV')
    def export_as_csv(self, request, queryset):
        """Export selected items as CSV"""
        meta = self.model._meta
        field_names = self.get_export_fields()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta}-{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        writer = csv.writer(response)
        writer.writerow(field_names)
        
        for obj in queryset:
            row = []
            for field in field_names:
                if hasattr(obj, field):
                    value = getattr(obj, field)
                    if callable(value):
                        value = value()
                    row.append(str(value))
                else:
                    # Check if it's a method on the admin
                    if hasattr(self, field):
                        value = getattr(self, field)(obj)
                        row.append(str(value))
                    else:
                        row.append('')
            writer.writerow(row)
        
        return response
    
    @admin.action(description='Export selected items to JSON')
    def export_as_json(self, request, queryset):
        """Export selected items as JSON"""
        meta = self.model._meta
        field_names = self.get_export_fields()
        
        data = []
        for obj in queryset:
            item = {}
            for field in field_names:
                if hasattr(obj, field):
                    value = getattr(obj, field)
                    if callable(value):
                        value = value()
                    # Convert non-serializable types
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    item[field] = value
                else:
                    # Check if it's a method on the admin
                    if hasattr(self, field):
                        value = getattr(self, field)(obj)
                        item[field] = str(value)
                    else:
                        item[field] = None
            data.append(item)
        
        response = HttpResponse(
            json.dumps(data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename={meta}-{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        return response
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        actions['export_as_csv'] = (
            self.export_as_csv,
            'export_as_csv',
            'Export selected items to CSV'
        )
        actions['export_as_json'] = (
            self.export_as_json,
            'export_as_json',
            'Export selected items to JSON'
        )
        return actions


class BulkUpdateMixin:
    """
    Mixin to add bulk update functionality
    """
    bulk_update_fields = []  # Fields that can be bulk updated
    
    @admin.action(description='Bulk update selected items')
    def bulk_update(self, request, queryset):
        """Show bulk update form"""
        if 'apply' in request.POST:
            # Process the bulk update
            updated_count = 0
            for field in self.bulk_update_fields:
                if field in request.POST and request.POST[field]:
                    update_dict = {field: request.POST[field]}
                    updated_count = queryset.update(**update_dict)
            
            self.message_user(request, f'Successfully updated {updated_count} items.')
            return None
        
        context = {
            'title': 'Bulk Update',
            'queryset': queryset,
            'opts': self.model._meta,
            'fields': self.bulk_update_fields,
            'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        }
        
        return TemplateResponse(
            request,
            'admin/bulk_update.html',
            context
        )
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if self.bulk_update_fields:
            actions['bulk_update'] = (
                self.bulk_update,
                'bulk_update',
                'Bulk update selected items'
            )
        return actions


class StatusColorMixin:
    """
    Mixin to add colored status displays
    """
    status_colors = {
        'active': 'green',
        'inactive': 'red',
        'pending': 'orange',
        'trial': 'blue',
        'expired': 'darkred',
        'success': 'green',
        'failed': 'red',
        'error': 'red',
        'warning': 'orange',
        'info': 'blue',
    }
    
    def colored_status(self, obj, field='status'):
        """Display status with color coding"""
        value = getattr(obj, field, None)
        if not value:
            return '-'
        
        # Check if it's a choice field
        if hasattr(obj, f'get_{field}_display'):
            display_value = getattr(obj, f'get_{field}_display')()
        else:
            display_value = value
        
        # Get color
        color = self.status_colors.get(value.lower(), 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            display_value
        )


class InlineCountMixin:
    """
    Mixin to show count of inline items
    """
    def get_inline_count(self, obj, inline_model):
        """Get count of related inline items"""
        if hasattr(obj, inline_model):
            related = getattr(obj, inline_model)
            if hasattr(related, 'count'):
                return related.count()
            elif hasattr(related, 'all'):
                return related.all().count()
        return 0


class AdminStatsMixin:
    """
    Mixin to add statistics to admin changelist
    """
    def changelist_view(self, request, extra_context=None):
        """Add statistics to changelist view"""
        response = super().changelist_view(request, extra_context)
        
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
        
        # Calculate basic metrics
        metrics = {
            'total_count': qs.count(),
        }
        
        # Add model-specific metrics
        if hasattr(self, 'get_metrics'):
            metrics.update(self.get_metrics(qs))
        
        if extra_context is None:
            extra_context = {}
        extra_context['metrics'] = metrics
        
        response.context_data.update(extra_context)
        return response