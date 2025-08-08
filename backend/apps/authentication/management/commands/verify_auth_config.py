"""
Verify and fix authentication configuration
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
import requests

User = get_user_model()


class Command(BaseCommand):
    help = 'Verify and fix authentication configuration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🔍 Verificando Configuração de Autenticação\n'))
        
        # 1. Check cookie settings
        self.stdout.write('1️⃣ Configurações de Cookies JWT:')
        self.stdout.write(f'   JWT_COOKIE_SECURE: {getattr(settings, "JWT_COOKIE_SECURE", "Not set")}')
        self.stdout.write(f'   JWT_COOKIE_SAMESITE: {getattr(settings, "JWT_COOKIE_SAMESITE", "Not set")}')
        self.stdout.write(f'   JWT_COOKIE_DOMAIN: {getattr(settings, "JWT_COOKIE_DOMAIN", "Not set")}')
        self.stdout.write(f'   JWT_ACCESS_COOKIE_NAME: {getattr(settings, "JWT_ACCESS_COOKIE_NAME", "Not set")}')
        self.stdout.write(f'   JWT_REFRESH_COOKIE_NAME: {getattr(settings, "JWT_REFRESH_COOKIE_NAME", "Not set")}\n')
        
        # Check if SameSite=None is set
        samesite = getattr(settings, "JWT_COOKIE_SAMESITE", "Not set")
        if samesite == "Lax":
            self.stdout.write(self.style.WARNING('   ⚠️  JWT_COOKIE_SAMESITE está configurado como "Lax"'))
            self.stdout.write('   Isso pode causar problemas com cross-origin requests.')
            self.stdout.write('   Para desenvolvimento, considere usar None ou configurar proxy.\n')
        
        # 2. Check CORS settings
        self.stdout.write('2️⃣ Configurações CORS:')
        self.stdout.write(f'   CORS_ALLOWED_ORIGINS: {getattr(settings, "CORS_ALLOWED_ORIGINS", [])}')
        self.stdout.write(f'   CORS_ALLOW_CREDENTIALS: {getattr(settings, "CORS_ALLOW_CREDENTIALS", False)}\n')
        
        # 3. Test authentication flow
        self.stdout.write('3️⃣ Testando fluxo de autenticação...')
        
        # Create a session
        session = requests.Session()
        base_url = 'http://localhost:8000'
        
        # Test login
        try:
            login_response = session.post(
                f'{base_url}/api/auth/login/',
                json={'email': 'arabel.bebel@hotmail.com', 'password': 'Levi123*'},
                headers={'Content-Type': 'application/json'}
            )
            
            if login_response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('   ✅ Login bem-sucedido'))
                
                # Check cookies
                self.stdout.write('\n4️⃣ Cookies recebidos:')
                for cookie in session.cookies:
                    self.stdout.write(f'   🍪 {cookie.name}')
                    self.stdout.write(f'      - Domain: {cookie.domain}')
                    self.stdout.write(f'      - Path: {cookie.path}')
                    self.stdout.write(f'      - Secure: {cookie.secure}')
                    self.stdout.write(f'      - HttpOnly: {cookie.has_nonstandard_attr("HttpOnly")}')
                    self.stdout.write(f'      - SameSite: {cookie.get_nonstandard_attr("SameSite") or "Not set"}')
                
                # Test reports endpoint
                self.stdout.write('\n5️⃣ Testando endpoint de reports...')
                reports_response = session.get(f'{base_url}/api/reports/reports/')
                
                if reports_response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS('   ✅ Reports endpoint acessível'))
                else:
                    self.stdout.write(self.style.ERROR(f'   ❌ Reports endpoint retornou: {reports_response.status_code}'))
                    
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ Login falhou: {login_response.status_code}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Erro: {str(e)}'))
        
        # 6. Recommendations
        self.stdout.write('\n6️⃣ Recomendações:')
        if settings.DEBUG:
            self.stdout.write('   Para desenvolvimento com frontend em porta diferente:')
            self.stdout.write('   1. Configure JWT_COOKIE_SAMESITE = None')
            self.stdout.write('   2. Ou use um proxy reverso (recomendado)')
            self.stdout.write('   3. Reinicie o servidor após mudanças')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Verificação completa!\n'))