"""
Test webhook with correct production external_id
"""
import requests
import json

def test_correct_webhook():
    webhook_url = "https://finance-backend-production-29df.up.railway.app/api/banking/pluggy/webhook/"
    
    # Test with the CORRECT external_id from production
    correct_external_id = "e71dd982-7747-460a-bfc7-4ee574fe2c84"
    
    payload = {
        "event": "transactions/created",
        "data": {
            "accountId": correct_external_id,
            "count": 1,
            "createdAt": "2025-07-21T20:00:00.000Z"
        }
    }
    
    print("Testing webhook with CORRECT production external_id")
    print(f"External ID: {correct_external_id}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        webhook_url,
        json=payload,
        headers={'Content-Type': 'application/json'},
        timeout=30
    )
    
    print(f"\nStatus: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("\n✅ SUCCESS! Webhook is working correctly!")
        print("The issue was that the external_id in production is different from local")
        print("\nNext steps:")
        print("1. When you make a real transaction, Pluggy should send a webhook")
        print("2. The webhook will use this external_id: " + correct_external_id)
        print("3. Your transactions should sync automatically")
    else:
        print("\n❌ Still having issues")

if __name__ == "__main__":
    test_correct_webhook()