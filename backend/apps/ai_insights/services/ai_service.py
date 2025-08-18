"""
AI Service
Integração com OpenAI e processamento de mensagens
"""
import json
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.template.defaultfilters import slugify

from apps.banking.models import Transaction, BankAccount
from django.db.models import Q, Sum, Avg
from ..models import (
    AIConversation,
    AIMessage,
    AIInsight,
    AICreditTransaction
)
from .credit_service import CreditService
from .anomaly_detection import AnomalyDetectionService
from .cache_service import CacheService
from .openai_wrapper import openai_wrapper, OpenAIError


logger = logging.getLogger(__name__)


class AIService:
    """Serviço para processamento de AI e geração de insights"""
    
    # Modelos e seus custos em créditos
    MODEL_COSTS = {
        'gpt-4o': 5,         # Mais poderoso
        'gpt-4o-mini': 1,    # Mais econômico
    }
    
    # Prompts do sistema
    SYSTEM_PROMPTS = {
        'financial_advisor': """Você é um consultor financeiro especializado em pequenas e médias empresas brasileiras.
Sua missão é fornecer insights acionáveis e práticos baseados nos dados financeiros apresentados.
Sempre:
- Seja direto e objetivo
- Forneça ações concretas que podem ser tomadas
- Quantifique impactos quando possível
- Use linguagem simples e acessível
- Considere o contexto brasileiro (impostos, regulamentações, mercado)
- Priorize insights que gerem economia ou aumento de receita""",
        
        'analysis': """Analise os dados financeiros fornecidos e identifique:
1. Anomalias ou padrões incomuns
2. Oportunidades de economia
3. Riscos potenciais
4. Tendências importantes
5. Comparações com períodos anteriores
Seja específico e quantifique sempre que possível.""",
        
        'recommendation': """Baseado nos dados fornecidos, gere recomendações práticas e acionáveis.
Cada recomendação deve incluir:
- O que fazer
- Por que fazer
- Impacto esperado (em R$ ou %)
- Prazo sugerido
- Passos para implementação""",
    }
    
    @classmethod
    def process_message(
        cls,
        conversation: AIConversation,
        user_message: str,
        context_data: Dict[str, Any] = None,
        request_type: str = 'general'
    ) -> Dict[str, Any]:
        """
        Processa mensagem do usuário e gera resposta AI
        
        Returns:
            Dict com mensagem AI, créditos usados, insights gerados
        """
        try:
            # Salva mensagem do usuário
            user_msg = AIMessage.objects.create(
                conversation=conversation,
                role='user',
                type='text',
                content=user_message
            )
            
            # Prepara contexto
            messages = cls._prepare_messages(
                conversation=conversation,
                user_message=user_message,
                context_data=context_data,
                request_type=request_type
            )
            
            # Seleciona modelo baseado no tipo
            model = 'gpt-4o-mini' if request_type == 'general' else 'gpt-4o'
            credit_cost = cls.MODEL_COSTS[model]
            
            # Verifica e usa créditos
            credit_result = CreditService.use_credits(
                company=conversation.company,
                amount=credit_cost,
                description=f'Chat AI - {request_type}',
                metadata={
                    'model': model,
                    'request_type': request_type,
                    'conversation_id': conversation.id
                },
                user=conversation.user,
                conversation=conversation,
                message=user_msg
            )
            
            # Chama OpenAI com error handling robusto
            try:
                response = openai_wrapper.create_completion(
                    messages=messages,
                    model=model,
                    temperature=0.7,
                    max_tokens=2000,
                    request_type=request_type
                )
                
                # Verifica se é fallback
                if response.get('is_fallback', False):
                    logger.warning(f"Using fallback response for conversation {conversation.id}")
                    # Em caso de fallback, reembolsa os créditos
                    CreditService.add_credits(
                        company=conversation.company,
                        amount=credit_cost,
                        description='Reembolso - Serviço temporariamente indisponível',
                        metadata={'reason': 'openai_fallback', 'conversation_id': conversation.id}
                    )
                
                # Processa resposta
                ai_content = response['content']
                tokens_used = response.get('usage', {}).get('total_tokens', 0)
                
            except OpenAIError as e:
                logger.error(f"OpenAI error in conversation {conversation.id}: {str(e)}")
                # Reembolsa créditos em caso de erro
                CreditService.add_credits(
                    company=conversation.company,
                    amount=credit_cost,
                    description='Reembolso - Erro no processamento',
                    metadata={'error': str(e), 'conversation_id': conversation.id}
                )
                raise
            
            # Extrai insights se não for fallback
            insights = []
            if not response.get('is_fallback', False):
                # Detecta insights no conteúdo
                detected_insights = cls._detect_insights_in_content(
                    content=ai_content,
                    conversation=conversation
                )
                insights.extend(detected_insights)
            
            # Salva mensagem AI
            ai_msg = AIMessage.objects.create(
                conversation=conversation,
                role='assistant',
                type=request_type,
                content=ai_content,
                credits_used=credit_cost if not response.get('is_fallback', False) else 0,
                tokens_used=tokens_used,
                model_used=response.get('model', model),
                structured_data=context_data,
                insights=[{
                    'id': i.id,
                    'title': i.title,
                    'priority': i.priority
                } for i in insights] if insights else None
            )
            
            # Atualiza métricas da conversa
            conversation.message_count += 2  # user + assistant
            if not response.get('is_fallback', False):
                conversation.total_credits_used += credit_cost
            conversation.insights_generated += len(insights)
            conversation.last_message_at = timezone.now()
            conversation.save()
            
            # Ajusta créditos retornados se for fallback
            actual_credits_used = 0 if response.get('is_fallback', False) else credit_cost
            
            return {
                'ai_message': ai_msg,
                'credits_used': actual_credits_used,
                'credits_remaining': credit_result['credits_remaining'] + (credit_cost if response.get('is_fallback', False) else 0),
                'insights': insights,
                'is_fallback': response.get('is_fallback', False)
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem AI: {str(e)}")
            raise
    
    @classmethod
    def _prepare_messages(
        cls,
        conversation: AIConversation,
        user_message: str,
        context_data: Dict[str, Any],
        request_type: str
    ) -> List[Dict[str, str]]:
        """Prepara mensagens para enviar ao OpenAI"""
        messages = []
        
        # System prompt baseado no tipo
        system_prompt = cls.SYSTEM_PROMPTS.get(
            request_type,
            cls.SYSTEM_PROMPTS['financial_advisor']
        )
        messages.append({
            'role': 'system',
            'content': system_prompt
        })
        
        # Contexto financeiro do cache
        cached_context = CacheService.get_financial_context(str(conversation.company.id))
        financial_context = cls._format_financial_context(cached_context)
        messages.append({
            'role': 'system',
            'content': f"Contexto financeiro atual:\n{financial_context}"
        })
        
        # Histórico recente (últimas 10 mensagens)
        recent_messages = conversation.messages.order_by(
            '-created_at'
        )[:10][::-1]  # Inverte para ordem cronológica
        
        for msg in recent_messages[:-1]:  # Exclui a última (usuário atual)
            messages.append({
                'role': msg.role,
                'content': msg.content
            })
        
        # Contexto adicional se fornecido
        if context_data:
            messages.append({
                'role': 'system',
                'content': f"Dados adicionais: {json.dumps(context_data, ensure_ascii=False)}"
            })
        
        # Mensagem atual do usuário
        messages.append({
            'role': 'user',
            'content': user_message
        })
        
        return messages
    
    @classmethod
    def _format_financial_context(cls, context: Dict[str, Any]) -> str:
        """Formata contexto financeiro para o prompt"""
        if not context:
            return "Sem dados financeiros disponíveis"
        
        lines = []
        
        # Informações da empresa
        if 'company' in context:
            c = context['company']
            lines.append(f"Empresa: {c.get('name')} - {c.get('sector')}")
            lines.append(f"Funcionários: {c.get('employees')}")
            if c.get('monthly_revenue'):
                lines.append(f"Receita mensal: R$ {c['monthly_revenue']:,.2f}")
        
        # Contas bancárias
        if 'accounts' in context:
            a = context['accounts']
            lines.append(f"\nContas: {a.get('count')} contas")
            lines.append(f"Saldo total: R$ {a.get('total_balance', 0):,.2f}")
        
        # Mês atual
        if 'current_month' in context:
            cm = context['current_month']
            lines.append(f"\nMês atual:")
            lines.append(f"- Receitas: R$ {cm.get('income', 0):,.2f}")
            lines.append(f"- Despesas: R$ {abs(cm.get('expense', 0)):,.2f}")
            lines.append(f"- Resultado: R$ {cm.get('net', 0):,.2f}")
            lines.append(f"- Transações: {cm.get('transactions', 0)}")
        
        # Mês anterior para comparação
        if 'last_month' in context:
            lm = context['last_month']
            lines.append(f"\nMês anterior:")
            lines.append(f"- Receitas: R$ {lm.get('income', 0):,.2f}")
            lines.append(f"- Despesas: R$ {abs(lm.get('expense', 0)):,.2f}")
            lines.append(f"- Resultado: R$ {lm.get('net', 0):,.2f}")
        
        # Top despesas
        if 'top_expenses' in context and context['top_expenses']:
            lines.append(f"\nPrincipais despesas:")
            for exp in context['top_expenses'][:5]:
                lines.append(
                    f"- {exp['category']}: R$ {abs(exp['total']):,.2f}"
                )
        
        return '\n'.join(lines)
    
    @classmethod
    def _get_functions(cls) -> List[Dict[str, Any]]:
        """Define funções disponíveis para o modelo"""
        return [
            {
                'name': 'create_insight',
                'description': 'Cria um insight acionável baseado na análise',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'enum': [
                                'cost_saving', 'cash_flow', 'anomaly',
                                'opportunity', 'risk', 'trend',
                                'benchmark', 'tax', 'growth'
                            ],
                            'description': 'Tipo do insight'
                        },
                        'priority': {
                            'type': 'string',
                            'enum': ['critical', 'high', 'medium', 'low'],
                            'description': 'Prioridade do insight'
                        },
                        'title': {
                            'type': 'string',
                            'description': 'Título conciso do insight'
                        },
                        'description': {
                            'type': 'string',
                            'description': 'Descrição detalhada'
                        },
                        'potential_impact': {
                            'type': 'number',
                            'description': 'Impacto potencial em R$'
                        },
                        'impact_percentage': {
                            'type': 'number',
                            'description': 'Impacto em % do resultado'
                        },
                        'action_items': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'Lista de ações recomendadas'
                        },
                        'expires_days': {
                            'type': 'integer',
                            'description': 'Dias até o insight expirar'
                        }
                    },
                    'required': [
                        'type', 'priority', 'title',
                        'description', 'action_items'
                    ]
                }
            }
        ]
    
    @classmethod
    def _process_function_call(
        cls,
        function_call,
        conversation: AIConversation
    ) -> List[AIInsight]:
        """Processa function calls e cria insights"""
        insights = []
        
        if function_call.name == 'create_insight':
            args = json.loads(function_call.arguments)
            
            # Calcula data de expiração
            expires_at = None
            if 'expires_days' in args:
                expires_at = timezone.now() + timedelta(
                    days=args['expires_days']
                )
            
            insight = AIInsight.objects.create(
                company=conversation.company,
                type=args['type'],
                priority=args['priority'],
                title=args['title'],
                description=args['description'],
                action_items=args['action_items'],
                potential_impact=args.get('potential_impact'),
                impact_percentage=args.get('impact_percentage'),
                data_context={
                    'financial_context': conversation.financial_context,
                    'created_from': 'ai_chat'
                },
                conversation=conversation,
                expires_at=expires_at
            )
            insights.append(insight)
        
        return insights
    
    @classmethod
    def _detect_insights_in_content(
        cls,
        content: str,
        conversation: AIConversation
    ) -> List[AIInsight]:
        """Detecta insights no conteúdo da resposta"""
        insights = []
        
        # Keywords que indicam insights importantes
        critical_keywords = [
            'urgente', 'crítico', 'imediato', 'alerta',
            'risco alto', 'atenção urgente'
        ]
        high_keywords = [
            'importante', 'significativo', 'relevante',
            'oportunidade', 'economia', 'redução'
        ]
        
        content_lower = content.lower()
        
        # Detecta prioridade baseado em keywords
        priority = 'medium'
        if any(kw in content_lower for kw in critical_keywords):
            priority = 'critical'
        elif any(kw in content_lower for kw in high_keywords):
            priority = 'high'
        
        # Detecta valores monetários
        import re
        money_pattern = r'R\$\s*([\d.,]+)'
        money_matches = re.findall(money_pattern, content)
        
        potential_impact = None
        if money_matches:
            # Pega o maior valor mencionado
            values = []
            for match in money_matches:
                try:
                    value = float(
                        match.replace('.', '').replace(',', '.')
                    )
                    values.append(value)
                except:
                    pass
            if values:
                potential_impact = max(values)
        
        # Se detectou informações relevantes, cria insight
        if priority in ['critical', 'high'] or potential_impact:
            # Extrai primeira frase como título
            sentences = content.split('.')
            title = sentences[0].strip()
            if len(title) > 200:
                title = title[:197] + '...'
            
            insight = AIInsight.objects.create(
                company=conversation.company,
                type='opportunity' if 'oportunidade' in content_lower else 'risk',
                priority=priority,
                title=title,
                description=content,
                potential_impact=potential_impact,
                data_context={
                    'detected_from_content': True,
                    'conversation_id': conversation.id
                },
                conversation=conversation,
                is_automated=True
            )
            insights.append(insight)
        
        return insights
    
    @classmethod
    def generate_automated_insights(
        cls,
        company: 'Company'
    ) -> List[AIInsight]:
        """
        Gera insights automatizados baseados nos dados da empresa
        Executado periodicamente via Celery
        """
        insights = []
        
        try:
            # Análise de fluxo de caixa
            cash_flow_insight = cls._analyze_cash_flow(company)
            if cash_flow_insight:
                insights.append(cash_flow_insight)
            
            # Análise de despesas
            expense_insights = cls._analyze_expenses(company)
            insights.extend(expense_insights)
            
            # Análise de tendências
            trend_insights = cls._analyze_trends(company)
            insights.extend(trend_insights)
            
            # Detecção de anomalias
            anomaly_insights = cls._detect_anomalies(company)
            insights.extend(anomaly_insights)
            
            logger.info(
                f"Gerados {len(insights)} insights automáticos "
                f"para {company.name}"
            )
            
        except Exception as e:
            logger.error(
                f"Erro ao gerar insights automáticos: {str(e)}"
            )
        
        return insights
    
    @classmethod
    def _analyze_cash_flow(cls, company: 'Company') -> Optional[AIInsight]:
        """Analisa fluxo de caixa e gera insights"""
        from apps.banking.models import BankAccount
        
        # Calcula saldo total
        total_balance = BankAccount.objects.filter(
            company=company,
            is_active=True
        ).aggregate(
            total=Sum('balance')
        )['total'] or 0
        
        # Calcula média de despesas mensais
        now = timezone.now()
        three_months_ago = now - timedelta(days=90)
        
        monthly_expenses = Transaction.active.filter(
            company=company,
            amount__lt=0,
            date__gte=three_months_ago
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        avg_monthly_expense = abs(monthly_expenses) / 3
        
        # Calcula meses de runway
        if avg_monthly_expense > 0:
            runway_months = total_balance / avg_monthly_expense
            
            if runway_months < 2:
                return AIInsight.objects.create(
                    company=company,
                    type='cash_flow',
                    priority='critical',
                    title='Alerta: Fluxo de caixa crítico',
                    description=(
                        f'Seu saldo atual de R$ {total_balance:,.2f} '
                        f'cobre apenas {runway_months:.1f} meses de '
                        f'despesas. Média mensal: R$ {avg_monthly_expense:,.2f}'
                    ),
                    action_items=[
                        'Revisar despesas não essenciais imediatamente',
                        'Acelerar recebimento de contas a receber',
                        'Negociar prazos com fornecedores',
                        'Buscar linhas de crédito preventivamente'
                    ],
                    potential_impact=avg_monthly_expense,
                    is_automated=True,
                    expires_at=now + timedelta(days=7)
                )
        
        return None
    
    @classmethod
    def _analyze_expenses(cls, company: 'Company') -> List[AIInsight]:
        """Analisa despesas e identifica oportunidades de economia"""
        insights = []
        now = timezone.now()
        month_start = now.replace(day=1)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        
        # Análise simplificada de despesas totais (sem categorias)
        three_months_ago = now - timedelta(days=90)
        
        # Despesas do mês atual
        current_expenses = Transaction.active.filter(
            company=company,
            amount__lt=0,
            date__gte=month_start
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Média histórica
        historical_expenses = Transaction.active.filter(
            company=company,
            amount__lt=0,
            date__gte=three_months_ago,
            date__lt=month_start
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        months_count = 3
        historical_avg = historical_expenses / months_count if months_count > 0 else 0
        
        current_avg = current_expenses / now.day if now.day > 0 else 0
        projected_monthly = current_avg * 30
        
        # Se projeção é 30% maior que histórico
        if abs(projected_monthly) > abs(historical_avg) * 1.3 and historical_avg != 0:
            increase_pct = (
                (abs(projected_monthly) - abs(historical_avg)) / 
                abs(historical_avg) * 100
            )
            
            insight = AIInsight.objects.create(
                company=company,
                type='cost_saving',
                priority='high',
                title=f'Aumento de {increase_pct:.0f}% nas despesas totais',
                description=(
                    f'Despesas totais estão {increase_pct:.0f}% '
                    f'acima da média histórica. Projeção mensal: '
                    f'R$ {abs(projected_monthly):,.2f} vs média de '
                    f'R$ {abs(historical_avg):,.2f}'
                ),
                action_items=[
                    'Revisar todas as despesas do mês',
                    'Identificar gastos não planejados',
                    'Analisar variações significativas',
                    'Estabelecer orçamento mensal'
                ],
                potential_impact=abs(projected_monthly) - abs(historical_avg),
                impact_percentage=increase_pct,
                data_context={
                    'current_total': float(current_expenses),
                    'historical_avg': float(historical_avg),
                    'projected_monthly': float(projected_monthly)
                },
                is_automated=True,
                expires_at=now + timedelta(days=30)
            )
            insights.append(insight)
        
        return insights[:3]  # Limita a 3 insights por execução
    
    @classmethod
    def _analyze_trends(cls, company: 'Company') -> List[AIInsight]:
        """Analisa tendências de receita e despesa"""
        insights = []
        now = timezone.now()
        
        # Analisa últimos 6 meses
        monthly_data = []
        for i in range(6):
            month_start = (now - timedelta(days=30*i)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1)
            
            month_stats = Transaction.active.filter(
                company=company,
                date__gte=month_start,
                date__lt=month_end
            ).aggregate(
                revenue=Sum('amount', filter=Q(amount__gt=0)),
                expenses=Sum('amount', filter=Q(amount__lt=0))
            )
            
            monthly_data.append({
                'month': month_start,
                'revenue': month_stats['revenue'] or 0,
                'expenses': abs(month_stats['expenses'] or 0)
            })
        
        # Calcula tendências
        if len(monthly_data) >= 3:
            # Tendência de receita
            recent_revenue = sum(m['revenue'] for m in monthly_data[:3]) / 3
            older_revenue = sum(m['revenue'] for m in monthly_data[3:]) / 3
            
            if older_revenue > 0:
                revenue_change = (
                    (recent_revenue - older_revenue) / older_revenue * 100
                )
                
                if revenue_change < -10:  # Queda maior que 10%
                    insight = AIInsight.objects.create(
                        company=company,
                        type='trend',
                        priority='high',
                        title=f'Alerta: Receita em queda ({revenue_change:.0f}%)',
                        description=(
                            f'Receita média caiu {abs(revenue_change):.0f}% '
                            f'nos últimos 3 meses comparado ao período anterior. '
                            f'Média recente: R$ {recent_revenue:,.2f} vs '
                            f'R$ {older_revenue:,.2f}'
                        ),
                        action_items=[
                            'Analisar perda de clientes',
                            'Revisar estratégia de vendas',
                            'Identificar novos canais de receita',
                            'Intensificar ações de retenção'
                        ],
                        potential_impact=recent_revenue - older_revenue,
                        impact_percentage=revenue_change,
                        is_automated=True,
                        expires_at=now + timedelta(days=14)
                    )
                    insights.append(insight)
        
        return insights
    
    @classmethod
    def _detect_anomalies(cls, company: 'Company') -> List[AIInsight]:
        """Detecta transações anômalas usando ML avançado"""
        insights = []
        
        try:
            # Usa o serviço de detecção de anomalias avançado
            anomaly_service = AnomalyDetectionService()
            anomaly_data = anomaly_service.generate_automated_insights(company.id)
            
            # Converte dados em objetos AIInsight
            for anomaly in anomaly_data:
                try:
                    insight = AIInsight.objects.create(
                        company=company,
                        type=anomaly.get('type', 'anomaly'),
                        priority=anomaly.get('priority', 'medium'),
                        title=anomaly.get('title', 'Anomalia detectada'),
                        description=anomaly.get('description', ''),
                        action_items=anomaly.get('action_items', []),
                        potential_impact=anomaly.get('potential_impact', 0),
                        impact_percentage=anomaly.get('impact_percentage'),
                        data_context=anomaly.get('data_context', {}),
                        is_automated=True,
                        expires_at=timezone.now() + timedelta(days=30)
                    )
                    insights.append(insight)
                    
                except Exception as e:
                    logger.error(f"Erro ao criar insight de anomalia: {str(e)}")
                    continue
            
            logger.info(f"Detectadas {len(insights)} anomalias para {company.name}")
            
        except Exception as e:
            logger.error(f"Erro na detecção de anomalias para {company.name}: {str(e)}")
            
            # Fallback para detecção simples em caso de erro
            insights = cls._detect_anomalies_simple(company)
        
        return insights[:5]  # Limita a 5 anomalias por execução
    
    @classmethod
    def _detect_anomalies_simple(cls, company: 'Company') -> List[AIInsight]:
        """Método simples de detecção de anomalias como fallback"""
        insights = []
        now = timezone.now()
        
        try:
            # Analisa transações dos últimos 30 dias
            recent_transactions = Transaction.active.filter(
                bank_account__company=company,
                transaction_date__gte=now - timedelta(days=30)
            ).values('amount', 'description', 'transaction_date')
            
            amounts = [abs(float(txn['amount'])) for txn in recent_transactions if txn['amount']]
            
            if len(amounts) >= 10:
                import statistics
                mean = statistics.mean(amounts)
                stdev = statistics.stdev(amounts) if len(amounts) > 1 else 0
                
                # Identifica outliers (> 2.5 desvios padrão)
                outliers = [a for a in amounts if a > mean + 2.5 * stdev]
                
                if outliers and stdev > 0:
                    max_outlier = max(outliers)
                    
                    insight = AIInsight.objects.create(
                        company=company,
                        type='anomaly',
                        priority='medium',
                        title='Transação atípica detectada',
                        description=(
                            f'Detectada transação de R$ {max_outlier:,.2f}, '
                            f'muito acima da média de R$ {mean:,.2f}.'
                        ),
                        action_items=[
                            'Verificar se a transação está correta',
                            'Confirmar se não há cobrança duplicada'
                        ],
                        potential_impact=max_outlier - mean,
                        is_automated=True,
                        expires_at=now + timedelta(days=7)
                    )
                    insights.append(insight)
        
        except Exception as e:
            logger.error(f"Erro na detecção simples de anomalias: {str(e)}")
        
        return insights