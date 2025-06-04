"""
Create default bank providers
"""
from django.core.management.base import BaseCommand

from apps.banking.models import BankProvider


class Command(BaseCommand):
    help = 'Create default Brazilian bank providers'

    def handle(self, *args, **options):
        banks = [
            {
                'name': 'Banco do Brasil',
                'code': '001',
                'color': '#FFFF00',
                'is_open_banking': True,
            },
            {
                'name': 'Bradesco',
                'code': '237',
                'color': '#CC092F',
                'is_open_banking': True,
            },
            {
                'name': 'Itaú',
                'code': '341',
                'color': '#FF7800',
                'is_open_banking': True,
            },
            {
                'name': 'Santander',
                'code': '033',
                'color': '#EC0000',
                'is_open_banking': True,
            },
            {
                'name': 'Caixa Econômica Federal',
                'code': '104',
                'color': '#005CA9',
                'is_open_banking': True,
            },
            {
                'name': 'Nubank',
                'code': '260',
                'color': '#8A05BE',
                'is_open_banking': True,
                'requires_agency': False,
            },
            {
                'name': 'Inter',
                'code': '077',
                'color': '#FF8700',
                'is_open_banking': True,
            },
            {
                'name': 'C6 Bank',
                'code': '336',
                'color': '#242424',
                'is_open_banking': True,
            },
            {
                'name': 'Banco Original',
                'code': '212',
                'color': '#00A868',
                'is_open_banking': True,
            },
            {
                'name': 'Mercado Pago',
                'code': '323',
                'color': '#009EE3',
                'is_open_banking': True,
                'requires_agency': False,
            },
        ]

        for bank_data in banks:
            bank, created = BankProvider.objects.update_or_create(
                code=bank_data['code'],
                defaults=bank_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created bank: {bank.name}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Updated bank: {bank.name}')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully created/updated bank providers')
        )