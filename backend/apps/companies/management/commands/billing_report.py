"""
Management command to generate billing reports
Place this file at: backend/apps/companies/management/commands/billing_report.py
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
import csv
import os

from apps.companies.models import Company, PaymentHistory, SubscriptionPlan


class Command(BaseCommand):
    help = 'Gera relatório detalhado de faturamento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Número de dias para o relatório (default: 30)'
        )
        parser.add_argument(
            '--export',
            action='store_true',
            help='Exportar relatório para CSV'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='billing_report.csv',
            help='Nome do arquivo de saída (default: billing_report.csv)'
        )

    def handle(self, *args, **options):
        days = options['days']
        export = options['export']
        output_file = options['output']
        
        start_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"RELATÓRIO DE FATURAMENTO - Últimos {days} dias")
        self.stdout.write(f"Período: {start_date.strftime('%d/%m/%Y')} até {timezone.now().strftime('%d/%m/%Y')}")
        self.stdout.write(f"{'='*80}\n")
        
        # Métricas gerais
        total_companies = Company.objects.filter(is_active=True).count()
        active_subs = Company.objects.filter(subscription_status='active').count()
        trial_subs = Company.objects.filter(subscription_status='trial').count()
        cancelled_subs = Company.objects.filter(subscription_status='cancelled').count()
        
        self.stdout.write(self.style.SUCCESS("📊 MÉTRICAS GERAIS:"))
        self.stdout.write(f"   Total de empresas ativas: {total_companies}")
        self.stdout.write(f"   Assinaturas pagas: {active_subs}")
        self.stdout.write(f"   Em período trial: {trial_subs}")
        self.stdout.write(f"   Canceladas: {cancelled_subs}")
        
        # Distribuição por plano
        self.stdout.write(self.style.SUCCESS("\n📋 DISTRIBUIÇÃO POR PLANO:"))
        plan_distribution = Company.objects.filter(
            subscription_status='active'
        ).values(
            'subscription_plan__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        for plan in plan_distribution:
            plan_name = plan['subscription_plan__name'] or 'Sem plano'
            self.stdout.write(f"   {plan_name}: {plan['count']} empresas")
        
        # MRR (Monthly Recurring Revenue)
        companies_monthly = Company.objects.filter(
            subscription_status='active',
            billing_cycle='monthly'
        ).select_related('subscription_plan')
        
        companies_yearly = Company.objects.filter(
            subscription_status='active',
            billing_cycle='yearly'
        ).select_related('subscription_plan')
        
        mrr_monthly = sum(
            company.subscription_plan.price_monthly 
            for company in companies_monthly 
            if company.subscription_plan
        )
        
        mrr_yearly = sum(
            company.subscription_plan.price_yearly / 12 
            for company in companies_yearly 
            if company.subscription_plan
        )
        
        mrr_total = mrr_monthly + mrr_yearly
        arr_total = mrr_total * 12  # Annual Recurring Revenue
        
        self.stdout.write(self.style.SUCCESS("\n💰 RECEITA RECORRENTE:"))
        self.stdout.write(f"   MRR Total: R$ {mrr_total:,.2f}")
        self.stdout.write(f"   - Planos mensais: R$ {mrr_monthly:,.2f}")
        self.stdout.write(f"   - Planos anuais: R$ {mrr_yearly:,.2f} (mensal)")
        self.stdout.write(f"   ARR (Anual): R$ {arr_total:,.2f}")
        
        # Receita do período
        payments = PaymentHistory.objects.filter(
            transaction_date__gte=start_date,
            status='paid'
        )
        
        revenue = payments.aggregate(total=Sum('amount'))['total'] or 0
        payment_count = payments.count()
        
        self.stdout.write(self.style.SUCCESS("\n📈 RECEITA DO PERÍODO:"))
        self.stdout.write(f"   Total recebido: R$ {revenue:,.2f}")
        self.stdout.write(f"   Número de pagamentos: {payment_count}")
        if payment_count > 0:
            self.stdout.write(f"   Ticket médio: R$ {revenue/payment_count:,.2f}")
        
        # Por tipo de transação
        by_type = payments.values('transaction_type').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        if by_type:
            self.stdout.write("\n   Detalhamento por tipo:")
            for item in by_type:
                tipo = dict(PaymentHistory.TRANSACTION_TYPES).get(
                    item['transaction_type'], 
                    item['transaction_type']
                )
                self.stdout.write(
                    f"   - {tipo}: R$ {item['total']:,.2f} ({item['count']} transações)"
                )
        
        # Churn e métricas de retenção
        cancelled_period = Company.objects.filter(
            subscription_status='cancelled',
            subscription_end_date__gte=start_date
        ).count()
        
        churn_rate = (cancelled_period / active_subs * 100) if active_subs > 0 else 0
        retention_rate = 100 - churn_rate
        
        self.stdout.write(self.style.WARNING("\n🔄 CHURN E RETENÇÃO:"))
        self.stdout.write(f"   Cancelamentos no período: {cancelled_period}")
        self.stdout.write(f"   Taxa de churn: {churn_rate:.2f}%")
        self.stdout.write(f"   Taxa de retenção: {retention_rate:.2f}%")
        
        # Trials
        trials_expiring_7d = Company.objects.filter(
            subscription_status='trial',
            trial_ends_at__lte=timezone.now() + timedelta(days=7),
            trial_ends_at__gt=timezone.now()
        ).count()
        
        trials_expiring_3d = Company.objects.filter(
            subscription_status='trial',
            trial_ends_at__lte=timezone.now() + timedelta(days=3),
            trial_ends_at__gt=timezone.now()
        ).count()
        
        trials_expired = Company.objects.filter(
            subscription_status='trial',
            trial_ends_at__lt=timezone.now()
        ).count()
        
        self.stdout.write(self.style.WARNING("\n⏰ STATUS DE TRIALS:"))
        self.stdout.write(f"   Expirando em 7 dias: {trials_expiring_7d}")
        self.stdout.write(f"   Expirando em 3 dias: {trials_expiring_3d}")
        self.stdout.write(f"   Já expirados: {trials_expired}")
        
        # Conversão de trials
        trial_conversions = Company.objects.filter(
            subscription_status='active',
            subscription_start_date__gte=start_date
        ).count()
        
        if trial_conversions > 0:
            self.stdout.write(f"   Conversões no período: {trial_conversions}")
        
        # Pagamentos falhados
        failed_payments = PaymentHistory.objects.filter(
            transaction_date__gte=start_date,
            status='failed'
        )
        
        failed_stats = failed_payments.aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        self.stdout.write(self.style.ERROR("\n❌ PAGAMENTOS FALHADOS:"))
        self.stdout.write(f"   Quantidade: {failed_stats['count'] or 0}")
        self.stdout.write(f"   Valor total: R$ {failed_stats['total'] or 0:,.2f}")
        
        if failed_stats['count'] and failed_stats['count'] > 0:
            # Listar empresas com pagamentos falhados
            failed_companies = failed_payments.values(
                'company__name'
            ).annotate(
                count=Count('id'),
                total=Sum('amount')
            ).order_by('-count')[:5]
            
            self.stdout.write("\n   Top 5 empresas com falhas:")
            for fc in failed_companies:
                self.stdout.write(
                    f"   - {fc['company__name']}: "
                    f"{fc['count']} falhas, R$ {fc['total']:,.2f}"
                )
        
        # Previsão de receita
        self.stdout.write(self.style.SUCCESS("\n📊 PREVISÃO PRÓXIMOS 30 DIAS:"))
        
        # Renovações mensais
        monthly_renewals = Company.objects.filter(
            subscription_status='active',
            billing_cycle='monthly',
            next_billing_date__lte=timezone.now().date() + timedelta(days=30)
        ).aggregate(
            count=Count('id'),
            revenue=Sum('subscription_plan__price_monthly')
        )
        
        # Renovações anuais
        yearly_renewals = Company.objects.filter(
            subscription_status='active',
            billing_cycle='yearly',
            next_billing_date__lte=timezone.now().date() + timedelta(days=30)
        ).aggregate(
            count=Count('id'),
            revenue=Sum('subscription_plan__price_yearly')
        )
        
        expected_revenue = (monthly_renewals['revenue'] or 0) + (yearly_renewals['revenue'] or 0)
        expected_transactions = (monthly_renewals['count'] or 0) + (yearly_renewals['count'] or 0)
        
        self.stdout.write(f"   Renovações esperadas: {expected_transactions}")
        self.stdout.write(f"   Receita prevista: R$ {expected_revenue:,.2f}")
        
        if export:
            self._export_to_csv(start_date, output_file)
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Relatório exportado para: {output_file}')
            )
        
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(
            f"Relatório gerado em: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )
        self.stdout.write(f"{'='*80}\n")
    
    def _export_to_csv(self, start_date, filename):
        """Exporta dados detalhados para CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Cabeçalho
            writer.writerow([
                'Empresa', 'CNPJ', 'Email', 'Plano', 'Status', 
                'Ciclo', 'MRR', 'Última Transação', 'Próxima Cobrança',
                'Dias até Renovação', 'Trial Expira', 'Criada em'
            ])
            
            # Dados
            for company in Company.objects.filter(is_active=True).select_related(
                'subscription_plan', 'owner'
            ):
                last_payment = company.payment_history.filter(
                    status='paid'
                ).order_by('-transaction_date').first()
                
                mrr = 0
                if company.subscription_plan and company.subscription_status == 'active':
                    if company.billing_cycle == 'yearly':
                        mrr = company.subscription_plan.price_yearly / 12
                    else:
                        mrr = company.subscription_plan.price_monthly
                
                days_until_renewal = ''
                if company.next_billing_date:
                    delta = company.next_billing_date - timezone.now().date()
                    days_until_renewal = delta.days
                
                writer.writerow([
                    company.name,
                    company.cnpj or 'N/A',
                    company.owner.email,
                    company.subscription_plan.name if company.subscription_plan else 'N/A',
                    company.get_subscription_status_display(),
                    company.get_billing_cycle_display() if hasattr(company, 'billing_cycle') else 'N/A',
                    f"R$ {mrr:.2f}",
                    last_payment.transaction_date.strftime('%d/%m/%Y') if last_payment else 'N/A',
                    company.next_billing_date.strftime('%d/%m/%Y') if company.next_billing_date else 'N/A',
                    days_until_renewal,
                    company.trial_ends_at.strftime('%d/%m/%Y') if company.trial_ends_at else 'N/A',
                    company.created_at.strftime('%d/%m/%Y')
                ])