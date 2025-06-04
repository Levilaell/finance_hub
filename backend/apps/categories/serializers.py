"""
Categories app serializers
"""
from rest_framework import serializers

from .models import (
    CategoryRule,
    CategorySuggestion,
    AITrainingData,
    CategorizationLog,
    CategoryPerformance,
)


class CategoryRuleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = CategoryRule
        fields = [
            'id', 'name', 'rule_type', 'conditions', 'category',
            'category_name', 'priority', 'is_active', 'confidence_threshold',
            'match_count', 'accuracy_rate', 'created_at', 'updated_at',
            'created_by', 'created_by_name'
        ]
        read_only_fields = ['match_count', 'accuracy_rate', 'created_at', 'updated_at']


class CategorySuggestionSerializer(serializers.ModelSerializer):
    transaction_description = serializers.CharField(source='transaction.description', read_only=True)
    transaction_amount = serializers.DecimalField(source='transaction.amount', max_digits=15, decimal_places=2, read_only=True)
    suggested_category_name = serializers.CharField(source='suggested_category.name', read_only=True)
    suggested_category_icon = serializers.CharField(source='suggested_category.icon', read_only=True)
    
    class Meta:
        model = CategorySuggestion
        fields = [
            'id', 'transaction', 'transaction_description', 'transaction_amount',
            'suggested_category', 'suggested_category_name', 'suggested_category_icon',
            'confidence_score', 'alternative_suggestions', 'model_version',
            'is_accepted', 'is_rejected', 'user_feedback', 'created_at',
            'reviewed_at', 'reviewed_by'
        ]
        read_only_fields = ['created_at', 'reviewed_at']


class AITrainingDataSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.full_name', read_only=True)
    
    class Meta:
        model = AITrainingData
        fields = [
            'id', 'description', 'amount', 'transaction_type', 'counterpart_name',
            'category', 'category_name', 'subcategory', 'is_verified',
            'verification_source', 'extracted_features', 'created_at',
            'verified_by', 'verified_by_name'
        ]
        read_only_fields = ['created_at']


class CategorizationLogSerializer(serializers.ModelSerializer):
    transaction_description = serializers.CharField(source='transaction.description', read_only=True)
    suggested_category_name = serializers.CharField(source='suggested_category.name', read_only=True)
    final_category_name = serializers.CharField(source='final_category.name', read_only=True)
    
    class Meta:
        model = CategorizationLog
        fields = [
            'id', 'transaction', 'transaction_description', 'method',
            'suggested_category', 'suggested_category_name', 'confidence_score',
            'processing_time_ms', 'rule_used', 'ai_model_version',
            'was_accepted', 'final_category', 'final_category_name', 'created_at'
        ]
        read_only_fields = ['created_at']


class CategoryPerformanceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    
    class Meta:
        model = CategoryPerformance
        fields = [
            'id', 'category', 'category_name', 'category_icon',
            'total_predictions', 'correct_predictions', 'false_positives',
            'false_negatives', 'accuracy', 'precision', 'recall', 'f1_score',
            'period_start', 'period_end', 'calculated_at'
        ]
        read_only_fields = ['calculated_at']