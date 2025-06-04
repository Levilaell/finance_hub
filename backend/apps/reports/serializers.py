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
            'id', 'report_type', 'title', 'period_start', 'period_end',
            'status', 'file_path', 'file_size', 'file_size_mb', 'error_message',
            'created_at', 'completed_at', 'created_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'completed_at', 'file_size']
    
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
    next_run_date = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = ReportSchedule
        fields = [
            'id', 'name', 'report_type', 'frequency', 'day_of_month',
            'day_of_week', 'is_active', 'email_recipients', 'next_run_date',
            'last_run_date', 'run_count', 'created_at', 'created_by_name'
        ]
        read_only_fields = ['id', 'last_run_date', 'run_count', 'created_at']
    
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
            'id', 'name', 'description', 'template_config', 'is_system',
            'is_active', 'created_at', 'created_by_name'
        ]
        read_only_fields = ['id', 'is_system', 'created_at']
    
    def create(self, validated_data):
        validated_data['company'] = self.context['request'].user.company
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)