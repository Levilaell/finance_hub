#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.reports.report_generator import ReportGenerator
from apps.companies.models import Company
from apps.banking.models import Transaction
from datetime import datetime, timedelta
from collections import defaultdict
from decimal import Decimal
import json

# Get the first company
company = Company.objects.first()
if not company:
    print('No company found')
    sys.exit(1)

generator = ReportGenerator(company)
end_date = datetime.now().date()
start_date = end_date - timedelta(days=30)

print(f"Company: {company.name}")
print(f"Period: {start_date} to {end_date}")

# Get transactions like in the report
transactions = generator._get_filtered_transactions(start_date, end_date, None)

print(f"\nTotal transactions: {transactions.count()}")

# Debug category trends calculation
print("\n=== DEBUGGING CATEGORY TRENDS ===")
trends = defaultdict(lambda: defaultdict(Decimal))

transfer_pix_transactions = []
for trans in transactions:
    if trans.transaction_type in ['debit', 'transfer_out', 'pix_out', 'fee']:
        month_key = trans.transaction_date.strftime('%Y-%m')
        category_name = trans.category.name if trans.category else 'Sem categoria'
        
        # Debug Transfer - Pix specifically
        if category_name == 'Transfer - Pix':
            transfer_pix_transactions.append({
                'date': trans.transaction_date,
                'amount': trans.amount,
                'abs_amount': abs(trans.amount),
                'description': trans.description[:50]
            })
        
        trends[category_name][month_key] += abs(trans.amount)

print(f"\nTransfer - Pix transactions:")
total_transfer_pix = Decimal('0')
for t in transfer_pix_transactions:
    print(f"  {t['date']}: {t['amount']} (abs: {t['abs_amount']}) - {t['description']}")
    total_transfer_pix += t['abs_amount']

print(f"\nCalculated Transfer - Pix total: {total_transfer_pix}")
print(f"From trends dict: {dict(trends.get('Transfer - Pix', {}))}")

# Show all category trends
print(f"\nAll category trends:")
for cat_name, monthly_data in trends.items():
    for month, amount in monthly_data.items():
        print(f"  {cat_name} - {month}: {amount}")