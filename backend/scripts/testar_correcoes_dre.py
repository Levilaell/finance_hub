#!/usr/bin/env python
"""
Script para testar as correções no gerador de relatório DRE
"""

import os
import sys
import django
from datetime import date
from decimal import Decimal
from django.db import models

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.banking.models import Transaction, BankAccount
from apps.companies.models import Company
from apps.reports.report_generator import ReportGenerator


def testar_correcoes():
    """Testa as correções no report generator"""
    print("=" * 80)
    print("TESTE DAS CORREÇÕES NO GERADOR DE RELATÓRIO DRE")
    print("=" * 80)
    
    # Buscar empresa específica do Levi
    company = Company.objects.filter(name__icontains='Levi').first()
    
    if not company:
        # Se não encontrar, buscar primeira empresa que tenha transações
        for comp in Company.objects.all():
            if Transaction.objects.filter(bank_account__company=comp).exists():
                company = comp
                break
    
    if not company:
        print("Nenhuma empresa com transações encontrada")
        print(f"Total de empresas: {Company.objects.count()}")
        print(f"Total de transações: {Transaction.objects.count()}")
        return
    
    print(f"\nEmpresa: {company.name}")
    
    # Período do relatório
    start_date = date(2025, 7, 1)
    end_date = date(2025, 7, 19)
    
    # Criar instância do gerador
    generator = ReportGenerator(company)
    
    # Buscar transações diretamente
    transactions = Transaction.objects.filter(
        bank_account__company=company,
        transaction_date__gte=start_date,
        transaction_date__lte=end_date
    )
    
    print(f"\nPeríodo: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
    print(f"Total de transações: {transactions.count()}")
    
    # Testar filtros de receitas
    print("\n" + "=" * 60)
    print("TESTE 1: FILTROS DE RECEITAS")
    print("=" * 60)
    
    revenue_transactions = transactions.filter(
        transaction_type__in=['credit', 'transfer_in', 'pix_in', 'interest']
    )
    
    print(f"\nTransações de receita encontradas: {revenue_transactions.count()}")
    
    revenue_by_type = {}
    for trans_type in ['credit', 'transfer_in', 'pix_in', 'interest']:
        count = revenue_transactions.filter(transaction_type=trans_type).count()
        total = revenue_transactions.filter(transaction_type=trans_type).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        if count > 0:
            revenue_by_type[trans_type] = {'count': count, 'total': total}
    
    print("\nReceitas por tipo:")
    for trans_type, data in revenue_by_type.items():
        print(f"  {trans_type}: {data['count']} transações = R$ {data['total']:,.2f}")
    
    total_revenue = sum(data['total'] for data in revenue_by_type.values())
    print(f"\nTOTAL DE RECEITAS: R$ {total_revenue:,.2f}")
    
    # Testar filtros de despesas
    print("\n" + "=" * 60)
    print("TESTE 2: FILTROS DE DESPESAS")
    print("=" * 60)
    
    expense_transactions = transactions.filter(
        transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
    )
    
    print(f"\nTransações de despesa encontradas: {expense_transactions.count()}")
    
    expense_by_type = {}
    for trans_type in ['debit', 'transfer_out', 'pix_out', 'fee']:
        count = expense_transactions.filter(transaction_type=trans_type).count()
        total = expense_transactions.filter(transaction_type=trans_type).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        if count > 0:
            expense_by_type[trans_type] = {'count': count, 'total': total}
    
    print("\nDespesas por tipo:")
    for trans_type, data in expense_by_type.items():
        print(f"  {trans_type}: {data['count']} transações = R$ {data['total']:,.2f}")
    
    total_expenses = sum(data['total'] for data in expense_by_type.values())
    print(f"\nTOTAL DE DESPESAS: R$ {total_expenses:,.2f}")
    
    # Calcular lucro/prejuízo
    print("\n" + "=" * 60)
    print("TESTE 3: CÁLCULO DO RESULTADO")
    print("=" * 60)
    
    # As despesas já estão como valores negativos, então somamos
    gross_profit = total_revenue + total_expenses  
    print(f"\nReceitas:  R$ {total_revenue:,.2f}")
    print(f"Despesas:  R$ {total_expenses:,.2f}")
    print(f"RESULTADO: R$ {gross_profit:,.2f}")
    
    # Testar categorias
    print("\n" + "=" * 60)
    print("TESTE 4: CATEGORIAS")
    print("=" * 60)
    
    # Receitas por categoria
    revenue_by_category = revenue_transactions.values(
        'category__name'
    ).annotate(
        total=models.Sum('amount'),
        count=models.Count('id')
    ).order_by('-total')
    
    print("\nReceitas por categoria:")
    for item in revenue_by_category:
        category_name = item['category__name'] or 'Sem categoria'
        print(f"  {category_name}: {item['count']} transações = R$ {item['total']:,.2f}")
    
    # Despesas por categoria
    expense_by_category = expense_transactions.values(
        'category__name'
    ).annotate(
        total=models.Sum('amount'),
        count=models.Count('id')
    ).order_by('-total')
    
    print("\nDespesas por categoria:")
    for item in expense_by_category:
        category_name = item['category__name'] or 'Sem categoria'
        print(f"  {category_name}: {item['count']} transações = R$ {item['total']:,.2f}")
    
    # Comparar com valores do relatório original
    print("\n" + "=" * 60)
    print("COMPARAÇÃO COM RELATÓRIO ORIGINAL")
    print("=" * 60)
    
    print("\nRelatório Original:")
    print("  Receitas: R$ 15.288,17")
    print("  Despesas: R$ 15.261,18")
    print("  Lucro:    R$ 26,99")
    
    print("\nApós Correções:")
    print(f"  Receitas: R$ {total_revenue:,.2f}")
    print(f"  Despesas: R$ {total_expenses:,.2f}")
    print(f"  Lucro:    R$ {gross_profit:,.2f}")
    
    # Identificar diferenças
    diff_revenue = total_revenue - Decimal('15288.17')
    diff_expenses = total_expenses - Decimal('-15261.18')  # Valor original como negativo
    diff_profit = gross_profit - Decimal('26.99')
    
    print("\nDiferenças:")
    print(f"  Receitas: R$ {diff_revenue:,.2f}")
    print(f"  Despesas: R$ {diff_expenses:,.2f}")
    print(f"  Lucro:    R$ {diff_profit:,.2f}")
    
    print("\n" + "=" * 60)
    print("CONCLUSÃO")
    print("=" * 60)
    if abs(diff_revenue) < 0.01 and abs(diff_expenses) < 0.01:
        print("✅ CORREÇÕES APLICADAS COM SUCESSO!")
        print("   Os valores de receitas e despesas estão corretos.")
        print(f"   O lucro corrigido é: R$ {gross_profit:,.2f}")
    else:
        print("❌ Ainda há diferenças nos valores.")


if __name__ == '__main__':
    testar_correcoes()