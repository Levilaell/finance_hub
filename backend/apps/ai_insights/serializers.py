"""
AI Insights serializers
Serialização dos modelos de chat, créditos e insights
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal

from apps.companies.models import Company
from .models import (
    AICredit, 
    AICreditTransaction, 
    AIConversation, 
    AIMessage, 
    AIInsight
)

User = get_user_model()


class AICreditSerializer(serializers.ModelSerializer):
    """Serializer para créditos AI"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    total_available = serializers.SerializerMethodField()
    usage_percentage = serializers.SerializerMethodField()
    next_reset = serializers.SerializerMethodField()
    
    class Meta:
        model = AICredit
        fields = [
            'id', 'company', 'company_name', 'balance', 
            'monthly_allowance', 'bonus_credits', 'total_available',
            'usage_percentage', 'last_reset', 'next_reset',
            'total_purchased', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_reset']
    
    def get_total_available(self, obj):
        """Calcula total de créditos disponíveis"""
        return obj.balance + obj.bonus_credits
    
    def get_usage_percentage(self, obj):
        """Calcula percentual de uso no mês"""
        if obj.monthly_allowance == 0:
            return 0
        used = obj.monthly_allowance - obj.balance
        return round((used / obj.monthly_allowance) * 100, 2)
    
    def get_next_reset(self, obj):
        """Calcula data do próximo reset"""
        from datetime import timedelta
        from django.utils import timezone
        
        # Reset acontece no primeiro dia do mês
        next_month = obj.last_reset.replace(day=1) + timedelta(days=32)
        return next_month.replace(day=1)


class AICreditTransactionSerializer(serializers.ModelSerializer):
    """Serializer para transações de créditos"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    conversation_title = serializers.CharField(
        source='conversation.title', 
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = AICreditTransaction
        fields = [
            'id', 'company', 'type', 'type_display', 'amount',
            'balance_before', 'balance_after', 'description',
            'metadata', 'user', 'user_name', 'conversation',
            'conversation_title', 'message', 'payment_id',
            'created_at'
        ]
        read_only_fields = [
            'id', 'balance_before', 'balance_after', 'created_at'
        ]
    
    def create(self, validated_data):
        """Cria transação atualizando saldo"""
        company = validated_data['company']
        amount = validated_data['amount']
        
        with transaction.atomic():
            # Obtém ou cria registro de créditos
            ai_credit, created = AICredit.objects.get_or_create(
                company=company,
                defaults={
                    'balance': 0,
                    'monthly_allowance': company.subscription_plan.max_ai_requests_per_month
                    if company.subscription_plan else 0
                }
            )
            
            # Registra saldo anterior
            validated_data['balance_before'] = ai_credit.balance
            
            # Atualiza saldo
            if validated_data['type'] == 'usage':
                # Débito - usa créditos normais primeiro
                if ai_credit.balance >= abs(amount):
                    ai_credit.balance += amount  # amount é negativo
                else:
                    # Usa saldo normal + bônus
                    remaining = abs(amount) - ai_credit.balance
                    ai_credit.balance = 0
                    ai_credit.bonus_credits = max(0, ai_credit.bonus_credits - remaining)
            else:
                # Crédito - adiciona ao saldo ou bônus
                if validated_data['type'] == 'bonus':
                    ai_credit.bonus_credits += amount
                else:
                    ai_credit.balance += amount
            
            ai_credit.save()
            
            # Registra saldo após
            validated_data['balance_after'] = ai_credit.balance
            
            return super().create(validated_data)


class AIMessageSerializer(serializers.ModelSerializer):
    """Serializer para mensagens do chat"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = AIMessage
        fields = [
            'id', 'conversation', 'role', 'role_display',
            'type', 'type_display', 'content', 'credits_used',
            'tokens_used', 'model_used', 'structured_data',
            'insights', 'helpful', 'user_feedback', 'created_at'
        ]
        read_only_fields = [
            'id', 'credits_used', 'tokens_used', 'model_used', 
            'created_at'
        ]


class AIConversationSerializer(serializers.ModelSerializer):
    """Serializer para conversas"""
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    company = serializers.CharField(source='company.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = AIConversation
        fields = [
            'id', 'company', 'company_name', 'user', 'user_name',
            'title', 'status', 'status_display', 'financial_context',
            'settings', 'message_count', 'total_credits_used',
            'insights_generated', 'last_message', 'created_at',
            'updated_at', 'last_message_at'
        ]
        read_only_fields = [
            'id', 'user', 'message_count', 'total_credits_used',
            'insights_generated', 'created_at', 'updated_at',
            'last_message_at'
        ]
    
    def get_last_message(self, obj):
        """Retorna preview da última mensagem"""
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return {
                'role': last_msg.role,
                'content_preview': last_msg.content[:100] + '...' 
                    if len(last_msg.content) > 100 else last_msg.content,
                'created_at': last_msg.created_at
            }
        return None


class AIConversationDetailSerializer(AIConversationSerializer):
    """Serializer detalhado para conversa com mensagens"""
    messages = AIMessageSerializer(many=True, read_only=True)
    can_send_message = serializers.SerializerMethodField()
    credits_available = serializers.SerializerMethodField()
    
    class Meta(AIConversationSerializer.Meta):
        fields = AIConversationSerializer.Meta.fields + [
            'messages', 'can_send_message', 'credits_available'
        ]
    
    def get_can_send_message(self, obj):
        """Verifica se pode enviar mensagem"""
        ai_credit = AICredit.objects.filter(company=obj.company).first()
        if not ai_credit:
            return False
        return (ai_credit.balance + ai_credit.bonus_credits) > 0
    
    def get_credits_available(self, obj):
        """Retorna créditos disponíveis"""
        ai_credit = AICredit.objects.filter(company=obj.company).first()
        if not ai_credit:
            return 0
        return ai_credit.balance + ai_credit.bonus_credits


class AIInsightSerializer(serializers.ModelSerializer):
    """Serializer para insights"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    conversation_title = serializers.CharField(
        source='conversation.title',
        read_only=True,
        allow_null=True
    )
    days_until_expire = serializers.SerializerMethodField()
    
    class Meta:
        model = AIInsight
        fields = [
            'id', 'company', 'type', 'type_display', 'priority',
            'priority_display', 'status', 'status_display', 'title',
            'description', 'action_items', 'data_context',
            'potential_impact', 'impact_percentage', 'is_automated',
            'conversation', 'conversation_title', 'message',
            'action_taken', 'action_taken_at', 'actual_impact',
            'user_feedback', 'created_at', 'viewed_at', 'expires_at',
            'days_until_expire'
        ]
        read_only_fields = [
            'id', 'created_at', 'viewed_at'
        ]
    
    def get_days_until_expire(self, obj):
        """Calcula dias até expirar"""
        if not obj.expires_at:
            return None
        
        from django.utils import timezone
        delta = obj.expires_at - timezone.now()
        return max(0, delta.days)


class AIInsightActionSerializer(serializers.Serializer):
    """Serializer para marcar insight como executado"""
    action_taken = serializers.BooleanField(required=True)
    actual_impact = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2,
        required=False,
        allow_null=True
    )
    user_feedback = serializers.CharField(
        required=False,
        allow_blank=True
    )
    
    def update(self, instance, validated_data):
        """Atualiza status do insight"""
        from django.utils import timezone
        
        instance.action_taken = validated_data.get('action_taken', instance.action_taken)
        instance.actual_impact = validated_data.get('actual_impact', instance.actual_impact)
        instance.user_feedback = validated_data.get('user_feedback', instance.user_feedback)
        
        if instance.action_taken:
            instance.action_taken_at = timezone.now()
            instance.status = 'completed'
        
        instance.save()
        return instance


class MessageFeedbackSerializer(serializers.Serializer):
    """Serializer para feedback de mensagem"""
    helpful = serializers.BooleanField(required=True)
    user_feedback = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000
    )
    
    def update(self, instance, validated_data):
        """Atualiza feedback da mensagem"""
        instance.helpful = validated_data.get('helpful')
        instance.user_feedback = validated_data.get('user_feedback', '')
        instance.save()
        return instance


class CreditPurchaseSerializer(serializers.Serializer):
    """Serializer para compra de créditos"""
    amount = serializers.IntegerField(
        min_value=10,
        max_value=10000,
        help_text="Quantidade de créditos para comprar"
    )
    payment_method_id = serializers.CharField(
        help_text="ID do método de pagamento"
    )
    
    def validate_amount(self, value):
        """Valida quantidade de créditos"""
        # Pacotes predefinidos
        valid_amounts = [10, 50, 100, 500, 1000, 5000]
        if value not in valid_amounts:
            raise serializers.ValidationError(
                f"Quantidade deve ser uma das opções: {valid_amounts}"
            )
        return value


class ChatMessageSerializer(serializers.Serializer):
    """Serializer para enviar mensagem no chat"""
    content = serializers.CharField(
        min_length=1,
        max_length=4000,
        help_text="Conteúdo da mensagem"
    )
    context_data = serializers.JSONField(
        required=False,
        help_text="Dados adicionais de contexto"
    )
    request_type = serializers.ChoiceField(
        choices=[
            ('general', 'Pergunta Geral'),
            ('analysis', 'Análise Detalhada'),
            ('report', 'Relatório'),
            ('recommendation', 'Recomendação'),
        ],
        default='general'
    )