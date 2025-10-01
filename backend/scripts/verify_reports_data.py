#!/usr/bin/env python
"""
Script para verificar dados esperados nos gráficos de relatórios
Data de referência: 2025-10-01
"""

import os
import sys
import django
from datetime import datetime, timedelta
from collections import defaultdict
import json

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.banking.models import Transaction
from django.db.models import Sum, Count
from django.utils import timezone
import pytz

# Data de referência
REFERENCE_DATE = datetime(2025, 10, 1, 0, 0, 0)
TZ = pytz.timezone('America/Sao_Paulo')

def get_period_dates(period_name):
    """Retorna start_date e end_date para cada período"""
    ref = TZ.localize(REFERENCE_DATE)

    periods = {
        'todas': {
            'start': TZ.localize(datetime(2020, 1, 1, 0, 0, 0)),
            'end': ref
        },
        'mes_atual': {
            'start': ref.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            'end': ref.replace(day=31, hour=23, minute=59, second=59, microsecond=999999)
        },
        'ultimos_3_meses': {
            'start': ref - timedelta(days=90),
            'end': ref
        },
        'ultimos_6_meses': {
            'start': ref - timedelta(days=180),
            'end': ref
        },
        'ano_atual': {
            'start': TZ.localize(datetime(2025, 1, 1, 0, 0, 0)),
            'end': ref
        },
        'ano_anterior': {
            'start': TZ.localize(datetime(2024, 1, 1, 0, 0, 0)),
            'end': TZ.localize(datetime(2024, 12, 31, 23, 59, 59, 999999))
        }
    }

    return periods.get(period_name)

def calculate_summary(start_date, end_date):
    """Calcula resumo financeiro para um período"""
    transactions = Transaction.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    )

    income = transactions.filter(type='CREDIT').aggregate(
        total=Sum('amount')
    )['total'] or 0

    expenses = transactions.filter(type='DEBIT').aggregate(
        total=Sum('amount')
    )['total'] or 0

    balance = float(income) - float(expenses)

    return {
        'transactions_count': transactions.count(),
        'income': float(income),
        'expenses': float(expenses),
        'balance': balance
    }

def calculate_category_breakdown(start_date, end_date):
    """Calcula breakdown por categoria (top 10)"""
    expenses = Transaction.objects.filter(
        type='DEBIT',
        date__gte=start_date,
        date__lte=end_date
    )

    category_totals = defaultdict(float)
    for t in expenses:
        cat = t.user_category.name if t.user_category else (t.pluggy_category or 'Sem categoria')
        category_totals[cat] += float(t.amount)

    # Top 10 categorias
    sorted_categories = sorted(
        category_totals.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    return [
        {'name': cat, 'value': value}
        for cat, value in sorted_categories
    ]

def calculate_monthly_trends(start_date, end_date):
    """Calcula tendências mensais (receitas vs despesas)"""
    transactions = Transaction.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    )

    monthly_data = defaultdict(lambda: {'receitas': 0.0, 'despesas': 0.0})

    for t in transactions:
        month_key = t.date.strftime('%b/%y')  # Ex: "set/25"

        if t.is_income:
            monthly_data[month_key]['receitas'] += float(t.amount)
        if t.is_expense:
            monthly_data[month_key]['despesas'] += float(t.amount)

    # Ordenar por data e pegar últimos 12 meses
    sorted_months = sorted(monthly_data.items(), key=lambda x: datetime.strptime(x[0], '%b/%y'))

    return [
        {
            'mes': month,
            'receitas': data['receitas'],
            'despesas': data['despesas']
        }
        for month, data in sorted_months[-12:]
    ]

def calculate_daily_balance(start_date, end_date):
    """Calcula evolução diária do saldo (últimos 30 dias do período)"""
    transactions = Transaction.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')

    daily_balances = {}
    running_balance = 0.0

    for t in transactions:
        day_key = t.date.strftime('%d %b')

        if t.is_income:
            running_balance += float(t.amount)
        if t.is_expense:
            running_balance -= float(t.amount)

        daily_balances[day_key] = running_balance

    # Pegar últimos 30 dias
    sorted_days = list(daily_balances.items())[-30:]

    return [
        {'dia': day, 'saldo': balance}
        for day, balance in sorted_days
    ]

def main():
    """Executa verificação para todos os períodos"""

    periods = [
        ('todas', 'Todas'),
        ('mes_atual', 'Mês atual'),
        ('ultimos_3_meses', 'Últimos 3 meses'),
        ('ultimos_6_meses', 'Últimos 6 meses'),
        ('ano_atual', 'Ano atual'),
        ('ano_anterior', 'Ano anterior')
    ]

    results = {}

    for period_key, period_label in periods:
        dates = get_period_dates(period_key)

        if not dates:
            continue

        start = dates['start']
        end = dates['end']

        print(f"\n{'='*80}")
        print(f"PERÍODO: {period_label}")
        print(f"Range: {start.date()} até {end.date()}")
        print(f"{'='*80}")

        # 1. Resumo (Cards)
        summary = calculate_summary(start, end)
        print(f"\n[RESUMO FINANCEIRO]")
        print(f"  Transacoes: {summary['transactions_count']}")
        print(f"  Receitas: R$ {summary['income']:,.2f}")
        print(f"  Despesas: R$ {summary['expenses']:,.2f}")
        print(f"  Saldo: R$ {summary['balance']:,.2f}")

        # 2. Categorias (Pie Chart)
        categories = calculate_category_breakdown(start, end)
        print(f"\n[TOP 10 CATEGORIAS DE DESPESAS]")
        total_expenses = sum(cat['value'] for cat in categories)
        for i, cat in enumerate(categories, 1):
            percentage = (cat['value'] / total_expenses * 100) if total_expenses > 0 else 0
            print(f"  {i}. {cat['name']}: R$ {cat['value']:,.2f} ({percentage:.1f}%)")

        # 3. Tendências Mensais (Bar Chart)
        monthly = calculate_monthly_trends(start, end)
        print(f"\n[TENDENCIAS MENSAIS - ultimos 12 meses]")
        for month_data in monthly:
            print(f"  {month_data['mes']}: Receitas R$ {month_data['receitas']:,.2f} | Despesas R$ {month_data['despesas']:,.2f}")

        # 4. Evolução Diária (Line Chart)
        daily = calculate_daily_balance(start, end)
        print(f"\n[EVOLUCAO DO SALDO - ultimos 30 dias]")
        if len(daily) <= 10:
            for day_data in daily:
                print(f"  {day_data['dia']}: R$ {day_data['saldo']:,.2f}")
        else:
            print(f"  Primeiros 3 dias:")
            for day_data in daily[:3]:
                print(f"    {day_data['dia']}: R$ {day_data['saldo']:,.2f}")
            print(f"  ...")
            print(f"  Últimos 3 dias:")
            for day_data in daily[-3:]:
                print(f"    {day_data['dia']}: R$ {day_data['saldo']:,.2f}")

        # Salvar resultados
        results[period_key] = {
            'label': period_label,
            'date_range': {
                'start': start.isoformat(),
                'end': end.isoformat()
            },
            'summary': summary,
            'categories': categories,
            'monthly': monthly,
            'daily': daily
        }

    # Salvar em JSON para referência
    output_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'claudedocs',
        'expected_report_data.json'
    )

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"[OK] Resultados salvos em: {output_file}")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
