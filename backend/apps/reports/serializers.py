"""
Reports app serializers
"""
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Report, ReportTemplate
from .services.validation_service import ReportValidationService


class ReportSerializer(serializers.ModelSerializer):
    """
    Report serializer for financial reports with enhanced validation
    """
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'report_type', 'title', 'description', 'period_start', 'period_end',
            'file_format', 'is_generated', 'file', 'file_size', 'file_size_mb',
            'error_message', 'created_at', 'created_by_name',
            'download_url', 'status', 'parameters', 'filters'
        ]
        read_only_fields = ['id', 'created_at', 'file_size', 'is_generated']
    
    def get_file_size_mb(self, obj):
        """Convert file size to MB"""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return None
    
    def get_download_url(self, obj):
        """Get secure download URL if report is generated"""
        if obj.is_generated and obj.file:
            from django.core.signing import TimestampSigner
            signer = TimestampSigner()
            signed_id = signer.sign(str(obj.id))
            return f"/api/reports/secure-download/{signed_id}/"
        return None
    
    def get_status(self, obj):
        """Get report status"""
        if obj.is_generated:
            return 'completed'
        elif obj.error_message:
            return 'failed'
        else:
            return 'processing'
    
    def validate(self, attrs):
        """Validate report data using validation service"""
        try:
            # Get company from context
            company = self.context['request'].user.company
            
            # Prepare data for validation
            validation_data = {
                'report_type': attrs.get('report_type'),
                'period_start': attrs.get('period_start'),
                'period_end': attrs.get('period_end'),
                'file_format': attrs.get('file_format', 'pdf'),
                'title': attrs.get('title'),
                'description': attrs.get('description'),
                'filters': attrs.get('filters', {}),
                'parameters': attrs.get('parameters', {})
            }
            
            # Validate using service
            validated_data = ReportValidationService.validate_report_request(
                validation_data,
                company
            )
            
            # Update attrs with validated data
            attrs.update(validated_data)
            
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        except Exception as e:
            raise serializers.ValidationError(f"Validation error: {str(e)}")
        
        return attrs


class ReportTemplateSerializer(serializers.ModelSerializer):
    """
    Report template serializer for custom report templates with validation
    """
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    usage_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'description', 'report_type', 'template_config', 
            'charts', 'default_parameters', 'default_filters', 'is_public',
            'is_active', 'created_at', 'updated_at', 'created_by_name',
            'usage_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_usage_count(self, obj):
        """Get number of reports generated from this template"""
        return obj.reports.count() if hasattr(obj, 'reports') else 0
    
    def validate(self, attrs):
        """Validate template data"""
        try:
            # Prepare data for validation
            validation_data = {
                'name': attrs.get('name'),
                'description': attrs.get('description'),
                'report_type': attrs.get('report_type'),
                'template_config': attrs.get('template_config', {}),
                'default_parameters': attrs.get('default_parameters', {}),
                'default_filters': attrs.get('default_filters', {}),
                'is_active': attrs.get('is_active', True),
                'is_public': attrs.get('is_public', False)
            }
            
            # Validate using service
            validated_data = ReportValidationService.validate_template_data(
                validation_data
            )
            
            # Update attrs with validated data
            attrs.update(validated_data)
            
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        except Exception as e:
            raise serializers.ValidationError(f"Validation error: {str(e)}")
        
        return attrs
    
    def create(self, validated_data):
        validated_data['company'] = self.context['request'].user.company
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


