"""
Companies serializers
"""
from rest_framework import serializers
from .models import Company


class CompanySerializer(serializers.ModelSerializer):
    """Company serializer"""
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    
    class Meta:
        model = Company
        fields = [
            # Basic info
            'id', 'name', 'cnpj', 'company_type', 'business_sector',
            
            # Owner info
            'owner_email',
            
            # Status
            'is_active',
            
            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'owner_email', 'created_at', 'updated_at'
        ]
    
    def validate_cnpj(self, value):
        """Validate CNPJ format and uniqueness"""
        # Basic format validation
        clean_cnpj = ''.join(filter(str.isdigit, value))
        if len(clean_cnpj) != 14:
            raise serializers.ValidationError("CNPJ deve conter 14 dígitos")
        
        # Check uniqueness (excluding current instance)
        queryset = Company.objects.filter(cnpj=value, is_active=True)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("CNPJ já está em uso")
        
        return value