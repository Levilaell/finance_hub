"""
Serializers for AI Insights API
"""
from rest_framework import serializers
from apps.ai_insights.models import AIInsight, AIInsightConfig


class AIInsightConfigSerializer(serializers.ModelSerializer):
    """Serializer for AI Insight Configuration."""

    class Meta:
        model = AIInsightConfig
        fields = [
            'is_enabled',
            'enabled_at',
            'last_generated_at',
            'next_scheduled_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['enabled_at', 'last_generated_at', 'next_scheduled_at', 'created_at', 'updated_at']


class AIInsightListSerializer(serializers.ModelSerializer):
    """Serializer for listing AI Insights (without full details)."""
    score_change = serializers.DecimalField(max_digits=3, decimal_places=1, read_only=True)
    is_recent = serializers.BooleanField(read_only=True)

    class Meta:
        model = AIInsight
        fields = [
            'id',
            'health_score',
            'health_status',
            'summary',
            'period_start',
            'period_end',
            'generated_at',
            'score_change',
            'is_recent',
            'has_error',
            'error_message'
        ]


class AIInsightDetailSerializer(serializers.ModelSerializer):
    """Serializer for AI Insight details."""
    score_change = serializers.DecimalField(max_digits=3, decimal_places=1, read_only=True)
    is_recent = serializers.BooleanField(read_only=True)

    class Meta:
        model = AIInsight
        fields = [
            'id',
            'health_score',
            'health_status',
            'summary',
            'period_start',
            'period_end',
            'alerts',
            'opportunities',
            'predictions',
            'recommendations',
            'generated_at',
            'tokens_used',
            'model_version',
            'score_change',
            'is_recent',
            'has_error',
            'error_message'
        ]


class AIInsightComparisonSerializer(serializers.Serializer):
    """Serializer for comparing two insights."""
    insight1 = AIInsightDetailSerializer()
    insight2 = AIInsightDetailSerializer()
    comparison = serializers.DictField()


class EnableAIInsightsSerializer(serializers.Serializer):
    """Serializer for enabling AI insights."""
    company_type = serializers.ChoiceField(
        choices=[
            ('mei', 'MEI'),
            ('me', 'Microempresa'),
            ('epp', 'Empresa de Pequeno Porte'),
            ('ltda', 'Limitada'),
            ('sa', 'Sociedade Anônima'),
            ('other', 'Outros'),
        ],
        required=True
    )
    business_sector = serializers.ChoiceField(
        choices=[
            ('retail', 'Comércio'),
            ('services', 'Serviços'),
            ('industry', 'Indústria'),
            ('technology', 'Tecnologia'),
            ('healthcare', 'Saúde'),
            ('education', 'Educação'),
            ('food', 'Alimentação'),
            ('construction', 'Construção'),
            ('automotive', 'Automotivo'),
            ('agriculture', 'Agricultura'),
            ('other', 'Outros'),
        ],
        required=True
    )
