#!/usr/bin/env python
"""
Test upgrade API endpoint
"""
import requests
import json

# Configuration
API_URL = "http://localhost:8000/api"
TOKEN = "your_auth_token_here"  # Replace with actual token

def test_upgrade_api():
    """Test the upgrade endpoint"""
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Test data
    upgrade_data = {
        "plan_id": 3,  # Enterprise plan
        "billing_cycle": "monthly"
    }
    
    print("Testing Upgrade API Endpoint")
    print("="*50)
    print(f"URL: {API_URL}/companies/subscription/upgrade/")
    print(f"Data: {json.dumps(upgrade_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{API_URL}/companies/subscription/upgrade/",
            headers=headers,
            json=upgrade_data
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            if 'proration' in data:
                print("\n✅ Proration calculated successfully!")
                print(f"   Net amount: R$ {data['proration']['net_amount']}")
                print(f"   Days remaining: {data['proration']['days_remaining']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

# Example of expected response:
expected_response = """
{
    "message": "Subscription upgraded successfully",
    "new_plan": {
        "id": 3,
        "name": "Empresarial",
        "price_monthly": "149.90"
    },
    "proration": {
        "credit": 29.95,
        "charge": 74.95,
        "net_amount": 45.00,
        "days_remaining": 15,
        "current_plan": "Professional",
        "new_plan": "Empresarial",
        "billing_cycle": "monthly"
    },
    "payment_required": true,
    "amount": 45.00
}
"""

print("\n\nExpected Response Format:")
print("="*50)
print(expected_response)

if __name__ == "__main__":
    print("\nNote: This script requires:")
    print("1. Backend server running on localhost:8000")
    print("2. Valid auth token from a logged-in user")
    print("3. User must have an active subscription")
    print("\nTo get a token, login via frontend and check localStorage")
    
    # Uncomment to run:
    # test_upgrade_api()