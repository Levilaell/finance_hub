"""
AI Insights views
APIs para chat com IA, gerenciamento de créditos e insights
"""
import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError
from rest_framework.throttling import UserRateThrottle

from apps.companies.models import Company
from apps.companies.permissions import IsCompanyOwnerOrStaff
from .models import (
    AICredit, 
    AICreditTransaction, 
    AIConversation, 
    AIMessage, 
    AIInsight
)
from .serializers import (
    AICreditSerializer,
    AICreditTransactionSerializer,
    AIConversationSerializer,
    AIConversationDetailSerializer,
    AIMessageSerializer,
    AIInsightSerializer,
    AIInsightActionSerializer,
    MessageFeedbackSerializer,
    CreditPurchaseSerializer,
    ChatMessageSerializer
)
from .services import AIService, CreditService
from .services.export_service import ExportService
from .services.credit_service import InsufficientCreditsError

logger = logging.getLogger(__name__)


class CompanyRequiredMixin:
    """Mixin para verificar se usuário tem empresa associada"""
    
    def get_user_company(self):
        """Retorna a empresa do usuário ou None se não existir"""
        if not hasattr(self.request.user, 'company') or not self.request.user.company:
            return None
        return self.request.user.company
    
    def check_company_or_error(self):
        """Verifica se usuário tem empresa ou retorna erro HTTP"""
        company = self.get_user_company()
        if not company:
            logger.warning(f"User {self.request.user.id} attempted to access AI Insights without company")
            return StandardAPIResponse.error(
                error="no_company_associated",
                message="Usuário não possui empresa associada. Por favor, complete seu cadastro.",
                status_code=status.HTTP_403_FORBIDDEN,
                error_code="NO_COMPANY"
            )
        return company


class AIInsightsRateThrottle(UserRateThrottle):
    """Custom throttle for AI operations"""
    scope = 'ai_operations'
    rate = '100/hour'  # Max 100 AI operations per hour per user


class StandardAPIResponse:
    """Standardized API response format"""
    
    @staticmethod
    def success(data=None, message=None, status_code=status.HTTP_200_OK):
        """Success response format"""
        response_data = {
            'success': True,
            'data': data,
            'message': message,
            'timestamp': timezone.now().isoformat()
        }
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(error=None, message=None, status_code=status.HTTP_400_BAD_REQUEST, error_code=None):
        """Error response format"""
        response_data = {
            'success': False,
            'error': error,
            'message': message,
            'error_code': error_code,
            'timestamp': timezone.now().isoformat()
        }
        return Response(response_data, status=status_code)


class AICreditViewSet(CompanyRequiredMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar créditos AI
    
    Endpoints:
    - GET /api/ai-insights/credits/ - Créditos da empresa
    - GET /api/ai-insights/credits/transactions/ - Histórico de transações
    - POST /api/ai-insights/credits/purchase/ - Comprar créditos
    """
    serializer_class = AICreditSerializer
    permission_classes = [permissions.IsAuthenticated, IsCompanyOwnerOrStaff]
    
    def get_queryset(self):
        """Retorna créditos da empresa do usuário"""
        user_company = self.get_user_company()
        if not user_company:
            return AICredit.objects.none()
        
        return AICredit.objects.filter(company=user_company)
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Lista histórico de transações de créditos"""
        company_result = self.check_company_or_error()
        if isinstance(company_result, Response):
            return company_result
        
        user_company = company_result
        
        # Filtros
        transaction_type = request.query_params.get('type')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = AICreditTransaction.objects.filter(
            company=user_company
        ).select_related('user', 'conversation', 'message')
        
        if transaction_type:
            queryset = queryset.filter(type=transaction_type)
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AICreditTransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AICreditTransactionSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], throttle_classes=[AIInsightsRateThrottle])
    def purchase(self, request):
        """Compra de créditos avulsos"""
        # Verificar empresa primeiro
        company_result = self.check_company_or_error()
        if isinstance(company_result, Response):
            return company_result
        
        user_company = company_result
        
        try:
            serializer = CreditPurchaseSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Log attempt
            logger.info(f"Credit purchase attempt by user {request.user.id} for company {user_company.id}")
            
            # Processa compra via CreditService
            result = CreditService.purchase_credits(
                company=user_company,
                amount=serializer.validated_data['amount'],
                payment_method_id=serializer.validated_data['payment_method_id'],
                user=request.user
            )
            
            logger.info(f"Credit purchase successful: {result['transaction'].id}")
            
            return StandardAPIResponse.success(
                data={
                    'transaction_id': str(result['transaction'].id),
                    'new_balance': result['new_balance'],
                    'credits_purchased': serializer.validated_data['amount']
                },
                message=f"{serializer.validated_data['amount']} créditos adicionados com sucesso!",
                status_code=status.HTTP_201_CREATED
            )
            
        except ValidationError as e:
            logger.warning(f"Credit purchase validation error: {str(e)}")
            return StandardAPIResponse.error(
                error=str(e),
                message="Dados de compra inválidos",
                error_code="VALIDATION_ERROR"
            )
        except ValueError as e:
            logger.warning(f"Credit purchase value error: {str(e)}")
            return StandardAPIResponse.error(
                error=str(e),
                message="Pacote de créditos inválido",
                error_code="INVALID_PACKAGE"
            )
        except Exception as e:
            logger.error(f"Credit purchase error: {str(e)}", exc_info=True)
            return StandardAPIResponse.error(
                error="Erro interno no processamento",
                message="Erro ao processar compra de créditos",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code="PURCHASE_ERROR"
            )


class AIConversationViewSet(CompanyRequiredMixin, viewsets.ModelViewSet):
    """
    ViewSet para conversas com IA
    
    Endpoints:
    - GET /api/ai-insights/conversations/ - Lista conversas
    - POST /api/ai-insights/conversations/ - Cria nova conversa
    - GET /api/ai-insights/conversations/{id}/ - Detalhes da conversa
    - POST /api/ai-insights/conversations/{id}/send_message/ - Envia mensagem
    - POST /api/ai-insights/conversations/{id}/archive/ - Arquiva conversa
    """
    permission_classes = [permissions.IsAuthenticated, IsCompanyOwnerOrStaff]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AIConversationDetailSerializer
        return AIConversationSerializer
    
    def get_queryset(self):
        """Retorna conversas da empresa do usuário"""
        user_company = self.get_user_company()
        if not user_company:
            return AIConversation.objects.none()
        
        queryset = AIConversation.objects.filter(
            company=user_company
        ).select_related('user', 'company')
        
        # Filtros
        status_filter = self.request.query_params.get('status', 'active')
        if status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        
        user_filter = self.request.query_params.get('user')
        if user_filter:
            queryset = queryset.filter(user_id=user_filter)
        
        return queryset.order_by('-updated_at')
    
    def perform_create(self, serializer):
        """Cria nova conversa"""
        user_company = self.get_user_company()
        if not user_company:
            raise ValidationError("Usuário não possui empresa associada")
            
        serializer.save(
            company=user_company,
            user=self.request.user,
            financial_context=self._get_financial_context()
        )
    
    def _get_financial_context(self):
        """Obtém contexto financeiro atual"""
        company = self.get_user_company()
        if not company:
            return {}
        
        # Importa modelos necessários
        from apps.banking.models import BankAccount, Transaction
        from decimal import Decimal
        from datetime import timedelta
        
        now = timezone.now()
        month_start = now.replace(day=1)
        last_month = month_start - timedelta(days=1)
        last_month_start = last_month.replace(day=1)
        
        # Contas bancárias
        accounts = BankAccount.objects.filter(
            company=company,
            is_active=True
        ).aggregate(
            total_balance=Sum('balance'),
            count=Count('id')
        )
        
        # Transações do mês
        current_month_txns = Transaction.active.filter(
            company=company,
            date__gte=month_start
        ).aggregate(
            total_income=Sum('amount', filter=Q(amount__gt=0)),
            total_expense=Sum('amount', filter=Q(amount__lt=0)),
            count=Count('id')
        )
        
        # Transações do mês anterior
        last_month_txns = Transaction.active.filter(
            company=company,
            date__gte=last_month_start,
            date__lt=month_start
        ).aggregate(
            total_income=Sum('amount', filter=Q(amount__gt=0)),
            total_expense=Sum('amount', filter=Q(amount__lt=0))
        )
        
        # Top categorias de despesas (simplificado sem Category model)
        top_expense_categories = []
        
        return {
            'timestamp': now.isoformat(),
            'company': {
                'name': company.name,
                'sector': company.business_sector,
                'employees': company.employee_count,
                'monthly_revenue': float(company.monthly_revenue or 0)
            },
            'accounts': {
                'total_balance': float(accounts['total_balance'] or 0),
                'count': accounts['count']
            },
            'current_month': {
                'income': float(current_month_txns['total_income'] or 0),
                'expense': float(current_month_txns['total_expense'] or 0),
                'transactions': current_month_txns['count'],
                'net': float((current_month_txns['total_income'] or 0) + 
                           (current_month_txns['total_expense'] or 0))
            },
            'last_month': {
                'income': float(last_month_txns['total_income'] or 0),
                'expense': float(last_month_txns['total_expense'] or 0),
                'net': float((last_month_txns['total_income'] or 0) + 
                           (last_month_txns['total_expense'] or 0))
            },
            'top_expenses': top_expense_categories
        }
    
    @action(detail=True, methods=['post'], throttle_classes=[AIInsightsRateThrottle])
    def send_message(self, request, pk=None):
        """Envia mensagem no chat"""
        try:
            conversation = self.get_object()
            
            # Verifica se conversa está ativa
            if conversation.status != 'active':
                logger.warning(f"Attempt to send message to inactive conversation {pk}")
                return StandardAPIResponse.error(
                    error="Conversa não está ativa",
                    message="Esta conversa foi arquivada ou excluída",
                    error_code="CONVERSATION_INACTIVE"
                )
            
            # Valida dados
            serializer = ChatMessageSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Verifica créditos
            has_credits, credit_message = CreditService.check_credits(
                conversation.company
            )
            if not has_credits:
                logger.warning(f"Insufficient credits for company {conversation.company.id}")
                return StandardAPIResponse.error(
                    error=credit_message,
                    message="Créditos insuficientes para processar mensagem",
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    error_code="INSUFFICIENT_CREDITS"
                )
            
            # Log message processing attempt
            logger.info(f"Processing AI message for conversation {pk} by user {request.user.id}")
            
            # Processa mensagem via AIService
            result = AIService.process_message(
                conversation=conversation,
                user_message=serializer.validated_data['content'],
                context_data=serializer.validated_data.get('context_data', {}),
                request_type=serializer.validated_data.get('request_type', 'general')
            )
            
            # Serializa resposta
            message_serializer = AIMessageSerializer(result['ai_message'])
            
            logger.info(f"AI message processed successfully: {result['ai_message'].id}")
            
            return StandardAPIResponse.success(
                data={
                    'message': message_serializer.data,
                    'credits_used': result['credits_used'],
                    'credits_remaining': result['credits_remaining'],
                    'insights': [{
                        'id': str(insight.id),
                        'title': insight.title,
                        'priority': insight.priority
                    } for insight in result.get('insights', [])]
                },
                message="Mensagem processada com sucesso",
                status_code=status.HTTP_201_CREATED
            )
            
        except InsufficientCreditsError as e:
            logger.warning(f"Insufficient credits error: {str(e)}")
            return StandardAPIResponse.error(
                error=str(e),
                message="Créditos insuficientes",
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                error_code="INSUFFICIENT_CREDITS"
            )
        except ValidationError as e:
            logger.warning(f"Message validation error: {str(e)}")
            return StandardAPIResponse.error(
                error=str(e),
                message="Dados da mensagem inválidos",
                error_code="VALIDATION_ERROR"
            )
        except Exception as e:
            logger.error(f"Error processing AI message: {str(e)}", exc_info=True)
            return StandardAPIResponse.error(
                error="Erro interno no processamento",
                message="Erro ao processar mensagem com IA",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code="MESSAGE_PROCESSING_ERROR"
            )
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Arquiva conversa"""
        conversation = self.get_object()
        conversation.status = 'archived'
        conversation.save()
        
        return Response({
            'success': True,
            'message': 'Conversa arquivada com sucesso'
        })
    
    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        """Reativa conversa arquivada"""
        conversation = self.get_object()
        
        if conversation.status == 'deleted':
            return Response({
                'error': 'Não é possível reativar conversa excluída'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        conversation.status = 'active'
        conversation.save()
        
        return Response({
            'success': True,
            'message': 'Conversa reativada com sucesso'
        })
    
    @action(detail=True, methods=['get'], url_path='export/json')
    def export_json(self, request, pk=None):
        """Exporta conversa em formato JSON"""
        try:
            conversation = self.get_object()
            data = ExportService.export_conversation_to_json(conversation)
            
            filename = f"conversa_{conversation.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            return ExportService.create_export_response(
                data=data,
                filename=filename,
                content_type='application/json',
                format_type='json'
            )
            
        except Exception as e:
            return Response({
                'error': f'Erro ao exportar conversa: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='export/csv')
    def export_csv(self, request, pk=None):
        """Exporta conversa em formato CSV"""
        try:
            conversation = self.get_object()
            data = ExportService.export_conversation_to_csv(conversation)
            
            filename = f"conversa_{conversation.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return ExportService.create_export_response(
                data=data,
                filename=filename,
                content_type='text/csv',
                format_type='csv'
            )
            
        except Exception as e:
            return Response({
                'error': f'Erro ao exportar conversa: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='export/pdf')
    def export_pdf(self, request, pk=None):
        """Exporta conversa em formato PDF"""
        try:
            conversation = self.get_object()
            data = ExportService.export_conversation_to_pdf(conversation)
            
            filename = f"conversa_{conversation.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            return ExportService.create_export_response(
                data=data,
                filename=filename,
                content_type='application/pdf',
                format_type='pdf'
            )
            
        except Exception as e:
            return Response({
                'error': f'Erro ao exportar conversa: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIMessageViewSet(CompanyRequiredMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para mensagens (somente leitura)
    
    Endpoints:
    - POST /api/ai-insights/messages/{id}/feedback/ - Enviar feedback
    """
    serializer_class = AIMessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsCompanyOwnerOrStaff]
    
    def get_queryset(self):
        """Retorna mensagens das conversas da empresa"""
        user_company = self.get_user_company()
        if not user_company:
            return AIMessage.objects.none()
        
        return AIMessage.objects.filter(
            conversation__company=user_company
        ).select_related('conversation')
    
    @action(detail=True, methods=['post'])
    def feedback(self, request, pk=None):
        """Registra feedback sobre mensagem"""
        message = self.get_object()
        
        serializer = MessageFeedbackSerializer(
            message, 
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Feedback registrado com sucesso'
        })


class AIInsightViewSet(CompanyRequiredMixin, viewsets.ModelViewSet):
    """
    ViewSet para insights gerados pela IA
    
    Endpoints:
    - GET /api/ai-insights/insights/ - Lista insights
    - GET /api/ai-insights/insights/{id}/ - Detalhes do insight
    - POST /api/ai-insights/insights/{id}/mark_viewed/ - Marca como visto
    - POST /api/ai-insights/insights/{id}/take_action/ - Registra ação tomada
    - POST /api/ai-insights/insights/{id}/dismiss/ - Descarta insight
    """
    serializer_class = AIInsightSerializer
    permission_classes = [permissions.IsAuthenticated, IsCompanyOwnerOrStaff]
    
    def get_queryset(self):
        """Retorna insights da empresa"""
        user_company = self.get_user_company()
        if not user_company:
            return AIInsight.objects.none()
        
        queryset = AIInsight.objects.filter(
            company=user_company
        ).select_related('conversation')
        
        # Filtros
        insight_type = self.request.query_params.get('type')
        if insight_type:
            queryset = queryset.filter(type=insight_type)
        
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Exclui expirados por padrão
        include_expired = self.request.query_params.get('include_expired', 'false')
        if include_expired.lower() != 'true':
            queryset = queryset.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_viewed(self, request, pk=None):
        """Marca insight como visualizado"""
        insight = self.get_object()
        
        if not insight.viewed_at:
            insight.viewed_at = timezone.now()
            insight.status = 'viewed'
            insight.save()
        
        return Response({
            'success': True,
            'viewed_at': insight.viewed_at
        })
    
    @action(detail=True, methods=['post'])
    def take_action(self, request, pk=None):
        """Registra ação tomada no insight"""
        insight = self.get_object()
        
        serializer = AIInsightActionSerializer(
            insight,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Ação registrada com sucesso',
            'insight': AIInsightSerializer(insight).data
        })
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Descarta insight"""
        insight = self.get_object()
        
        insight.status = 'dismissed'
        insight.user_feedback = request.data.get('reason', '')
        insight.save()
        
        return Response({
            'success': True,
            'message': 'Insight descartado'
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Resumo dos insights"""
        company_result = self.check_company_or_error()
        if isinstance(company_result, Response):
            return company_result
        
        user_company = company_result
        
        # Estatísticas gerais
        stats = AIInsight.objects.filter(
            company=user_company
        ).aggregate(
            total=Count('id'),
            new=Count('id', filter=Q(status='new')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            completed=Count('id', filter=Q(status='completed')),
            critical=Count('id', filter=Q(priority='critical', status__in=['new', 'viewed'])),
            high=Count('id', filter=Q(priority='high', status__in=['new', 'viewed'])),
            total_potential_impact=Sum('potential_impact'),
            total_actual_impact=Sum('actual_impact')
        )
        
        # Insights por tipo
        by_type = AIInsight.objects.filter(
            company=user_company,
            status__in=['new', 'viewed', 'in_progress']
        ).values('type').annotate(
            count=Count('id'),
            potential_impact=Sum('potential_impact')
        ).order_by('-count')
        
        return Response({
            'stats': stats,
            'by_type': by_type,
            'effectiveness': {
                'insights_actioned': stats['completed'],
                'success_rate': round(
                    (stats['completed'] / stats['total'] * 100) 
                    if stats['total'] > 0 else 0,
                    2
                ),
                'roi': float(stats['total_actual_impact'] or 0)
            }
        })
    
    @action(detail=False, methods=['get'], url_path='export/json')
    def export_json(self, request):
        """Exporta insights em formato JSON"""
        company_result = self.check_company_or_error()
        if isinstance(company_result, Response):
            return company_result
        
        user_company = company_result
        
        try:
            insights = AIInsight.objects.filter(company=user_company)
            
            # Aplicar filtros se fornecidos
            status_filter = request.query_params.get('status')
            if status_filter:
                insights = insights.filter(status=status_filter)
            
            priority_filter = request.query_params.get('priority')
            if priority_filter:
                insights = insights.filter(priority=priority_filter)
            
            type_filter = request.query_params.get('type')
            if type_filter:
                insights = insights.filter(type=type_filter)
            
            data = ExportService.export_insights_to_json(list(insights))
            filename = f"insights_{user_company.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            return ExportService.create_export_response(
                data=data,
                filename=filename,
                content_type='application/json',
                format_type='json'
            )
            
        except Exception as e:
            return Response({
                'error': f'Erro ao exportar insights: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='export/csv')
    def export_csv(self, request):
        """Exporta insights em formato CSV"""
        company_result = self.check_company_or_error()
        if isinstance(company_result, Response):
            return company_result
        
        user_company = company_result
        
        try:
            insights = AIInsight.objects.filter(company=user_company)
            
            # Aplicar filtros se fornecidos
            status_filter = request.query_params.get('status')
            if status_filter:
                insights = insights.filter(status=status_filter)
            
            priority_filter = request.query_params.get('priority')
            if priority_filter:
                insights = insights.filter(priority=priority_filter)
            
            type_filter = request.query_params.get('type')
            if type_filter:
                insights = insights.filter(type=type_filter)
            
            data = ExportService.export_insights_to_csv(list(insights))
            filename = f"insights_{user_company.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return ExportService.create_export_response(
                data=data,
                filename=filename,
                content_type='text/csv',
                format_type='csv'
            )
            
        except Exception as e:
            return Response({
                'error': f'Erro ao exportar insights: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)