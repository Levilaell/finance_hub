"""
API Views for AI Insights
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from decimal import Decimal
import logging

from apps.ai_insights.models import AIInsight, AIInsightConfig
from apps.ai_insights.serializers import (
    AIInsightListSerializer,
    AIInsightDetailSerializer,
    AIInsightConfigSerializer,
    AIInsightComparisonSerializer,
    EnableAIInsightsSerializer
)
from apps.ai_insights.services.insight_generator import InsightGenerator
from apps.ai_insights.tasks import generate_insight_for_user
from apps.authentication.models import UserActivityLog

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class AIInsightViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for AI Insights.
    Provides list, retrieve, and custom actions.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AIInsightListSerializer

    def get_queryset(self):
        """Return insights for the authenticated user."""
        return AIInsight.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Use detailed serializer for retrieve action."""
        if self.action == 'retrieve':
            return AIInsightDetailSerializer
        return AIInsightListSerializer

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get the latest insight for the user."""
        latest_insight = self.get_queryset().filter(has_error=False).first()

        if not latest_insight:
            return Response(
                {'error': 'Nenhuma análise disponível. Ative os Insights com IA primeiro.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Log insight view
        UserActivityLog.log_event(
            user=request.user,
            event_type='ai_insights_viewed',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            insight_id=str(latest_insight.id),
            health_score=float(latest_insight.health_score)
        )

        serializer = AIInsightDetailSerializer(latest_insight)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def config(self, request):
        """Get AI insights configuration for the user."""
        config, created = AIInsightConfig.objects.get_or_create(user=request.user)
        serializer = AIInsightConfigSerializer(config)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def enable(self, request):
        """
        Enable AI insights for the user.
        Requires company_type and business_sector.
        """
        from apps.companies.models import Company

        serializer = EnableAIInsightsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get or create company
        if hasattr(request.user, 'company') and request.user.company is not None:
            company = request.user.company
            # Update company info
            company.company_type = serializer.validated_data['company_type']
            company.business_sector = serializer.validated_data['business_sector']
            company.save(update_fields=['company_type', 'business_sector', 'updated_at'])
        else:
            # Create minimal company for AI insights
            # Use email as company name and generate a placeholder CNPJ
            import random
            placeholder_cnpj = f"{random.randint(10, 99)}.{random.randint(100, 999)}.{random.randint(100, 999)}/{random.randint(1000, 9999)}-{random.randint(10, 99)}"

            # Create without validation since CNPJ is placeholder
            company = Company(
                owner=request.user,
                name=f"Empresa de {request.user.email.split('@')[0]}",
                cnpj=placeholder_cnpj,
                company_type=serializer.validated_data['company_type'],
                business_sector=serializer.validated_data['business_sector']
            )
            company.save(skip_validation=True)

        # Enable AI insights
        config, created = AIInsightConfig.objects.get_or_create(user=request.user)

        if not config.is_enabled:
            config.is_enabled = True
            config.enabled_at = timezone.now()
            config.save()

            # Log AI insights enabled
            UserActivityLog.log_event(
                user=request.user,
                event_type='ai_insights_enabled',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                company_type=serializer.validated_data['company_type'],
                business_sector=serializer.validated_data['business_sector']
            )

            # Generate first insight immediately (async)
            generate_insight_for_user.delay(request.user.id)

            return Response({
                'message': 'Insights com IA habilitados com sucesso! Sua primeira análise será gerada em instantes.',
                'config': AIInsightConfigSerializer(config).data
            }, status=status.HTTP_201_CREATED)

        else:
            return Response({
                'message': 'Insights com IA já estavam habilitados. Informações da empresa atualizadas.',
                'config': AIInsightConfigSerializer(config).data
            })

    @action(detail=False, methods=['post'])
    def regenerate(self, request):
        """Force regenerate insight for the user."""
        try:
            config = AIInsightConfig.objects.get(user=request.user, is_enabled=True)

            # Log AI insights regeneration
            UserActivityLog.log_event(
                user=request.user,
                event_type='ai_insights_regenerated',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            # Trigger new generation
            generate_insight_for_user.delay(request.user.id)

            return Response({
                'message': 'Regeneração iniciada. Aguarde alguns instantes.'
            })

        except AIInsightConfig.DoesNotExist:
            return Response(
                {'error': 'Insights com IA não estão habilitados'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def disable(self, request):
        """Disable AI insights for the user."""
        try:
            config = AIInsightConfig.objects.get(user=request.user)
            config.is_enabled = False
            config.save()

            # Log AI insights disabled
            UserActivityLog.log_event(
                user=request.user,
                event_type='ai_insights_disabled',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            return Response({
                'message': 'Insights com IA desabilitados com sucesso.'
            })

        except AIInsightConfig.DoesNotExist:
            return Response(
                {'error': 'Configuração não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def can_enable(self, request):
        """
        Check if user can enable AI insights.
        Returns validation status and requirements.
        """
        can_enable, reason = InsightGenerator.can_generate_for_user(request.user)

        # Check company info
        has_company = hasattr(request.user, 'company') and request.user.company is not None

        if has_company:
            company = request.user.company
            has_type = bool(company.company_type)
            has_sector = bool(company.business_sector)
        else:
            has_type = False
            has_sector = False

        return Response({
            'can_enable': has_company,  # Only needs company to enable (type/sector provided in enable action)
            'has_company': has_company,
            'has_company_type': has_type,
            'has_business_sector': has_sector,
            'message': 'Pronto para habilitar' if has_company else 'Empresa não cadastrada'
        })

    @action(detail=True, methods=['get'])
    def compare(self, request, pk=None):
        """
        Compare current insight with a previous one.
        Usage: /api/ai-insights/{id}/compare/?with={other_id}
        """
        insight1 = self.get_object()

        # Get the insight to compare with
        compare_with_id = request.query_params.get('with')

        if not compare_with_id:
            # If no ID provided, compare with previous insight
            insight2 = AIInsight.objects.filter(
                user=request.user,
                generated_at__lt=insight1.generated_at,
                has_error=False
            ).first()

            if not insight2:
                return Response(
                    {'error': 'Não há análises anteriores para comparar'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            try:
                insight2 = AIInsight.objects.get(
                    id=compare_with_id,
                    user=request.user
                )
            except AIInsight.DoesNotExist:
                return Response(
                    {'error': 'Análise não encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Build comparison
        comparison = self._build_comparison(insight1, insight2)

        serializer = AIInsightComparisonSerializer({
            'insight1': insight1,
            'insight2': insight2,
            'comparison': comparison
        })

        return Response(serializer.data)

    def _build_comparison(self, insight1: AIInsight, insight2: AIInsight) -> dict:
        """Build comparison data between two insights."""
        score_change = insight1.health_score - insight2.health_score

        return {
            'score_change': float(score_change),
            'score_change_percentage': float((score_change / insight2.health_score) * 100) if insight2.health_score > 0 else 0,
            'status_changed': insight1.health_status != insight2.health_status,
            'period1': {
                'start': insight1.period_start.isoformat(),
                'end': insight1.period_end.isoformat()
            },
            'period2': {
                'start': insight2.period_start.isoformat(),
                'end': insight2.period_end.isoformat()
            },
            'improvements': self._find_improvements(insight1, insight2),
            'deteriorations': self._find_deteriorations(insight1, insight2)
        }

    def _find_improvements(self, new: AIInsight, old: AIInsight) -> list:
        """Find improvements between two insights."""
        improvements = []

        # Score improvement
        if new.health_score > old.health_score:
            improvements.append(f'Score aumentou {new.health_score - old.health_score:.1f} pontos')

        # Less alerts
        if len(new.alerts) < len(old.alerts):
            improvements.append(f'Redução de {len(old.alerts) - len(new.alerts)} alerta(s)')

        # More opportunities
        if len(new.opportunities) > len(old.opportunities):
            improvements.append(f'Aumento de {len(new.opportunities) - len(old.opportunities)} oportunidade(s)')

        return improvements

    def _find_deteriorations(self, new: AIInsight, old: AIInsight) -> list:
        """Find deteriorations between two insights."""
        deteriorations = []

        # Score decrease
        if new.health_score < old.health_score:
            deteriorations.append(f'Score diminuiu {old.health_score - new.health_score:.1f} pontos')

        # More alerts
        if len(new.alerts) > len(old.alerts):
            deteriorations.append(f'Aumento de {len(new.alerts) - len(old.alerts)} alerta(s)')

        # Less opportunities
        if len(new.opportunities) < len(old.opportunities):
            deteriorations.append(f'Redução de {len(old.opportunities) - len(new.opportunities)} oportunidade(s)')

        return deteriorations

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get paginated history of insights."""
        insights = self.get_queryset()

        # Pagination
        page = self.paginate_queryset(insights)
        if page is not None:
            serializer = AIInsightListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AIInsightListSerializer(insights, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def score_evolution(self, request):
        """Get evolution of health scores over time."""
        insights = self.get_queryset().filter(has_error=False).order_by('generated_at')

        evolution = [
            {
                'date': insight.generated_at.date().isoformat(),
                'score': float(insight.health_score),
                'status': insight.health_status
            }
            for insight in insights
        ]

        return Response({'evolution': evolution})
