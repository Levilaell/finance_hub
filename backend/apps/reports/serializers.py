"""
Reports app serializers
"""
from rest_framework import serializers
from .models import Report, ReportTemplate, AIAnalysis, AIAnalysisTemplate


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


class AIAnalysisSerializer(serializers.ModelSerializer):
    """
    AI Analysis serializer for AI-generated financial analyses
    """
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    analysis_type_display = serializers.CharField(source='get_analysis_type_display', read_only=True)
    days_since_created = serializers.SerializerMethodField()
    
    class Meta:
        model = AIAnalysis
        fields = [
            'id', 'title', 'description', 'analysis_type', 'analysis_type_display',
            'period_start', 'period_end', 'analysis_config', 'input_parameters', 'filters',
            'ai_response', 'insights', 'recommendations', 'predictions', 'summary',
            'confidence_score', 'health_score', 'risk_score',
            'is_processed', 'processing_time', 'error_message',
            'cache_key', 'expires_at', 'is_public', 'is_favorite', 'tags',
            'created_at', 'updated_at', 'created_by_name', 'days_since_created'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'is_processed', 'processing_time',
            'cache_key', 'expires_at'
        ]
    
    def get_days_since_created(self, obj):
        """Calculate days since analysis was created"""
        from django.utils import timezone
        delta = timezone.now() - obj.created_at
        return delta.days
    
    def create(self, validated_data):
        validated_data['company'] = self.context['request'].user.company
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AIAnalysisListSerializer(serializers.ModelSerializer):
    """
    Simplified AI Analysis serializer for list views
    """
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    analysis_type_display = serializers.CharField(source='get_analysis_type_display', read_only=True)
    days_since_created = serializers.SerializerMethodField()
    summary_text = serializers.SerializerMethodField()
    
    class Meta:
        model = AIAnalysis
        fields = [
            'id', 'title', 'description', 'analysis_type', 'analysis_type_display',
            'period_start', 'period_end', 'confidence_score', 'health_score',
            'is_processed', 'is_favorite', 'tags', 'created_at', 'created_by_name',
            'days_since_created', 'summary_text'
        ]
    
    def get_days_since_created(self, obj):
        """Calculate days since analysis was created"""
        from django.utils import timezone
        delta = timezone.now() - obj.created_at
        return delta.days
    
    def get_summary_text(self, obj):
        """Get summary text for preview"""
        if obj.summary and 'key_message' in obj.summary:
            return obj.summary['key_message']
        elif obj.insights and len(obj.insights) > 0:
            return obj.insights[0].get('description', '')[:100] + '...'
        return 'Análise disponível'


class AIAnalysisTemplateSerializer(serializers.ModelSerializer):
    """
    AI Analysis Template serializer for reusable AI analysis templates
    """
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    analysis_type_display = serializers.CharField(source='get_analysis_type_display', read_only=True)
    
    class Meta:
        model = AIAnalysisTemplate
        fields = [
            'id', 'name', 'description', 'analysis_type', 'analysis_type_display',
            'template_config', 'prompt_template', 'default_parameters', 'default_filters',
            'output_format', 'visualization_config', 'is_active', 'is_public',
            'created_at', 'updated_at', 'created_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['company'] = self.context['request'].user.company
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)