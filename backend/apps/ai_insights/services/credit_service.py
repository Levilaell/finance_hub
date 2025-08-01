"""
Credit Service
Gerenciamento de créditos AI
"""
from typing import Tuple, Dict, Any
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from apps.companies.models import Company
from apps.payments.models import PaymentMethod
from apps.payments.services import StripeService
from ..models import AICredit, AICreditTransaction


class InsufficientCreditsError(Exception):
    """Exception raised when company doesn't have enough credits"""
    pass


class CreditService:
    """Serviço para gerenciamento de créditos AI"""
    
    # Preços por pacote de créditos (em reais)
    CREDIT_PACKAGES = {
        10: Decimal('9.90'),      # R$ 0,99 por crédito
        50: Decimal('44.90'),     # R$ 0,90 por crédito
        100: Decimal('79.90'),    # R$ 0,80 por crédito
        500: Decimal('349.90'),   # R$ 0,70 por crédito
        1000: Decimal('599.90'),  # R$ 0,60 por crédito
        5000: Decimal('2499.90'), # R$ 0,50 por crédito
    }
    
    # Custo em créditos por tipo de requisição
    CREDIT_COSTS = {
        'general': 1,        # Pergunta simples
        'analysis': 3,       # Análise detalhada
        'report': 5,         # Relatório completo
        'recommendation': 2, # Recomendação
    }
    
    @classmethod
    def check_credits(cls, company: Company) -> Tuple[bool, str]:
        """
        Verifica se empresa tem créditos disponíveis
        
        Returns:
            Tuple[bool, str]: (tem_creditos, mensagem)
        """
        # Verifica se empresa pode usar AI
        can_use, message = company.can_use_ai_insight()
        if not can_use:
            return False, message
        
        # Obtém ou cria registro de créditos
        ai_credit, created = AICredit.objects.get_or_create(
            company=company,
            defaults={
                'balance': 0,
                'monthly_allowance': cls._get_monthly_allowance(company)
            }
        )
        
        # Se foi criado agora, aplica créditos iniciais
        if created:
            cls._apply_initial_credits(ai_credit)
        
        # Verifica se precisa resetar créditos mensais
        if cls._should_reset_monthly_credits(ai_credit):
            cls._reset_monthly_credits(ai_credit)
        
        # Calcula total disponível
        total_available = ai_credit.balance + ai_credit.bonus_credits
        
        if total_available <= 0:
            return False, "Sem créditos disponíveis. Compre créditos para continuar."
        
        return True, f"{total_available} créditos disponíveis"
    
    @classmethod
    def use_credits(
        cls,
        company: Company,
        amount: int,
        description: str,
        metadata: Dict[str, Any] = None,
        user=None,
        conversation=None,
        message=None
    ) -> Dict[str, Any]:
        """
        Usa créditos da empresa
        
        Returns:
            Dict com informações da transação
        """
        with transaction.atomic():
            ai_credit = AICredit.objects.select_for_update().get(
                company=company
            )
            
            # Verifica disponibilidade
            total_available = ai_credit.balance + ai_credit.bonus_credits
            if total_available < amount:
                raise InsufficientCreditsError(
                    f"Créditos insuficientes. Disponível: {total_available}, "
                    f"Necessário: {amount}"
                )
            
            # Registra saldo anterior
            balance_before = ai_credit.balance
            bonus_before = ai_credit.bonus_credits
            
            # Deduz créditos (usa normais primeiro, depois bônus)
            remaining = amount
            if ai_credit.balance >= remaining:
                ai_credit.balance -= remaining
                remaining = 0
            else:
                remaining -= ai_credit.balance
                ai_credit.balance = 0
                ai_credit.bonus_credits -= remaining
            
            ai_credit.save()
            
            # Cria transação
            transaction_record = AICreditTransaction.objects.create(
                company=company,
                type='usage',
                amount=-amount,  # Negativo para débito
                balance_before=balance_before + bonus_before,
                balance_after=ai_credit.balance + ai_credit.bonus_credits,
                description=description,
                metadata=metadata or {},
                user=user,
                conversation=conversation,
                message=message
            )
            
            return {
                'transaction': transaction_record,
                'credits_used': amount,
                'credits_remaining': ai_credit.balance + ai_credit.bonus_credits
            }
    
    @classmethod
    def add_credits(
        cls,
        company: Company,
        amount: int,
        transaction_type: str,
        description: str,
        metadata: Dict[str, Any] = None,
        payment_id: str = None,
        user=None
    ) -> AICreditTransaction:
        """
        Adiciona créditos à empresa
        
        Args:
            company: Empresa
            amount: Quantidade de créditos
            transaction_type: Tipo da transação
            description: Descrição
            metadata: Metadados adicionais
            payment_id: ID do pagamento (se aplicável)
            user: Usuário que realizou a ação
            
        Returns:
            AICreditTransaction criada
        """
        with transaction.atomic():
            ai_credit, created = AICredit.objects.select_for_update().get_or_create(
                company=company,
                defaults={
                    'balance': 0,
                    'monthly_allowance': cls._get_monthly_allowance(company)
                }
            )
            
            # Registra saldo anterior
            balance_before = ai_credit.balance + ai_credit.bonus_credits
            
            # Adiciona créditos
            if transaction_type == 'bonus':
                ai_credit.bonus_credits += amount
            else:
                ai_credit.balance += amount
                if transaction_type == 'purchase':
                    ai_credit.total_purchased += amount
            
            ai_credit.save()
            
            # Cria transação
            return AICreditTransaction.objects.create(
                company=company,
                type=transaction_type,
                amount=amount,  # Positivo para crédito
                balance_before=balance_before,
                balance_after=ai_credit.balance + ai_credit.bonus_credits,
                description=description,
                metadata=metadata or {},
                payment_id=payment_id,
                user=user
            )
    
    @classmethod
    def purchase_credits(
        cls,
        company: Company,
        amount: int,
        payment_method_id: str,
        user=None
    ) -> Dict[str, Any]:
        """
        Processa compra de créditos
        
        Returns:
            Dict com informações da compra
        """
        # Valida pacote
        if amount not in cls.CREDIT_PACKAGES:
            raise ValueError(f"Pacote inválido: {amount} créditos")
        
        price = cls.CREDIT_PACKAGES[amount]
        
        # Obtém método de pagamento
        payment_method = PaymentMethod.objects.get(
            id=payment_method_id,
            company=company,
            is_active=True
        )
        
        # Processa pagamento
        payment_result = cls._process_payment(
            company=company,
            payment_method=payment_method,
            amount=price,
            description=f"Compra de {amount} créditos AI"
        )
        
        if not payment_result['success']:
            raise Exception(f"Erro no pagamento: {payment_result['error']}")
        
        # Adiciona créditos
        transaction_record = cls.add_credits(
            company=company,
            amount=amount,
            transaction_type='purchase',
            description=f"Compra de {amount} créditos",
            metadata={
                'price': str(price),
                'payment_gateway': payment_result['gateway'],
                'payment_status': payment_result['status']
            },
            payment_id=payment_result['payment_id'],
            user=user
        )
        
        # Obtém novo saldo
        ai_credit = AICredit.objects.get(company=company)
        new_balance = ai_credit.balance + ai_credit.bonus_credits
        
        return {
            'transaction': transaction_record,
            'payment_id': payment_result['payment_id'],
            'new_balance': new_balance
        }
    
    @classmethod
    def _get_monthly_allowance(cls, company: Company) -> int:
        """Obtém cota mensal baseada no plano"""
        if not company.subscription_plan:
            return 0
        
        # Mapeia planos para créditos mensais
        plan_credits = {
            'starter': 0,      # Sem AI
            'professional': 100,  # 100 créditos/mês
            'enterprise': 1000,   # 1000 créditos/mês
        }
        
        return plan_credits.get(
            company.subscription_plan.plan_type,
            0
        )
    
    @classmethod
    def _apply_initial_credits(cls, ai_credit: AICredit) -> None:
        """Aplica créditos iniciais para nova empresa"""
        # Empresas novas ganham 10 créditos de bônus
        ai_credit.bonus_credits = 10
        ai_credit.balance = ai_credit.monthly_allowance
        ai_credit.save()
        
        # Registra transação de bônus
        AICreditTransaction.objects.create(
            company=ai_credit.company,
            type='bonus',
            amount=10,
            balance_before=0,
            balance_after=ai_credit.balance + ai_credit.bonus_credits,
            description='Bônus de boas-vindas'
        )
    
    @classmethod
    def _should_reset_monthly_credits(cls, ai_credit: AICredit) -> bool:
        """Verifica se deve resetar créditos mensais"""
        now = timezone.now()
        
        # Reset no primeiro dia do mês
        if ai_credit.last_reset.month != now.month:
            return True
        
        # Ou se já passou mais de 30 dias
        if (now - ai_credit.last_reset).days > 30:
            return True
        
        return False
    
    @classmethod
    def _reset_monthly_credits(cls, ai_credit: AICredit) -> None:
        """Reseta créditos mensais"""
        old_balance = ai_credit.balance
        ai_credit.balance = ai_credit.monthly_allowance
        ai_credit.last_reset = timezone.now()
        ai_credit.save()
        
        # Registra transação
        AICreditTransaction.objects.create(
            company=ai_credit.company,
            type='monthly_reset',
            amount=ai_credit.monthly_allowance - old_balance,
            balance_before=old_balance + ai_credit.bonus_credits,
            balance_after=ai_credit.balance + ai_credit.bonus_credits,
            description=f'Reset mensal - {ai_credit.monthly_allowance} créditos'
        )
    
    @classmethod
    def _process_payment(
        cls,
        company: Company,
        payment_method: Any,  # PaymentMethod moved to payments app
        amount: Decimal,
        description: str
    ) -> Dict[str, Any]:
        """Processa pagamento via gateway"""
        # Usa apenas Stripe
        if payment_method.stripe_payment_method_id:
            return StripeService.process_credit_purchase(
                company=company,
                payment_method=payment_method,
                amount=amount,
                description=description
            )
        else:
            return {
                'success': False,
                'error': 'Método de pagamento inválido. Configure um cartão no Stripe.'
            }
    
    @classmethod
    def get_credit_history(
        cls,
        company: Company,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Obtém histórico e estatísticas de uso de créditos
        
        Returns:
            Dict com estatísticas
        """
        since = timezone.now() - timedelta(days=days)
        
        transactions = AICreditTransaction.objects.filter(
            company=company,
            created_at__gte=since
        )
        
        # Estatísticas por tipo
        stats = {}
        for t_type, t_name in AICreditTransaction.TRANSACTION_TYPES:
            type_transactions = transactions.filter(type=t_type)
            stats[t_type] = {
                'count': type_transactions.count(),
                'total': type_transactions.aggregate(
                    total=Sum('amount')
                )['total'] or 0
            }
        
        # Créditos atuais
        ai_credit = AICredit.objects.filter(company=company).first()
        
        return {
            'current_balance': ai_credit.balance if ai_credit else 0,
            'bonus_credits': ai_credit.bonus_credits if ai_credit else 0,
            'total_available': (
                (ai_credit.balance + ai_credit.bonus_credits)
                if ai_credit else 0
            ),
            'monthly_allowance': ai_credit.monthly_allowance if ai_credit else 0,
            'total_purchased': ai_credit.total_purchased if ai_credit else 0,
            'last_reset': ai_credit.last_reset if ai_credit else None,
            'statistics': stats,
            'period_days': days
        }