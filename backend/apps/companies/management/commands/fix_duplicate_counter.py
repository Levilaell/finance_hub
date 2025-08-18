"""
Comando para corrigir contadores duplicados de transações
Problema: As transações estavam sendo contadas duas vezes:
1. No método Transaction.create_safe()
2. No signal post_save de Transaction

Este comando corrige os contadores para o valor real.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count
from apps.companies.models import Company, ResourceUsage
from apps.banking.models import Transaction


class Command(BaseCommand):
    help = 'Corrige contadores duplicados de transações'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='ID específico da empresa para corrigir (opcional)',
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
        
        # Data do mês atual
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        self.stdout.write(f'Verificando transações a partir de: {month_start.date()}')
        self.stdout.write('=' * 60)
        
        total_companies = 0
        total_fixed = 0
        
        for company in companies:
            # Contar transações reais do mês atual
            real_transactions = Transaction.objects.filter(
                company=company,
                date__gte=month_start
            ).count()
            
            # Contador atual
            current_counter = company.current_month_transactions or 0
            
            self.stdout.write(f'\nEmpresa: {company.name} (ID: {company.id})')
            self.stdout.write(f'  Email do proprietário: {company.owner.email}')
            self.stdout.write(f'  Transações reais no mês: {real_transactions}')
            self.stdout.write(f'  Contador atual: {current_counter}')
            
            if current_counter != real_transactions:
                difference = current_counter - real_transactions
                
                # Detectar possível duplicação
                if current_counter == real_transactions * 2:
                    self.stdout.write(
                        self.style.ERROR(f'  ⚠️  DUPLICAÇÃO DETECTADA! Contador é exatamente o dobro!')
                    )
                elif current_counter > real_transactions:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  Contador inflado em {difference} transações')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  Contador menor que o real em {-difference} transações')
                    )
                
                if not dry_run:
                    # Corrigir contador da empresa
                    company.current_month_transactions = real_transactions
                    company.save(update_fields=['current_month_transactions'])
                    
                    # Atualizar ResourceUsage também
                    try:
                        resource_usage = ResourceUsage.get_or_create_current_month(company)
                        resource_usage.transactions_count = real_transactions
                        resource_usage.save(update_fields=['transactions_count'])
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'  Erro ao atualizar ResourceUsage: {e}')
                        )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ Contador corrigido para {real_transactions}')
                    )
                    total_fixed += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  📝 Seria corrigido de {current_counter} para {real_transactions}')
                    )
                    total_fixed += 1
            else:
                self.stdout.write(
                    self.style.SUCCESS('  ✅ Contador já está correto')
                )
            
            # Mostrar status do plano
            if company.subscription_plan:
                limit = company.subscription_plan.max_transactions
                percentage = (real_transactions / limit) * 100 if limit > 0 else 0
                
                self.stdout.write(f'  Plano: {company.subscription_plan.name}')
                self.stdout.write(f'  Limite: {limit} transações')
                self.stdout.write(f'  Uso real: {percentage:.1f}%')
                
                if percentage >= 90:
                    self.stdout.write(
                        self.style.ERROR(f'  🚨 Próximo do limite!')
                    )
                elif percentage >= 80:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  Uso alto')
                    )
            
            total_companies += 1
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(f'Total de empresas verificadas: {total_companies}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY-RUN: {total_fixed} contadores precisam de correção')
            )
            self.stdout.write(
                self.style.WARNING('Execute sem --dry-run para aplicar as correções')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Concluído! {total_fixed} contadores corrigidos')
            )
            if total_fixed > 0:
                self.stdout.write(
                    self.style.SUCCESS('Os contadores de transações foram corrigidos com sucesso!')
                )