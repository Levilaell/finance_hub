"""
Lista os planos atuais e mostra como atualizá-los com IDs do Stripe
"""
from django.core.management.base import BaseCommand
from apps.companies.models import SubscriptionPlan
from decimal import Decimal


class Command(BaseCommand):
    help = 'Lista os planos atuais para facilitar a atualização com IDs do Stripe'

    def handle(self, *args, **options):
        self.stdout.write("=== PLANOS DE ASSINATURA ATUAIS ===\n")
        
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('display_order')
        
        if not plans:
            self.stdout.write(self.style.ERROR("Nenhum plano ativo encontrado!"))
            return
        
        # Mostrar planos atuais
        for plan in plans:
            self.stdout.write(f"\n{self.style.SUCCESS(plan.name.upper())}")
            self.stdout.write(f"  Tipo: {plan.plan_type}")
            self.stdout.write(f"  Slug: {plan.slug}")
            self.stdout.write(f"  Preço Mensal: R$ {plan.price_monthly}")
            self.stdout.write(f"  Preço Anual: R$ {plan.price_yearly}")
            self.stdout.write(f"  Desconto Anual: {plan.get_yearly_discount_percentage()}%")
            
            if plan.stripe_price_id_monthly or plan.stripe_price_id_yearly:
                self.stdout.write(self.style.WARNING("  IDs do Stripe já configurados:"))
                if plan.stripe_price_id_monthly:
                    self.stdout.write(f"    - Mensal: {plan.stripe_price_id_monthly}")
                if plan.stripe_price_id_yearly:
                    self.stdout.write(f"    - Anual: {plan.stripe_price_id_yearly}")
            else:
                self.stdout.write(self.style.ERROR("  ✗ IDs do Stripe não configurados"))
        
        # Gerar código Python para atualização
        self.stdout.write("\n\n" + "="*50)
        self.stdout.write(self.style.NOTICE("\nCÓDIGO PARA ATUALIZAR OS PLANOS:"))
        self.stdout.write("\nCopie e cole este código no shell do Django (python manage.py shell):")
        self.stdout.write("Substitua os 'price_XXX' pelos IDs reais do Stripe!\n")
        
        self.stdout.write("```python")
        self.stdout.write("from apps.companies.models import SubscriptionPlan")
        self.stdout.write("")
        
        for plan in plans:
            self.stdout.write(f"# {plan.name}")
            self.stdout.write(f"plan = SubscriptionPlan.objects.get(slug='{plan.slug}')")
            self.stdout.write(f"plan.stripe_price_id_monthly = 'price_XXX'  # Substitua pelo ID do preço mensal")
            self.stdout.write(f"plan.stripe_price_id_yearly = 'price_YYY'   # Substitua pelo ID do preço anual")
            self.stdout.write("plan.save()")
            self.stdout.write("")
        
        self.stdout.write("```")
        
        # Instruções
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.NOTICE("\nINSTRUÇÕES:"))
        self.stdout.write("\n1. Vá para o dashboard do Stripe: https://dashboard.stripe.com/products")
        self.stdout.write("2. Para cada produto (Starter, Professional, Enterprise):")
        self.stdout.write("   - Clique no produto")
        self.stdout.write("   - Você verá dois preços (mensal e anual)")
        self.stdout.write("   - Copie o ID de cada preço (começa com 'price_')")
        self.stdout.write("3. Substitua os 'price_XXX' e 'price_YYY' pelos IDs reais")
        self.stdout.write("4. Execute o código no shell do Django")
        
        # Exemplo de formato
        self.stdout.write("\n" + self.style.NOTICE("\nEXEMPLO DE IDs DO STRIPE:"))
        self.stdout.write("  - Mensal: price_1QTxyz123ABC...")
        self.stdout.write("  - Anual:  price_1QTxyz456DEF...")
        self.stdout.write("\nNÃO use o ID do produto (prod_XXX), use o ID do preço (price_XXX)!")