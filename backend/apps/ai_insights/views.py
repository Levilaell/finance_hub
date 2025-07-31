"""
AI Insights views
APIs para chat com IA, gerenciamento de créditos e insights
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction

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


class AICreditViewSet(viewsets.ReadOnlyModelViewSet):
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
        user_company = self.request.user.company
        return AICredit.objects.filter(company=user_company)
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Lista histórico de transações de créditos"""
        user_company = request.user.company
        
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
    
    @action(detail=False, methods=['post'])
    def purchase(self, request):
        """Compra de créditos avulsos"""
        serializer = CreditPurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Processa compra via CreditService
            result = CreditService.purchase_credits(
                company=request.user.company,
                amount=serializer.validated_data['amount'],
                payment_method_id=serializer.validated_data['payment_method_id'],
                user=request.user
            )
            
            return Response({
                'success': True,
                'transaction_id': result['transaction'].id,
                'new_balance': result['new_balance'],
                'message': f"{serializer.validated_data['amount']} créditos adicionados com sucesso!"
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AIConversationViewSet(viewsets.ModelViewSet):
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
        user_company = self.request.user.company
        
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
        serializer.save(
            company=self.request.user.company,
            user=self.request.user,
            financial_context=self._get_financial_context()
        )
    
    def _get_financial_context(self):
        """Obtém contexto financeiro atual"""
        company = self.request.user.company
        
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
        current_month_txns = Transaction.objects.filter(
            company=company,
            date__gte=month_start
        ).aggregate(
            total_income=Sum('amount', filter=Q(amount__gt=0)),
            total_expense=Sum('amount', filter=Q(amount__lt=0)),
            count=Count('id')
        )
        
        # Transações do mês anterior
        last_month_txns = Transaction.objects.filter(
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
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Envia mensagem no chat"""
        conversation = self.get_object()
        
        # Verifica se conversa está ativa
        if conversation.status != 'active':
            return Response({
                'error': 'Conversa arquivada ou excluída'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Valida dados
        serializer = ChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verifica créditos
        has_credits, message = CreditService.check_credits(
            conversation.company
        )
        if not has_credits:
            return Response({
                'error': message,
                'credits_available': 0
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        try:
            # Processa mensagem via AIService
            result = AIService.process_message(
                conversation=conversation,
                user_message=serializer.validated_data['content'],
                context_data=serializer.validated_data.get('context_data', {}),
                request_type=serializer.validated_data.get('request_type', 'general')
            )
            
            # Serializa resposta
            message_serializer = AIMessageSerializer(result['ai_message'])
            
            return Response({
                'success': True,
                'message': message_serializer.data,
                'credits_used': result['credits_used'],
                'credits_remaining': result['credits_remaining'],
                'insights': result.get('insights', [])
            })
            
        except Exception as e:
            return Response({
                'error': f'Erro ao processar mensagem: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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


class AIMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para mensagens (somente leitura)
    
    Endpoints:
    - POST /api/ai-insights/messages/{id}/feedback/ - Enviar feedback
    """
    serializer_class = AIMessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsCompanyOwnerOrStaff]
    
    def get_queryset(self):
        """Retorna mensagens das conversas da empresa"""
        user_company = self.request.user.company
        
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


class AIInsightViewSet(viewsets.ModelViewSet):
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
        user_company = self.request.user.company
        
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
        user_company = request.user.company
        
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
        try:
            user_company = request.user.company
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
        try:
            user_company = request.user.company
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