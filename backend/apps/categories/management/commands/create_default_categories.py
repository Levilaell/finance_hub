"""
Create default transaction categories
"""
from django.core.management.base import BaseCommand

from apps.banking.models import TransactionCategory


class Command(BaseCommand):
    help = 'Create default transaction categories'

    def handle(self, *args, **options):
        # Income categories
        income_categories = [
            {
                'name': 'Vendas',
                'slug': 'vendas',
                'category_type': 'income',
                'icon': '💰',
                'color': '#10B981',
                'keywords': ['venda', 'pedido', 'fatura', 'nf', 'nota fiscal'],
            },
            {
                'name': 'Serviços',
                'slug': 'servicos',
                'category_type': 'income',
                'icon': '🛠️',
                'color': '#3B82F6',
                'keywords': ['servico', 'consultoria', 'manutencao', 'reparo'],
            },
            {
                'name': 'Investimentos',
                'slug': 'investimentos',
                'category_type': 'income',
                'icon': '📈',
                'color': '#6366F1',
                'keywords': ['rendimento', 'dividendo', 'juros', 'aplicacao'],
            },
            {
                'name': 'Outros Recebimentos',
                'slug': 'outros-recebimentos',
                'category_type': 'income',
                'icon': '📥',
                'color': '#8B5CF6',
                'keywords': ['reembolso', 'devolucao', 'estorno'],
            },
        ]

        # Expense categories
        expense_categories = [
            {
                'name': 'Fornecedores',
                'slug': 'fornecedores',
                'category_type': 'expense',
                'icon': '📦',
                'color': '#EF4444',
                'keywords': ['fornecedor', 'compra', 'material', 'estoque'],
            },
            {
                'name': 'Folha de Pagamento',
                'slug': 'folha-pagamento',
                'category_type': 'expense',
                'icon': '👥',
                'color': '#F59E0B',
                'keywords': ['salario', 'folha', 'pagamento', 'funcionario', 'rh'],
            },
            {
                'name': 'Impostos',
                'slug': 'impostos',
                'category_type': 'expense',
                'icon': '🏛️',
                'color': '#EF4444',
                'keywords': ['imposto', 'taxa', 'tributo', 'darf', 'das', 'inss', 'fgts'],
            },
            {
                'name': 'Aluguel e Condomínio',
                'slug': 'aluguel-condominio',
                'category_type': 'expense',
                'icon': '🏢',
                'color': '#F97316',
                'keywords': ['aluguel', 'condominio', 'iptu', 'locacao'],
            },
            {
                'name': 'Contas de Consumo',
                'slug': 'contas-consumo',
                'category_type': 'expense',
                'icon': '💡',
                'color': '#FACC15',
                'keywords': ['luz', 'agua', 'energia', 'telefone', 'internet', 'gas'],
            },
            {
                'name': 'Marketing',
                'slug': 'marketing',
                'category_type': 'expense',
                'icon': '📢',
                'color': '#A855F7',
                'keywords': ['propaganda', 'publicidade', 'anuncio', 'google', 'facebook', 'instagram'],
            },
            {
                'name': 'Transporte',
                'slug': 'transporte',
                'category_type': 'expense',
                'icon': '🚗',
                'color': '#6366F1',
                'keywords': ['combustivel', 'uber', 'taxi', 'frete', 'entrega', 'gasolina'],
            },
            {
                'name': 'Alimentação',
                'slug': 'alimentacao',
                'category_type': 'expense',
                'icon': '🍽️',
                'color': '#10B981',
                'keywords': ['restaurante', 'lanche', 'refeicao', 'ifood', 'almoco'],
            },
            {
                'name': 'Software e Tecnologia',
                'slug': 'software-tecnologia',
                'category_type': 'expense',
                'icon': '💻',
                'color': '#3B82F6',
                'keywords': ['software', 'licenca', 'assinatura', 'nuvem', 'hosting', 'dominio'],
            },
            {
                'name': 'Taxas Bancárias',
                'slug': 'taxas-bancarias',
                'category_type': 'expense',
                'icon': '🏦',
                'color': '#DC2626',
                'keywords': ['tarifa', 'taxa', 'juros', 'iof', 'ted', 'doc', 'anuidade'],
            },
            {
                'name': 'Outros Gastos',
                'slug': 'outros-gastos',
                'category_type': 'expense',
                'icon': '📤',
                'color': '#64748B',
                'keywords': ['diversos', 'outros', 'gasto'],
            },
        ]

        # Transfer category
        transfer_categories = [
            {
                'name': 'Transferências',
                'slug': 'transferencias',
                'category_type': 'transfer',
                'icon': '🔄',
                'color': '#64748B',
                'keywords': ['transferencia', 'transfer', 'entre contas'],
            },
        ]

        all_categories = income_categories + expense_categories + transfer_categories

        for cat_data in all_categories:
            category, created = TransactionCategory.objects.update_or_create(
                slug=cat_data['slug'],
                defaults={
                    **cat_data,
                    'is_system': True,
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Updated category: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully created/updated transaction categories')
        )