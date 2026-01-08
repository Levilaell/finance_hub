"""
API Views for AI Insights
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from django.utils import timezone
from django.db.models import Subquery, OuterRef, F
from django.db import transaction
from django.core.cache import cache
from decimal import Decimal
import logging
import hashlib

from apps.ai_insights.models import AIInsight, AIInsightConfig
from apps.ai_insights.serializers import (
    AIInsightListSerializer,
    AIInsightDetailSerializer,
    AIInsightConfigSerializer,
    AIInsightComparisonSerializer,
    EnableAIInsightsSerializer
)
from apps.ai_insights.services.insight_generator import InsightGenerator
from apps.ai_insights.services.alerts_service import AlertsService
from apps.ai_insights.tasks import generate_insight_for_user
from apps.authentication.models import UserActivityLog
from apps.banking.models import BankAccount, Transaction

logger = logging.getLogger(__name__)


# Rate limiting classes
class EnableThrottle(UserRateThrottle):
    """Limit enable requests to prevent abuse."""
    rate = '5/hour'


class RegenerateThrottle(UserRateThrottle):
    """Limit regenerate requests to control OpenAI costs."""
    rate = '3/hour'


class LatestThrottle(UserRateThrottle):
    """Limit polling requests."""
    rate = '60/minute'


def check_celery_available() -> tuple[bool, str]:
    """
    Check if Celery workers are available.
    Returns (is_available, error_message).
    """
    try:
        from celery import current_app

        # Check if we can ping the broker
        inspect = current_app.control.inspect(timeout=2.0)
        active_workers = inspect.active()

        if active_workers is None:
            return False, 'Serviço de processamento indisponível. Tente novamente em alguns minutos.'

        if len(active_workers) == 0:
            return False, 'Nenhum worker disponível para processar. Tente novamente em alguns minutos.'

        return True, ''
    except Exception as e:
        logger.warning(f'Could not check Celery status: {e}')
        # If we can't check, assume it's available (graceful degradation)
        return True, ''


def check_user_has_financial_data(user) -> tuple[bool, str, dict]:
    """
    Check if user has enough financial data for meaningful AI analysis.
    Returns (has_data, error_message, details).
    """
    details = {
        'has_accounts': False,
        'has_transactions': False,
        'accounts_count': 0,
        'transactions_count': 0
    }

    # Check for active bank accounts
    accounts_count = BankAccount.objects.filter(
        connection__user=user,
        is_active=True
    ).count()

    details['accounts_count'] = accounts_count
    details['has_accounts'] = accounts_count > 0

    if accounts_count == 0:
        return False, 'Você precisa conectar pelo menos uma conta bancária antes de ativar os Insights com IA. Vá em Configurações > Conexões Bancárias.', details

    # Check for transactions in last 90 days
    ninety_days_ago = timezone.now().date() - timezone.timedelta(days=90)
    transactions_count = Transaction.objects.filter(
        account__connection__user=user,
        date__gte=ninety_days_ago
    ).count()

    details['transactions_count'] = transactions_count
    details['has_transactions'] = transactions_count > 0

    if transactions_count == 0:
        return False, 'Nenhuma transação encontrada nos últimos 90 dias. Sincronize suas contas bancárias para obter dados atualizados.', details

    # Warn if very few transactions (but allow)
    if transactions_count < 10:
        logger.warning(f'User {user.id} has only {transactions_count} transactions - AI analysis may be limited')

    return True, '', details


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
        """Return insights for the authenticated user with optimized score_change calculation."""
        queryset = AIInsight.objects.filter(user=self.request.user)

        # For list actions, annotate score_change to avoid N+1 queries
        if self.action in ['list', 'history']:
            # Subquery to get the previous insight's health_score
            previous_score_subquery = AIInsight.objects.filter(
                user=self.request.user,
                generated_at__lt=OuterRef('generated_at')
            ).order_by('-generated_at').values('health_score')[:1]

            queryset = queryset.annotate(
                _previous_score=Subquery(previous_score_subquery),
                _score_change=F('health_score') - F('_previous_score')
            )

        return queryset

    def get_serializer_class(self):
        """Use detailed serializer for retrieve action."""
        if self.action == 'retrieve':
            return AIInsightDetailSerializer
        return AIInsightListSerializer

    @action(detail=False, methods=['get'], throttle_classes=[LatestThrottle])
    def latest(self, request):
        """Get the latest insight for the user with cache control headers."""
        latest_insight = self.get_queryset().filter(has_error=False).first()

        if not latest_insight:
            response = Response(
                {'error': 'Nenhuma análise disponível. Ative os Insights com IA primeiro.'},
                status=status.HTTP_404_NOT_FOUND
            )
            # Even 404 should not be cached during polling
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response

        # Log insight view (only once per minute per user to avoid spam)
        cache_key = f'ai_insight_view_log_{request.user.id}'
        if not cache.get(cache_key):
            UserActivityLog.log_event(
                user=request.user,
                event_type='ai_insights_viewed',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                insight_id=str(latest_insight.id),
                health_score=float(latest_insight.health_score)
            )
            cache.set(cache_key, True, timeout=60)

        serializer = AIInsightDetailSerializer(latest_insight)
        response = Response(serializer.data)

        # Add cache control headers - allow short cache for successful responses
        response['Cache-Control'] = 'private, max-age=60'  # Cache for 1 minute
        response['Vary'] = 'Authorization'

        return response

    @action(detail=False, methods=['get'])
    def config(self, request):
        """Get AI insights configuration for the user."""
        config, created = AIInsightConfig.objects.get_or_create(user=request.user)
        serializer = AIInsightConfigSerializer(config)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], throttle_classes=[EnableThrottle])
    @transaction.atomic
    def enable(self, request):
        """
        Enable AI insights for the user.
        Requires company_type and business_sector.
        Uses atomic transaction to ensure consistency between Company and Config.
        """
        from apps.companies.models import Company

        serializer = EnableAIInsightsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # VALIDATION 1: Check if user has financial data
        has_data, error_message, data_details = check_user_has_financial_data(request.user)
        if not has_data:
            return Response({
                'error': error_message,
                'details': data_details
            }, status=status.HTTP_400_BAD_REQUEST)

        # VALIDATION 2: Check if Celery is available
        celery_available, celery_error = check_celery_available()
        if not celery_available:
            return Response({
                'error': celery_error,
                'code': 'SERVICE_UNAVAILABLE'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Get or create company
        if hasattr(request.user, 'company') and request.user.company is not None:
            company = request.user.company
            # Update company info
            company.company_type = serializer.validated_data['company_type']
            company.business_sector = serializer.validated_data['business_sector']
            company.save(update_fields=['company_type', 'business_sector', 'updated_at'])
        else:
            # Create minimal company for AI insights
            # Generate deterministic placeholder CNPJ based on user ID to avoid collisions
            placeholder_cnpj = self._generate_placeholder_cnpj(request.user)

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
                business_sector=serializer.validated_data['business_sector'],
                transactions_count=data_details['transactions_count'],
                accounts_count=data_details['accounts_count']
            )

            # Generate first insight immediately (async) - outside transaction
            transaction.on_commit(lambda: generate_insight_for_user.delay(request.user.id))

            return Response({
                'message': 'Insights com IA habilitados com sucesso! Sua primeira análise será gerada em instantes.',
                'config': AIInsightConfigSerializer(config).data,
                'data_summary': {
                    'accounts_count': data_details['accounts_count'],
                    'transactions_count': data_details['transactions_count']
                }
            }, status=status.HTTP_201_CREATED)

        else:
            return Response({
                'message': 'Insights com IA já estavam habilitados. Informações da empresa atualizadas.',
                'config': AIInsightConfigSerializer(config).data
            })

    def _generate_placeholder_cnpj(self, user) -> str:
        """Generate a deterministic placeholder CNPJ based on user ID to avoid collisions."""
        # Create hash from user ID for deterministic generation
        hash_input = f"placeholder_cnpj_{user.id}_{user.email}".encode('utf-8')
        hash_digest = hashlib.sha256(hash_input).hexdigest()

        # Extract numbers from hash to form CNPJ pattern: XX.XXX.XXX/XXXX-XX
        nums = ''.join(c for c in hash_digest if c.isdigit())[:14].ljust(14, '0')
        return f"{nums[0:2]}.{nums[2:5]}.{nums[5:8]}/{nums[8:12]}-{nums[12:14]}"

    @action(detail=False, methods=['post'], throttle_classes=[RegenerateThrottle])
    def regenerate(self, request):
        """Force regenerate insight for the user."""
        try:
            config = AIInsightConfig.objects.get(user=request.user, is_enabled=True)

            # Check if there's already a pending generation (prevent duplicate tasks)
            cache_key = f'ai_insight_generating_{request.user.id}'
            if cache.get(cache_key):
                return Response({
                    'error': 'Uma análise já está sendo gerada. Aguarde a conclusão.',
                    'code': 'GENERATION_IN_PROGRESS'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            # VALIDATION: Check if Celery is available
            celery_available, celery_error = check_celery_available()
            if not celery_available:
                return Response({
                    'error': celery_error,
                    'code': 'SERVICE_UNAVAILABLE'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            # Mark as generating (expires in 5 minutes)
            cache.set(cache_key, True, timeout=300)

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
                {'error': 'Insights com IA não estão habilitados. Ative primeiro em Configurações.'},
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
        # Check financial data
        has_data, data_error, data_details = check_user_has_financial_data(request.user)

        # Check company info
        has_company = hasattr(request.user, 'company') and request.user.company is not None

        if has_company:
            company = request.user.company
            has_type = bool(company.company_type)
            has_sector = bool(company.business_sector)
        else:
            has_type = False
            has_sector = False

        # Determine overall status and message
        can_enable = has_data  # Now requires financial data, not just company
        if not has_data:
            message = data_error
        else:
            message = 'Pronto para habilitar'

        return Response({
            'can_enable': can_enable,
            'has_company': has_company,
            'has_company_type': has_type,
            'has_business_sector': has_sector,
            'has_accounts': data_details['has_accounts'],
            'has_transactions': data_details['has_transactions'],
            'accounts_count': data_details['accounts_count'],
            'transactions_count': data_details['transactions_count'],
            'message': message
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

        # Safe division: check for zero using Decimal comparison to handle edge cases
        if insight2.health_score and insight2.health_score > Decimal('0'):
            score_change_pct = float((score_change / insight2.health_score) * 100)
        else:
            score_change_pct = 0.0

        return {
            'score_change': float(score_change),
            'score_change_percentage': score_change_pct,
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
        """Get paginated history of insights with cache control headers."""
        insights = self.get_queryset()

        # Pagination
        page = self.paginate_queryset(insights)
        if page is not None:
            serializer = AIInsightListSerializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
        else:
            serializer = AIInsightListSerializer(insights, many=True)
            response = Response(serializer.data)

        # Add cache control headers to prevent stale data
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

        return response

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

    @action(detail=False, methods=['get'])
    def alerts(self, request):
        """
        Get rule-based financial alerts for the user.
        These are generated in real-time without AI, providing immediate actionable insights.
        """
        # Check if user has financial data
        has_data, error_message, data_details = check_user_has_financial_data(request.user)
        if not has_data:
            return Response({
                'alerts': [],
                'error': error_message,
                'details': data_details
            }, status=status.HTTP_200_OK)

        try:
            alerts_service = AlertsService(request.user)
            alerts = alerts_service.generate_alerts()

            # Group alerts by severity for easier frontend handling
            alerts_by_severity = {
                'critical': [],
                'high': [],
                'medium': [],
                'low': []
            }
            for alert in alerts:
                severity = alert.get('severity', 'low')
                if severity in alerts_by_severity:
                    alerts_by_severity[severity].append(alert)

            return Response({
                'alerts': alerts,
                'alerts_by_severity': alerts_by_severity,
                'counts': {
                    'total': len(alerts),
                    'critical': len(alerts_by_severity['critical']),
                    'high': len(alerts_by_severity['high']),
                    'medium': len(alerts_by_severity['medium']),
                    'low': len(alerts_by_severity['low'])
                },
                'generated_at': timezone.now().isoformat()
            })

        except Exception as e:
            logger.error(f'Error generating alerts for user {request.user.id}: {e}')
            return Response({
                'alerts': [],
                'error': 'Erro ao gerar alertas. Tente novamente.',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
