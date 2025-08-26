#!/usr/bin/env python
"""
Clear cash flow cache to ensure fresh data after bug fix
This should be run in production after deploying the fix
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.core.cache import cache
from apps.companies.models import Company

def clear_cash_flow_cache():
    """Clear all cash flow related cache keys"""
    
    print("🧹 Clearing Cash Flow cache...")
    
    # Get all companies to clear their specific cache keys
    companies = Company.objects.all()
    
    cache_keys_cleared = 0
    
    # Clear specific cash flow cache keys
    for company in companies:
        # Pattern: f"cashflow_data_{company.id}_{start_date}_{end_date}"
        # We can't enumerate all possible date combinations, so we'll clear the entire cache
        pass
    
    # Clear entire cache (safest approach after critical bug fix)
    cache.clear()
    print("✅ Entire cache cleared")
    
    # Test that cache is actually cleared
    test_key = "test_cache_cleared"
    cache.set(test_key, "test_value", 60)
    
    if cache.get(test_key):
        print("✅ Cache is working")
        cache.delete(test_key)
    else:
        print("❌ Cache might not be working")
    
    print("🎯 Cache clearing completed!")
    print()
    print("Next steps:")
    print("1. Deploy the fixed code to production")
    print("2. Run this script in production: python clear_cash_flow_cache.py")
    print("3. Test the cash flow endpoint")
    print("4. Refresh the reports page")

if __name__ == '__main__':
    clear_cash_flow_cache()