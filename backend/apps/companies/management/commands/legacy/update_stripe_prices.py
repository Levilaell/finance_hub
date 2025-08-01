"""
Comando para atualizar os IDs de preços do Stripe nos planos de assinatura
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.companies.models import SubscriptionPlan
import stripe


class Command(BaseCommand):
    help = 'Atualiza os IDs de preços do Stripe nos planos de assinatura'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra o que seria feito sem fazer alterações'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Configurar Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        self.stdout.write("=== Atualizando IDs de preços do Stripe ===\n")
        
        # Mapear planos para IDs do Stripe
        # IMPORTANTE: Substitua estes IDs pelos IDs reais dos seus produtos no Stripe
        stripe_price_mapping = {
            'starter': {
                'monthly': 'price_XXXXX_starter_monthly',  # Substitua pelo ID real
                'yearly': 'price_XXXXX_starter_yearly'     # Substitua pelo ID real
            },
            'professional': {
                'monthly': 'price_XXXXX_professional_monthly',  # Substitua pelo ID real
                'yearly': 'price_XXXXX_professional_yearly'     # Substitua pelo ID real
            },
            'enterprise': {
                'monthly': 'price_XXXXX_enterprise_monthly',  # Substitua pelo ID real
                'yearly': 'price_XXXXX_enterprise_yearly'     # Substitua pelo ID real
            }
        }
        
        # Buscar todos os planos
        plans = SubscriptionPlan.objects.all()
        
        for plan in plans:
            self.stdout.write(f"\nProcessando plano: {plan.name} ({plan.plan_type})")
            
            if plan.plan_type in stripe_price_mapping:
                price_ids = stripe_price_mapping[plan.plan_type]
                
                if dry_run:
                    self.stdout.write(self.style.WARNING(
                        f"  [DRY RUN] Atualizaria:"
                    ))
                    self.stdout.write(f"    - stripe_price_id_monthly: {price_ids['monthly']}")
                    self.stdout.write(f"    - stripe_price_id_yearly: {price_ids['yearly']}")
                else:
                    plan.stripe_price_id_monthly = price_ids['monthly']
                    plan.stripe_price_id_yearly = price_ids['yearly']
                    plan.save()
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✓ Atualizado com sucesso:"
                    ))
                    self.stdout.write(f"    - stripe_price_id_monthly: {price_ids['monthly']}")
                    self.stdout.write(f"    - stripe_price_id_yearly: {price_ids['yearly']}")
            else:
                self.stdout.write(self.style.ERROR(
                    f"  ✗ Tipo de plano '{plan.plan_type}' não encontrado no mapeamento"
                ))
        
        # Verificar se os preços existem no Stripe
        if not dry_run:
            self.stdout.write("\n=== Verificando preços no Stripe ===")
            
            for plan_type, price_ids in stripe_price_mapping.items():
                for billing_cycle, price_id in price_ids.items():
                    try:
                        # Tentar buscar o preço no Stripe
                        price = stripe.Price.retrieve(price_id)
                        self.stdout.write(self.style.SUCCESS(
                            f"✓ {plan_type} {billing_cycle}: {price_id} - OK (R$ {price.unit_amount/100:.2f})"
                        ))
                    except stripe.error.InvalidRequestError:
                        self.stdout.write(self.style.ERROR(
                            f"✗ {plan_type} {billing_cycle}: {price_id} - NÃO ENCONTRADO"
                        ))
        
        self.stdout.write("\n" + "="*50)
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                "\nEste foi um DRY RUN. Para aplicar as mudanças, execute sem --dry-run"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "\nAtualização concluída!"
            ))
            
        # Instruções para o usuário
        self.stdout.write("\n" + self.style.NOTICE("IMPORTANTE:"))
        self.stdout.write("1. Substitua os IDs de exemplo pelos IDs reais dos seus produtos no Stripe")
        self.stdout.write("2. Os IDs devem começar com 'price_' (não 'prod_')")
        self.stdout.write("3. Você pode encontrar os IDs no dashboard do Stripe em:")
        self.stdout.write("   https://dashboard.stripe.com/products")
        self.stdout.write("4. Clique no produto e copie o ID do preço (mensal e anual)")