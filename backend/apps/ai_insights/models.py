"""
AI Insights models
Chat com IA, sistema de créditos e insights financeiros
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

User = get_user_model()


class AICredit(models.Model):
    """Controle de créditos AI por empresa"""
    company = models.OneToOneField(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='ai_credits'
    )
    balance = models.IntegerField(
        _('saldo atual'),
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Créditos disponíveis atualmente'
    )
    monthly_allowance = models.IntegerField(
        _('cota mensal'),
        default=0,
        help_text='Créditos inclusos no plano'
    )
    bonus_credits = models.IntegerField(
        _('créditos bônus'),
        default=0,
        help_text='Créditos promocionais ou de cortesia'
    )
    last_reset = models.DateTimeField(
        _('último reset'),
        default=timezone.now,
        help_text='Data do último reset mensal'
    )
    total_purchased = models.IntegerField(
        _('total comprado'),
        default=0,
        help_text='Total de créditos já comprados'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_credits'
        verbose_name = _('AI Credit')
        verbose_name_plural = _('AI Credits')
    
    def __str__(self):
        return f"{self.company.name} - {self.balance} créditos"


class AICreditTransaction(models.Model):
    """Histórico de transações de créditos"""
    TRANSACTION_TYPES = [
        ('monthly_reset', 'Reset Mensal'),
        ('purchase', 'Compra Avulsa'),
        ('bonus', 'Bônus'),
        ('usage', 'Uso'),
        ('refund', 'Reembolso'),
        ('adjustment', 'Ajuste Manual'),
    ]
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='credit_transactions'
    )
    type = models.CharField(
        _('tipo'),
        max_length=20,
        choices=TRANSACTION_TYPES
    )
    amount = models.IntegerField(
        _('quantidade'),
        help_text='Positivo=crédito, Negativo=débito'
    )
    balance_before = models.IntegerField(_('saldo anterior'))
    balance_after = models.IntegerField(_('saldo após'))
    description = models.TextField(_('descrição'))
    
    # Metadados da transação
    metadata = models.JSONField(
        _('metadados'),
        default=dict,
        help_text='Tokens usados, modelo, conversation_id, etc'
    )
    
    # Referências opcionais
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    conversation = models.ForeignKey(
        'AIConversation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    message = models.ForeignKey(
        'AIMessage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Para compras
    payment_id = models.CharField(
        _('ID pagamento'),
        max_length=255,
        blank=True,
        help_text='Stripe/MercadoPago payment ID'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_credit_transactions'
        verbose_name = _('Credit Transaction')
        verbose_name_plural = _('Credit Transactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', '-created_at']),
            models.Index(fields=['type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.amount} créditos"


class AIConversation(models.Model):
    """Conversas com a IA"""
    STATUS_CHOICES = [
        ('active', 'Ativa'),
        ('archived', 'Arquivada'),
        ('deleted', 'Excluída'),
    ]
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='ai_conversations'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_conversations'
    )
    title = models.CharField(
        _('título'),
        max_length=200,
        help_text='Gerado automaticamente ou definido pelo usuário'
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # Contexto financeiro no momento da conversa
    financial_context = models.JSONField(
        _('contexto financeiro'),
        default=dict,
        help_text='Snapshot dos dados financeiros'
    )
    
    # Configurações da conversa
    settings = models.JSONField(
        _('configurações'),
        default=dict,
        help_text='Preferências, persona AI, etc'
    )
    
    # Métricas
    message_count = models.IntegerField(default=0)
    total_credits_used = models.IntegerField(default=0)
    insights_generated = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ai_conversations'
        verbose_name = _('AI Conversation')
        verbose_name_plural = _('AI Conversations')
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['company', 'status', '-updated_at']),
            models.Index(fields=['user', '-updated_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"


class AIMessage(models.Model):
    """Mensagens individuais no chat"""
    ROLE_CHOICES = [
        ('user', 'Usuário'),
        ('assistant', 'Assistente AI'),
        ('system', 'Sistema'),
    ]
    
    MESSAGE_TYPES = [
        ('text', 'Texto'),
        ('analysis', 'Análise'),
        ('report', 'Relatório'),
        ('chart', 'Gráfico'),
        ('alert', 'Alerta'),
    ]
    
    conversation = models.ForeignKey(
        AIConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(
        _('papel'),
        max_length=20,
        choices=ROLE_CHOICES
    )
    type = models.CharField(
        _('tipo'),
        max_length=20,
        choices=MESSAGE_TYPES,
        default='text'
    )
    content = models.TextField(_('conteúdo'))
    
    # Metadados da resposta AI
    credits_used = models.IntegerField(default=0)
    tokens_used = models.IntegerField(default=0)
    model_used = models.CharField(
        _('modelo usado'),
        max_length=50,
        default='gpt-4o-mini'
    )
    
    # Dados estruturados (gráficos, tabelas, etc)
    structured_data = models.JSONField(
        _('dados estruturados'),
        null=True,
        blank=True,
        help_text='Dados para renderizar gráficos, tabelas, etc'
    )
    
    # Insights extraídos
    insights = models.JSONField(
        _('insights'),
        null=True,
        blank=True,
        help_text='Insights acionáveis extraídos'
    )
    
    # Feedback do usuário
    helpful = models.BooleanField(null=True, blank=True)
    user_feedback = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_messages'
        verbose_name = _('AI Message')
        verbose_name_plural = _('AI Messages')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}..."


class AIInsight(models.Model):
    """Insights acionáveis gerados pela IA"""
    INSIGHT_TYPES = [
        ('cost_saving', 'Economia de Custos'),
        ('cash_flow', 'Fluxo de Caixa'),
        ('anomaly', 'Anomalia Detectada'),
        ('opportunity', 'Oportunidade'),
        ('risk', 'Alerta de Risco'),
        ('trend', 'Tendência'),
        ('benchmark', 'Comparativo de Mercado'),
        ('tax', 'Fiscal/Tributário'),
        ('growth', 'Crescimento'),
    ]
    
    PRIORITY_LEVELS = [
        ('critical', 'Crítico - Ação Imediata'),
        ('high', 'Alto - Esta Semana'),
        ('medium', 'Médio - Este Mês'),
        ('low', 'Baixo - Informativo'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'Novo'),
        ('viewed', 'Visualizado'),
        ('in_progress', 'Em Andamento'),
        ('completed', 'Concluído'),
        ('dismissed', 'Descartado'),
    ]
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='ai_insights'
    )
    type = models.CharField(
        _('tipo'),
        max_length=20,
        choices=INSIGHT_TYPES
    )
    priority = models.CharField(
        _('prioridade'),
        max_length=20,
        choices=PRIORITY_LEVELS
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    
    # Conteúdo do insight
    title = models.CharField(_('título'), max_length=200)
    description = models.TextField(_('descrição'))
    
    # Ações sugeridas
    action_items = models.JSONField(
        _('ações sugeridas'),
        default=list,
        help_text='Lista de ações recomendadas'
    )
    
    # Contexto e dados
    data_context = models.JSONField(
        _('contexto de dados'),
        default=dict,
        help_text='Dados que geraram o insight'
    )
    
    # Impacto estimado
    potential_impact = models.DecimalField(
        _('impacto potencial'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Valor estimado em R$'
    )
    impact_percentage = models.DecimalField(
        _('impacto percentual'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='% de impacto no resultado'
    )
    
    # Tracking
    is_automated = models.BooleanField(
        _('gerado automaticamente'),
        default=False
    )
    conversation = models.ForeignKey(
        AIConversation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_insights'
    )
    message = models.ForeignKey(
        AIMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_insights'
    )
    
    # Feedback e resultados
    action_taken = models.BooleanField(default=False)
    action_taken_at = models.DateTimeField(null=True, blank=True)
    actual_impact = models.DecimalField(
        _('impacto real'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Valor real economizado/ganho'
    )
    user_feedback = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Quando o insight não é mais relevante'
    )
    
    class Meta:
        db_table = 'ai_insights'
        verbose_name = _('AI Insight')
        verbose_name_plural = _('AI Insights')
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['company', 'status', '-created_at']),
            models.Index(fields=['type', 'priority', '-created_at']),
            models.Index(fields=['status', 'expires_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_priority_display()}"
