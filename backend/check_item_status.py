"""Check Pluggy item status"""
import requests
import asyncio
from apps.banking.pluggy_client import PluggyClient

async def check_item():
    item_id = "3d423d87-a59d-4349-a5bb-2e69b60e9382"  # From production
    
    async with PluggyClient() as client:
        item = await client.get_item(item_id)
        
        print(f"Item ID: {item_id}")
        print(f"Status: {item.get('status')}")
        print(f"Created: {item.get('createdAt')}")
        print(f"Updated: {item.get('updatedAt')}")
        
        if 'error' in item:
            print(f"Error: {item.get('error')}")
        
        # Calculate hours since update
        if item.get('updatedAt'):
            from datetime import datetime
            updated = datetime.fromisoformat(item['updatedAt'].replace('Z', '+00:00'))
            now = datetime.now(updated.tzinfo)
            hours = (now - updated).total_seconds() / 3600
            print(f"Hours since update: {hours:.1f}")
        
        return item

# Also try manual sync
def try_manual_sync():
    print("\n=== Tentando sincronização manual ===")
    
    # Login
    r = requests.post(
        "https://finance-backend-production-29df.up.railway.app/api/auth/login/",
        json={"email": "levilaelsilvaa@gmail.com", "password": "Levi123*"}
    )
    token = r.json()['tokens']['access']
    headers = {"Authorization": f"Bearer {token}"}
    
    # Sync
    sync_response = requests.post(
        "https://finance-backend-production-29df.up.railway.app/api/banking/pluggy/accounts/8/sync/",
        headers=headers
    )
    
    print(f"Status: {sync_response.status_code}")
    print(f"Response: {sync_response.json()}")

if __name__ == "__main__":
    # Check item
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(check_item())
    finally:
        loop.close()
    
    # Try manual sync
    try_manual_sync()