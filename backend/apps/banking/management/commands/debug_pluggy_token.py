# backend/apps/banking/management/commands/debug_pluggy_token.py
from django.core.management.base import BaseCommand
from apps.banking.pluggy_client import PluggyClient
import asyncio
import json

class Command(BaseCommand):
    help = 'Debug Pluggy token creation'

    async def test_token(self):
        async with PluggyClient() as client:
            # 1. Testar autenticação
            self.stdout.write("1. Testing authentication...")
            await client._ensure_authenticated()
            self.stdout.write(f"✓ Access token: {client._access_token[:50]}...")
            
            # 2. Criar connect token RAW
            self.stdout.write("\n2. Creating connect token...")
            response = await client.client.post(
                f"{client.base_url}/connect_token",
                json={},
                headers=client._get_headers()
            )
            
            self.stdout.write(f"Status: {response.status_code}")
            self.stdout.write(f"Headers: {dict(response.headers)}")
            
            raw_text = response.text
            self.stdout.write(f"\nRaw response:\n{raw_text}")
            
            if response.status_code == 200:
                data = response.json()
                self.stdout.write(f"\nParsed JSON:\n{json.dumps(data, indent=2)}")
                
                # Procurar o token em todos os campos possíveis
                possible_fields = ['accessToken', 'access_token', 'connectToken', 'token']
                for field in possible_fields:
                    if field in data:
                        self.stdout.write(f"\n✓ Found token in field '{field}'")
                        self.stdout.write(f"Token value: {data[field][:100]}...")

    def handle(self, *args, **options):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.test_token())
        finally:
            loop.close()