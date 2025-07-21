"""
Check webhooks registered in Pluggy
"""
from django.core.management.base import BaseCommand
from apps.banking.pluggy_client import PluggyClient
import asyncio
import json


class Command(BaseCommand):
    help = 'Check webhooks registered in Pluggy'

    def handle(self, *args, **options):
        self.stdout.write("=== Checking Pluggy Webhooks ===\n")
        
        async def check_webhooks():
            try:
                async with PluggyClient() as client:
                    # Get registered webhooks
                    response = await client._request('GET', '/webhooks')
                    
                    if response.get('results'):
                        self.stdout.write(f"Found {len(response['results'])} webhooks:\n")
                        
                        for webhook in response['results']:
                            self.stdout.write(f"ID: {webhook.get('id')}")
                            self.stdout.write(f"  URL: {webhook.get('url')}")
                            self.stdout.write(f"  Events: {', '.join(webhook.get('event', []))}")
                            self.stdout.write(f"  Created: {webhook.get('createdAt')}")
                            self.stdout.write(f"  Active: {webhook.get('isActive', True)}")
                            self.stdout.write("")
                    else:
                        self.stdout.write(self.style.WARNING("No webhooks found"))
                        
                    return response
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error checking webhooks: {e}"))
                return None
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(check_webhooks())
            
            if result:
                self.stdout.write("\n=== Webhook Status ===")
                
                expected_url = "https://finance-backend-production-29df.up.railway.app/api/banking/pluggy/webhook/"
                webhook_found = False
                
                for webhook in result.get('results', []):
                    if webhook.get('url') == expected_url:
                        webhook_found = True
                        if webhook.get('isActive', True):
                            self.stdout.write(self.style.SUCCESS(f"✅ Webhook is registered and active"))
                        else:
                            self.stdout.write(self.style.ERROR(f"❌ Webhook is registered but INACTIVE"))
                        break
                
                if not webhook_found:
                    self.stdout.write(self.style.ERROR(f"❌ Expected webhook URL not found: {expected_url}"))
                    self.stdout.write("\nTo register the webhook, run:")
                    self.stdout.write("python manage.py setup_pluggy_webhook")
                    
        finally:
            loop.close()