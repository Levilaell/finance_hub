#!/usr/bin/env python
"""
Script para testar a formatação do relatório DRE após as correções
"""

import os
import sys
import django
from datetime import date

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.banking.models import Transaction, BankAccount
from apps.companies.models import Company
from apps.reports.report_generator import ReportGenerator


def testar_formatacao():
    """Testa a formatação do relatório DRE"""
    print("=" * 80)
    print("TESTE DE FORMATAÇÃO DO RELATÓRIO DRE")
    print("=" * 80)
    
    # Buscar empresa
    company = Company.objects.filter(name__icontains='Levi').first()
    
    if not company:
        print("Nenhuma empresa encontrada")
        return
    
    print(f"Empresa: {company.name}")
    
    # Período do relatório
    start_date = date(2025, 7, 1)
    end_date = date(2025, 7, 19)
    
    # Criar instância do gerador
    generator = ReportGenerator(company)
    
    # Buscar transações
    transactions = Transaction.objects.filter(
        bank_account__company=company,
        transaction_date__gte=start_date,
        transaction_date__lte=end_date
    )
    
    print(f"\nPeríodo: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
    print(f"Total de transações: {transactions.count()}")
    
    # Testar cálculos internos do gerador
    print("\n" + "=" * 60)
    print("TESTE DOS MÉTODOS INTERNOS")
    print("=" * 60)
    
    # Teste do método _calculate_summary_stats
    stats = generator._calculate_summary_stats(transactions)
    print(f"\nSummary Stats:")
    print(f"  Total Income: R$ {stats['total_income']:,.2f}")
    print(f"  Total Expenses: R$ {stats['total_expenses']:,.2f}")
    print(f"  Net Balance: R$ {stats['net_balance']:,.2f}")
    
    # Teste do método _calculate_monthly_breakdown
    monthly = generator._calculate_monthly_breakdown(transactions, start_date, end_date)
    print(f"\nMonthly Breakdown:")
    for month_data in monthly:
        print(f"  {month_data['month']}: Income R$ {month_data['income']:,.2f}, "
              f"Expenses R$ {month_data['expenses']:,.2f}, "
              f"Profit R$ {month_data['profit']:,.2f}")
    
    # Teste do método _calculate_category_breakdown  
    categories = generator._calculate_category_breakdown(transactions)
    print(f"\nCategory Breakdown (Expenses):")
    total_cat_expenses = sum(abs(item['total']) for item in categories)
    print(f"  Total Category Expenses: R$ {total_cat_expenses:,.2f}")
    
    for item in categories[:5]:  # Top 5
        percentage = (abs(item['total']) / total_cat_expenses * 100) if total_cat_expenses > 0 else 0
        print(f"  {item['name']}: R$ {abs(item['total']):,.2f} ({percentage:.1f}%)")
    
    print("\n" + "=" * 60)
    print("VALORES PARA VERIFICAÇÃO NO RELATÓRIO")
    print("=" * 60)
    
    print(f"\nEsperado no relatório:")
    print(f"  RECEITAS: {stats['total_income']:,.2f} (positivo)")
    print(f"  DESPESAS: -{stats['total_expenses']:,.2f} (negativo formatado)")
    print(f"  LUCRO/PREJUÍZO: {stats['net_balance']:,.2f}")
    print(f"  Lucro Mensal (julho): {monthly[0]['profit']:,.2f}")
    
    if categories:
        print(f"\nPercentuais de categorias de despesa:")
        for item in categories[:3]:
            percentage = (abs(item['total']) / total_cat_expenses * 100) if total_cat_expenses > 0 else 0
            print(f"  {item['name']}: {percentage:.1f}%")


if __name__ == '__main__':
    testar_formatacao()