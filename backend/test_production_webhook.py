"""
Test webhook directly with production data
"""
import requests
import json

def test_webhook():
    # Test different account IDs that might exist in production
    webhook_url = "https://finance-backend-production-29df.up.railway.app/api/banking/pluggy/webhook/"
    
    # Possible external IDs based on your local data
    test_cases = [
        {
            "name": "Test with local external_id",
            "payload": {
                "event": "transactions/created",
                "data": {
                    "accountId": "f7829b8c-2b4a-4ffb-99ad-2d4b76dc46ed",
                    "count": 1,
                    "createdAt": "2025-07-21T20:00:00.000Z"
                }
            }
        },
        {
            "name": "Test item update",
            "payload": {
                "event": "item/updated",
                "data": {
                    "id": "2077a13a-a1de-4489-af5d-dd9a601ff5e3",
                    "status": "ACTIVE"
                }
            }
        }
    ]
    
    for test in test_cases:
        print(f"\n=== {test['name']} ===")
        print(f"Payload: {json.dumps(test['payload'], indent=2)}")
        
        response = requests.post(
            webhook_url,
            json=test['payload'],
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
    
    # Try to find the account using the account number
    print("\n=== Testing with account lookup ===")
    
    # The account number from production is 20414083-8
    # Let's see if we can trigger a sync differently
    print("\nBased on the production data:")
    print("- Account ID: 8")
    print("- Account Number: 20414083-8")
    print("- Bank: Inter (pluggy_215)")
    print("- 157 transactions synced")
    print("\nThe account IS connected via Pluggy (it has 157 real transactions)")
    print("But the external_id is not being shown in the API response")
    print("\nPossible issues:")
    print("1. The BankAccountSerializer doesn't include external_id field")
    print("2. The account might have been created differently in production")
    print("3. The webhook is working but Pluggy isn't sending events for new transactions")

if __name__ == "__main__":
    test_webhook()