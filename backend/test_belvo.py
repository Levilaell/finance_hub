#!/usr/bin/env python
"""Test Belvo integration"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Add .env path explicitly
from decouple import config
print(f"Loading from .env file...")

django.setup()

from apps.banking.belvo_client import BelvoClient

def test_belvo_connection():
    """Test basic Belvo API connection"""
    print("Testing Belvo API connection...")
    
    # Check settings directly
    from django.conf import settings
    print(f"\nSettings check:")
    print(f"BELVO_SECRET_ID from settings: {getattr(settings, 'BELVO_SECRET_ID', 'NOT SET')[:10] if getattr(settings, 'BELVO_SECRET_ID', '') else 'NOT SET'}...")
    print(f"BELVO_BASE_URL from settings: {getattr(settings, 'BELVO_BASE_URL', 'NOT SET')}")
    
    client = BelvoClient()
    print(f"\nClient check:")
    print(f"Base URL: {client.base_url}")
    print(f"Secret ID: {client.secret_id[:10] if client.secret_id else 'NOT SET'}...")
    print(f"Has password: {'Yes' if client.secret_password else 'No'}")
    
    try:
        # Test getting institutions
        print("\nFetching institutions...")
        institutions = client.get_institutions()
        
        if institutions:
            print(f"Found {len(institutions)} institutions")
            # Show first 3 institutions
            for inst in institutions[:3]:
                print(f"- {inst.get('display_name', inst.get('name'))} ({inst.get('name')})")
        else:
            print("No institutions found")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_belvo_connection()