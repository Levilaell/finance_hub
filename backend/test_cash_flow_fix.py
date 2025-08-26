#!/usr/bin/env python
"""
Test script to validate the Cash Flow fix works correctly
"""

import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.banking.models import Transaction, BankAccount
from apps.companies.models import Company
from apps.reports.views import CashFlowDataView
from decimal import Decimal

def test_cash_flow_fix():
    """Test that the cash flow fix resolves the date_key mismatch"""
    
    print("🧪 Testing Cash Flow Fix...")
    
    User = get_user_model()
    
    # Get test data
    user = User.objects.first()
    if not user:
        print("❌ No users found - need to create test user first")
        return
    
    company = Company.objects.first()
    if not company:
        print("❌ No companies found - need to create test company first")
        return
    
    # Associate user with company if not already
    if not hasattr(user, 'company') or not user.company:
        user.company = company
        user.save()
        print(f"✅ Associated user {user.email} with company {company.name}")
    
    account = BankAccount.objects.filter(company=company).first()
    if not account:
        print("❌ No bank accounts found - need to create test account first")
        return
    
    print(f"✅ Using account: {account.name}")
    
    # Check if we have transactions
    tx_count = Transaction.active.filter(company=company).count()
    print(f"📊 Active transactions for company: {tx_count}")
    
    if tx_count == 0:
        print("⚠️  No transactions found - Cash Flow will be empty (expected)")
        print("   To test with data, create some transactions first")
        return
    
    # Test the API endpoint
    factory = RequestFactory()
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    request = factory.get('/api/reports/dashboard/cash-flow/', {
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    })
    request.user = user
    
    # Test the view
    view = CashFlowDataView()
    
    try:
        response = view.get(request)
        print(f"✅ API Response Status: {response.status_code}")
        
        if response.status_code == 200 and hasattr(response, 'data'):
            data = response.data if hasattr(response, 'data') else []
            print(f"📈 Cash Flow data points returned: {len(data)}")
            
            if len(data) > 0:
                print("✅ SUCCESS: Cash Flow data is now being returned!")
                
                # Show sample data
                sample = data[0] if data else {}
                print(f"📊 Sample data point: {sample}")
                
                # Calculate totals
                total_income = sum(d.get('income', 0) for d in data)
                total_expenses = sum(d.get('expenses', 0) for d in data)
                final_balance = data[-1].get('balance', 0) if data else 0
                
                print(f"💰 Period totals:")
                print(f"   Income: ${total_income:.2f}")
                print(f"   Expenses: ${total_expenses:.2f}") 
                print(f"   Final Balance: ${final_balance:.2f}")
                
                if total_income > 0 or total_expenses > 0:
                    print("🎯 CASH FLOW FIX SUCCESSFUL - Data is being processed!")
                else:
                    print("⚠️  Data returned but all zeros - check transaction types")
            else:
                print("❌ No data points returned - may need to check date range or transaction filtering")
        else:
            print(f"❌ API Error: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error details: {response.data}")
                
    except Exception as e:
        print(f"❌ Exception during API test: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎯 Test completed!")
    print("\nNext steps:")
    print("1. If successful locally, deploy to production")
    print("2. Clear production cache: python clear_cash_flow_cache.py")
    print("3. Test production endpoint")
    print("4. Refresh browser to see Cash Flow chart with data")

if __name__ == '__main__':
    test_cash_flow_fix()
