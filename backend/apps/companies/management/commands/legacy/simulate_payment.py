"""
Management command to simulate payments for testing
Place this file at: backend/apps/companies/management/commands/simulate_payment.py
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import random
import string

from apps.companies.models import Company, PaymentHistory, PaymentMethod, SubscriptionPlan


class Command(BaseCommand):
    help = 'Simula pagamentos para teste do sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            'company_id',
            type=int,
            help='ID da empresa'
        )
        parser.add_argument(
            '--amount',
            type=float,
            help='Valor do pagamento (default: valor do plano atual)'
        )
        parser.add_argument(
            '--status',
            default='paid',
            choices=['paid', 'failed', 'pending', 'refunded'],
            help='Status do pagamento (default: paid)'
        )
        parser.add_argument(
            '--type',
            default='subscription',
            choices=['subscription', 'upgrade', 'refund', 'adjustment'],
            help='Tipo de transação (default: subscription)'
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Data da transação (formato: DD/MM/YYYY, default: hoje)'
        )
        parser.add_argument(
            '--gateway',
            default='stripe',
            choices=['stripe', 'mercadopago'],
            help='Gateway de pagamento (default: stripe)'
        )
        parser.add_argument(
            '--create-method',
            action='store_true',
            help='Criar método de pagamento se não existir'
        )

    def handle(self, *args, **options):
        try:
            company = Company.objects.get(id=options['company_id'])
        except Company.DoesNotExist:
            raise CommandError(f"Empresa com ID {options['company_id']} não encontrada")
        
        # Determinar valor
        if options['amount']:
            amount = Decimal(str(options['amount']))
        elif company.subscription_plan:
            if company.billing_cycle == 'yearly':
                amount = company.subscription_plan.price_yearly
            else:
                amount = company.subscription_plan.price_monthly
        else:
            amount = Decimal('149.00')  # Valor padrão
        
        # Processar data
        if options['date']:
            try:
                day, month, year = options['date'].split('/')
                transaction_date = timezone.datetime(
                    int(year), int(month), int(day),
                    tzinfo=timezone.get_current_timezone()
                )
            except ValueError:
                raise CommandError("Data inválida. Use o formato DD/MM/YYYY")
        else:
            transaction_date = timezone.now()
        
        # Verificar/criar método de pagamento
        payment_method = None
        if options['create_method'] or options['status'] == 'paid':
            payment_method = self._ensure_payment_method(company, options['gateway'])
        
        # Criar descrição
        description = self._generate_description(
            company, 
            options['type'], 
            options['status']
        )
        
        # Gerar IDs do gateway
        gateway_ids = self._generate_gateway_ids(options['gateway'])
        
        # Criar pagamento
        payment = PaymentHistory.objects.create(
            company=company,
            subscription_plan=company.subscription_plan,
            payment_method=payment_method,
            transaction_type=options['type'],
            amount=amount,
            currency='BRL',
            status=options['status'],
            description=description,
            transaction_date=transaction_date,
            due_date=transaction_date.date() if options['status'] == 'pending' else None,
            paid_at=transaction_date if options['status'] == 'paid' else None,
            **gateway_ids
        )
        
        # Atualizar status da empresa se necessário
        if options['status'] == 'paid' and options['type'] == 'subscription':
            self._update_company_status(company, transaction_date)
        
        # Exibir resultado
        self._display_result(payment, company)
        
        # Sugestões de próximos passos
        self._show_next_steps(company, options['status'])
    
    def _ensure_payment_method(self, company, gateway):
        """Garante que existe um método de pagamento"""
        payment_method = company.payment_methods.filter(is_active=True).first()
        
        if not payment_method:
            self.stdout.write("Criando método de pagamento...")
            
            payment_method = PaymentMethod.objects.create(
                company=company,
                payment_type='credit_card',
                card_brand='visa',
                last_four='4242',
                exp_month=12,
                exp_year=2025,
                cardholder_name=company.owner.get_full_name() or 'Test User',
                stripe_payment_method_id='pm_test_' + self._random_string(16) if gateway == 'stripe' else '',
                mercadopago_card_id='card_test_' + self._random_string(16) if gateway == 'mercadopago' else '',
                is_default=True,
                is_active=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Método de pagamento criado: Visa •••• 4242"
                )
            )
        
        return payment_method
    
    def _generate_description(self, company, transaction_type, status):
        """Gera descrição apropriada para o pagamento"""
        descriptions = {
            'subscription': f"Assinatura {company.subscription_plan.name if company.subscription_plan else 'N/A'} - {company.get_billing_cycle_display() if hasattr(company, 'billing_cycle') else 'Mensal'}",
            'upgrade': f"Upgrade para plano {company.subscription_plan.name if company.subscription_plan else 'Pro'}",
            'refund': f"Reembolso - {company.subscription_plan.name if company.subscription_plan else 'N/A'}",
            'adjustment': "Ajuste de cobrança"
        }
        
        base_description = descriptions.get(transaction_type, "Pagamento")
        
        if status == 'failed':
            base_description += " - FALHOU"
        elif status == 'pending':
            base_description += " - PENDENTE"
        
        return base_description
    
    def _generate_gateway_ids(self, gateway):
        """Gera IDs simulados do gateway"""
        if gateway == 'stripe':
            return {
                'stripe_payment_intent_id': 'pi_test_' + self._random_string(24),
                'stripe_invoice_id': 'in_test_' + self._random_string(24),
            }
        else:  # mercadopago
            return {
                'mercadopago_payment_id': self._random_string(10, digits_only=True),
            }
    
    def _random_string(self, length, digits_only=False):
        """Gera string aleatória"""
        if digits_only:
            return ''.join(random.choices(string.digits, k=length))
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def _update_company_status(self, company, transaction_date):
        """Atualiza status da empresa após pagamento bem-sucedido"""
        if company.subscription_status == 'trial':
            company.subscription_status = 'active'
            company.subscription_start_date = transaction_date
            self.stdout.write(
                self.style.SUCCESS(
                    "✅ Trial convertido em assinatura ativa"
                )
            )
        
        # Atualizar próxima data de cobrança
        if company.billing_cycle == 'yearly':
            company.next_billing_date = (transaction_date + timedelta(days=365)).date()
        else:
            # Adicionar um mês
            next_month = transaction_date + timedelta(days=30)
            company.next_billing_date = next_month.date()
        
        company.save()
    
    def _display_result(self, payment, company):
        """Exibe resultado da simulação"""
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS("✅ PAGAMENTO SIMULADO CRIADO"))
        self.stdout.write(f"{'='*60}")
        
        self.stdout.write(f"Empresa: {company.name}")
        self.stdout.write(f"Fatura: {payment.invoice_number}")
        self.stdout.write(f"Tipo: {payment.get_transaction_type_display()}")
        self.stdout.write(f"Valor: R$ {payment.amount}")
        self.stdout.write(f"Status: {payment.get_status_display()}")
        self.stdout.write(f"Data: {payment.transaction_date.strftime('%d/%m/%Y %H:%M')}")
        
        if payment.payment_method:
            self.stdout.write(
                f"Método: {payment.payment_method.card_brand} •••• "
                f"{payment.payment_method.last_four}"
            )
        
        gateway_label = 'Stripe' if payment.stripe_payment_intent_id else 'MercadoPago'
        gateway_id = payment.stripe_payment_intent_id or payment.mercadopago_payment_id
        if gateway_id:
            self.stdout.write(f"Gateway: {gateway_label} ({gateway_id})")
        
        self.stdout.write(f"{'='*60}\n")
    
    def _show_next_steps(self, company, status):
        """Mostra sugestões de próximos passos"""
        self.stdout.write("📝 PRÓXIMOS PASSOS:")
        
        if status == 'paid':
            self.stdout.write(
                "- Verificar no admin se o pagamento aparece corretamente"
            )
            self.stdout.write(
                "- Testar envio de recibo por email"
            )
            self.stdout.write(
                f"- Simular próxima cobrança em {company.next_billing_date}"
            )
        elif status == 'failed':
            self.stdout.write(
                "- Testar retry de pagamento"
            )
            self.stdout.write(
                "- Verificar se notificação de falha foi enviada"
            )
            self.stdout.write(
                "- Simular suspensão após múltiplas falhas"
            )
        elif status == 'pending':
            self.stdout.write(
                "- Aguardar confirmação do gateway"
            )
            self.stdout.write(
                "- Simular webhook de confirmação"
            )
        
        self.stdout.write("\nOutros comandos úteis:")
        self.stdout.write(
            f"- python manage.py billing_report --days 30"
        )
        self.stdout.write(
            f"- python manage.py check_limits"
        )