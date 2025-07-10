"""
Reports app serializers
"""
from rest_framework import serializers
from .models import Report, ReportSchedule, ReportTemplate


class ReportSerializer(serializers.ModelSerializer):
    """
    Report serializer for financial reports
    """
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'report_type', 'title', 'description', 'period_start', 'period_end',
            'file_format', 'is_generated', 'file', 'file_size', 'file_size_mb', 
            'generation_time', 'error_message', 'created_at', 'created_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'file_size', 'is_generated', 'generation_time']
    
    def get_file_size_mb(self, obj):
        """Convert file size to MB"""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return None


class ReportScheduleSerializer(serializers.ModelSerializer):
    """
    Report schedule serializer for automated reports
    """
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = ReportSchedule
        fields = [
            'id', 'name', 'report_type', 'frequency', 'send_email', 'email_recipients',
            'file_format', 'is_active', 'next_run_at', 'last_run_at',
            'parameters', 'filters', 'created_at', 'created_by_name'
        ]
        read_only_fields = ['id', 'last_run_at', 'created_at']
    
    def create(self, validated_data):
        validated_data['company'] = self.context['request'].user.company
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ReportTemplateSerializer(serializers.ModelSerializer):
    """
    Report template serializer for custom report templates
    """
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'description', 'report_type', 'template_config', 
            'charts', 'default_parameters', 'default_filters', 'is_public',
            'is_active', 'created_at', 'updated_at', 'created_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['company'] = self.context['request'].user.company
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)