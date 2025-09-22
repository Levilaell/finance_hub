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
    
