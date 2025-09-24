"""
Test Pluggy API credentials and connection
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os
import requests


class Command(BaseCommand):
    help = 'Test Pluggy API credentials'

    def handle(self, *args, **options):
        self.stdout.write("Testing Pluggy API credentials...")

        # Check environment variables
        client_id = os.getenv('PLUGGY_CLIENT_ID')
        client_secret = os.getenv('PLUGGY_CLIENT_SECRET')
        api_url = os.getenv('PLUGGY_API_URL', 'https://api.pluggy.ai')

        if not client_id:
            self.stdout.write(self.style.ERROR('❌ PLUGGY_CLIENT_ID not set'))
            return

        if not client_secret:
            self.stdout.write(self.style.ERROR('❌ PLUGGY_CLIENT_SECRET not set'))
            return

        self.stdout.write(f"✅ Client ID: {client_id[:10]}...")
        self.stdout.write(f"✅ Client Secret: {client_secret[:10]}...")
        self.stdout.write(f"✅ API URL: {api_url}")

        # Test authentication
        self.stdout.write("\nTesting authentication...")
        auth_url = f"{api_url}/auth"

        payload = {
            "clientId": client_id,
            "clientSecret": client_secret
        }

        try:
            response = requests.post(auth_url, json=payload)

            if response.status_code == 200:
                data = response.json()
                api_key = data.get('apiKey')
                if api_key:
                    self.stdout.write(self.style.SUCCESS(f"✅ Authentication successful! API Key: {api_key[:20]}..."))

                    # Test connect token
                    self.stdout.write("\nTesting connect token...")
                    token_url = f"{api_url}/connect_token"
                    headers = {'X-API-KEY': api_key}

                    token_response = requests.post(token_url, headers=headers, json={})

                    if token_response.status_code == 200:
                        token_data = token_response.json()
                        access_token = token_data.get('accessToken')
                        if access_token:
                            self.stdout.write(self.style.SUCCESS(f"✅ Connect token obtained: {access_token[:20]}..."))
                        else:
                            self.stdout.write(self.style.ERROR(f"❌ No accessToken in response: {token_data}"))
                    else:
                        self.stdout.write(self.style.ERROR(f"❌ Connect token failed: {token_response.status_code}"))
                        self.stdout.write(f"Response: {token_response.text}")
                else:
                    self.stdout.write(self.style.ERROR(f"❌ No apiKey in response: {data}"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ Authentication failed: {response.status_code}"))
                self.stdout.write(f"Response: {response.text}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))