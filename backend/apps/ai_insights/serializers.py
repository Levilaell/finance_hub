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
    # Use FloatField to ensure frontend receives number, not string
    # score_change is calculated via annotation in viewset to avoid N+1 queries
    health_score = serializers.FloatField(read_only=True)
    score_change = serializers.SerializerMethodField()
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
            'error_message',
            'alerts',
            'opportunities',
            'recommendations'
        ]

    def get_score_change(self, obj):
        """Get score_change from annotation or calculate if single object."""
        # Check if score_change was annotated by the viewset
        if hasattr(obj, '_score_change'):
            return float(obj._score_change) if obj._score_change is not None else None
        # Fallback for single object retrieval (already fetched, no N+1)
        if hasattr(obj, '_prefetched_previous'):
            prev = obj._prefetched_previous
            if prev:
                return float(obj.health_score - prev.health_score)
            return None
        # Last resort: use model property (only for single object, not lists)
        return float(obj.score_change) if obj.score_change is not None else None


class AIInsightDetailSerializer(serializers.ModelSerializer):
    """Serializer for AI Insight details."""
    # Use FloatField to ensure frontend receives number, not string
    health_score = serializers.FloatField(read_only=True)
    score_change = serializers.SerializerMethodField()
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

    def get_score_change(self, obj):
        """Get score_change, calculating only for single object retrieval."""
        # For detail view, it's a single object so the property query is acceptable
        score_change = obj.score_change
        return float(score_change) if score_change is not None else None


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
