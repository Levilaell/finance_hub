"""
Comando para recalcular os contadores de uso baseado nos dados reais do banco
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q
from apps.companies.models import Company, ResourceUsage
from apps.banking.models import Transaction
import calendar


class Command(BaseCommand):
    help = 'Recalcula os contadores de uso baseado nos dados reais do banco de dados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='ID específico da empresa para recalcular (opcional)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria alterado sem aplicar mudanças',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        company_id = options.get('company_id')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO DRY-RUN: Nenhuma alteração será aplicada')
            )
        
        # Filtrar empresas
        companies = Company.objects.filter(is_active=True)
        if company_id:
            companies = companies.filter(id=company_id)
        
        if not companies.exists():
            self.stdout.write(
                self.style.ERROR('Nenhuma empresa encontrada')
            )
            return
        
        # Data atual
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Último dia do mês atual
        last_day = calendar.monthrange(now.year, now.month)[1]
        current_month_end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
        
        self.stdout.write(f'Período: {current_month_start.date()} até {current_month_end.date()}')
        self.stdout.write('')
        
        total_updated = 0
        
        for company in companies:
            self.stdout.write(f'Empresa: {company.name} (ID: {company.id})')
            
            # Contar transações reais do mês atual
            real_transactions = Transaction.objects.filter(
                bank_account__company=company,
                transaction_date__gte=current_month_start,
                transaction_date__lte=current_month_end
            ).count()
            
            # Contador atual
            current_counter = company.current_month_transactions or 0
            
            # Mostrar diferença
            self.stdout.write(f'  Transações reais: {real_transactions}')
            self.stdout.write(f'  Contador atual: {current_counter}')
            
            if real_transactions != current_counter:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  Diferença encontrada: {real_transactions - current_counter}')
                )
                
                if not dry_run:
                    # Atualizar contador da empresa
                    company.current_month_transactions = real_transactions
                    company.save(update_fields=['current_month_transactions'])
                    
                    # Atualizar ResourceUsage também
                    resource_usage = ResourceUsage.get_or_create_current_month(company)
                    resource_usage.transactions_count = real_transactions
                    resource_usage.save(update_fields=['transactions_count'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ Contador atualizado para {real_transactions}')
                    )
                    total_updated += 1
                else:
                    self.stdout.write('  📝 Seria atualizado em execução real')
            else:
                self.stdout.write(
                    self.style.SUCCESS('  ✅ Contador já está correto')
                )
            
            # Mostrar status do plano
            if company.subscription_plan:
                limit = company.subscription_plan.max_transactions
                percentage = (real_transactions / limit) * 100 if limit > 0 else 0
                
                self.stdout.write(f'  Plano: {company.subscription_plan.name}')
                self.stdout.write(f'  Limite: {limit}')
                self.stdout.write(f'  Uso: {percentage:.1f}%')
                
                if percentage >= 90:
                    self.stdout.write(
                        self.style.ERROR(f'  🚨 Próximo do limite!')
                    )
                elif percentage >= 80:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  Uso alto')
                    )
            
            self.stdout.write('')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY-RUN: {total_updated} empresas precisam de atualização')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Concluído! {total_updated} empresas atualizadas')
            )