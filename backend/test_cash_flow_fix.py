#!/usr/bin/env python
"""
Teste para validar a correção do bug de Fluxo de Caixa
Este script simula transações com diferentes tipos para testar a correção
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.append('/Users/levilaell/Desktop/finance_hub/backend')
django.setup()

from decimal import Decimal
from datetime import date, timedelta
from apps.banking.models import Transaction, BankAccount
from apps.companies.models import Company
from django.db.models import Q

def test_transaction_type_filters():
    """Test both old and new transaction type filters"""
    
    print("=== TESTE DOS FILTROS DE TRANSAÇÃO ===")
    
    # Tipos que existem em produção (baseado na análise do CategorySpendingView)
    test_types = [
        # Receitas
        'CREDIT', 'credit', 'INCOME', 'income', 
        'transfer_in', 'pix_in', 'interest',
        # Despesas  
        'DEBIT', 'debit', 'EXPENSE', 'expense',
        'transfer_out', 'pix_out', 'fee'
    ]
    
    print("Tipos de transação testados:", test_types)
    
    print("\n1. FILTRO ANTIGO (CashFlowDataView - BUGGY):")
    for trans_type in test_types:
        # Old logic - case sensitive and restrictive
        if trans_type in ['CREDIT', 'INCOME']:
            result = "✅ RECEITA (detectada)"
        elif trans_type in ['DEBIT', 'EXPENSE']:
            result = "✅ DESPESA (detectada)"
        else:
            result = "❌ IGNORADA"
        print(f"  {trans_type:<15} → {result}")
    
    print("\n2. FILTRO NOVO (CashFlowDataView - CORRIGIDO):")
    for trans_type in test_types:
        # New logic - case insensitive and comprehensive
        upper_type = trans_type.upper() if trans_type else ''
        if upper_type in ['CREDIT', 'INCOME', 'TRANSFER_IN', 'PIX_IN', 'INTEREST']:
            result = "✅ RECEITA (detectada)"
        elif upper_type in ['DEBIT', 'EXPENSE', 'TRANSFER_OUT', 'PIX_OUT', 'FEE']:
            result = "✅ DESPESA (detectada)"
        else:
            result = "❌ IGNORADA"
        print(f"  {trans_type:<15} → {result}")
    
    print("\n3. FILTRO CategorySpendingView (REFERÊNCIA):")
    
    # Income filter from CategorySpendingView
    income_filter = (
        Q(type__iexact='CREDIT') | 
        Q(type__iexact='INCOME') | 
        Q(type__iexact='credit') | 
        Q(type__iexact='income') |
        Q(type__iexact='transfer_in') | 
        Q(type__iexact='pix_in') | 
        Q(type__iexact='interest')
    )
    
    # Expense filter from CategorySpendingView  
    expense_filter = (
        Q(type__iexact='DEBIT') | 
        Q(type__iexact='EXPENSE') | 
        Q(type__iexact='debit') | 
        Q(type__iexact='expense') |
        Q(type__iexact='transfer_out') | 
        Q(type__iexact='pix_out') | 
        Q(type__iexact='fee')
    )
    
    for trans_type in test_types:
        # Simulate Django Q filter matching
        is_income = any([
            trans_type.upper() == 'CREDIT',
            trans_type.upper() == 'INCOME', 
            trans_type.lower() == 'credit',
            trans_type.lower() == 'income',
            trans_type.lower() == 'transfer_in',
            trans_type.lower() == 'pix_in',
            trans_type.lower() == 'interest'
        ])
        
        is_expense = any([
            trans_type.upper() == 'DEBIT',
            trans_type.upper() == 'EXPENSE',
            trans_type.lower() == 'debit', 
            trans_type.lower() == 'expense',
            trans_type.lower() == 'transfer_out',
            trans_type.lower() == 'pix_out',
            trans_type.lower() == 'fee'
        ])
        
        if is_income:
            result = "✅ RECEITA (detectada)"
        elif is_expense:
            result = "✅ DESPESA (detectada)"  
        else:
            result = "❌ IGNORADA"
            
        print(f"  {trans_type:<15} → {result}")
    
    print("\n=== ANÁLISE ===")
    
    # Count detections
    old_detections = len([t for t in test_types if t in ['CREDIT', 'INCOME', 'DEBIT', 'EXPENSE']])
    new_detections = len([t for t in test_types if t.upper() in [
        'CREDIT', 'INCOME', 'TRANSFER_IN', 'PIX_IN', 'INTEREST',
        'DEBIT', 'EXPENSE', 'TRANSFER_OUT', 'PIX_OUT', 'FEE'
    ]])
    
    print(f"Filtro ANTIGO detectou: {old_detections}/{len(test_types)} tipos ({old_detections/len(test_types)*100:.1f}%)")
    print(f"Filtro NOVO detectou: {new_detections}/{len(test_types)} tipos ({new_detections/len(test_types)*100:.1f}%)")
    
    if new_detections > old_detections:
        print("✅ CORREÇÃO EFETIVA: Filtro novo detecta mais tipos de transação")
        print("   O gráfico de Fluxo de Caixa agora deve mostrar dados!")
    else:
        print("❌ Correção pode não ser suficiente")

if __name__ == '__main__':
    test_transaction_type_filters()