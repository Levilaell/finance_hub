from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import requests
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Test simplified authentication system'
    
    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True)
        parser.add_argument('--password', type=str, required=True)
    
    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        
        self.stdout.write("🧪 Testando autenticação simplificada...")
        
        # Test 1: Token creation
        try:
            user = User.objects.get(email=email)
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            self.stdout.write(f"✅ Token criado com sucesso")
            self.stdout.write(f"   Access token: {len(str(access))} chars")
            self.stdout.write(f"   Refresh token: {len(str(refresh))} chars")
        except Exception as e:
            self.stdout.write(f"❌ Falha na criação do token: {e}")
            return
        
        # Test 2: Login via API
        try:
            response = requests.post('http://localhost:8000/api/auth/login/', {
                'email': email,
                'password': password
            })
            if response.status_code == 200:
                data = response.json()
                self.stdout.write(f"✅ Login via API bem-sucedido")
                self.stdout.write(f"   Usuário: {data.get('user', {}).get('email')}")
            else:
                self.stdout.write(f"❌ Login via API falhou: {response.status_code}")
                self.stdout.write(f"   Erro: {response.text}")
        except Exception as e:
            self.stdout.write(f"❌ Erro na requisição de login: {e}")
        
        self.stdout.write("\n✅ Teste de autenticação concluído")
