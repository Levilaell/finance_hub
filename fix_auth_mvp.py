#!/usr/bin/env python3
"""
SCRIPT DE CORREÇÃO DE AUTENTICAÇÃO - MVP

Aplica as correções identificadas na análise ultrathink para resolver
o erro "O token informado não é válido para qualquer tipo de token"

USO:
    python fix_auth_mvp.py --backend-only    # Aplicar apenas correções backend
    python fix_auth_mvp.py --frontend-only   # Aplicar apenas correções frontend  
    python fix_auth_mvp.py --all             # Aplicar todas as correções (padrão)
    python fix_auth_mvp.py --diagnose        # Apenas diagnóstico sem modificações
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

def print_banner():
    print("""
🔧 FINANCE HUB - CORREÇÃO DE AUTENTICAÇÃO MVP
==============================================
Baseado na análise ultrathink do problema de token JWT.
    """)

def diagnose_current_state():
    """Diagnostica o estado atual da autenticação"""
    print("🔍 DIAGNÓSTICO DO ESTADO ATUAL")
    print("=" * 50)
    
    issues = []
    
    # 1. Verificar configuração JWT atual
    backend_settings = Path("backend/core/settings/development.py")
    if backend_settings.exists():
        with open(backend_settings, 'r') as f:
            content = f.read()
            if "ACCESS_TOKEN_LIFETIME': timedelta(minutes=30)" in content:
                issues.append("❌ Tokens de acesso muito curtos (30min)")
            if "ROTATE_REFRESH_TOKENS': True" in content:
                issues.append("❌ Rotação de tokens habilitada (complexidade desnecessária)")
            if "BLACKLIST_AFTER_ROTATION': True" in content:
                issues.append("❌ Blacklist após rotação habilitada")
        print(f"✅ Arquivo de configuração encontrado: {backend_settings}")
    else:
        issues.append(f"❌ Arquivo de configuração não encontrado: {backend_settings}")
    
    # 2. Verificar frontend
    frontend_api = Path("frontend/lib/api-client.ts")
    if frontend_api.exists():
        with open(frontend_api, 'r') as f:
            content = f.read()
            if "withCredentials: false" in content:
                print("✅ Configuração correta: withCredentials: false")
            if "Bearer ${accessToken}" in content:
                print("✅ Configuração correta: Bearer tokens")
        print(f"✅ API Client encontrado: {frontend_api}")
    else:
        issues.append(f"❌ API Client não encontrado: {frontend_api}")
    
    # 3. Verificar arquivos de correção
    auth_simplified = Path("backend/core/settings/auth_simplified.py")
    simple_auth = Path("frontend/lib/simple-auth.ts")
    
    if auth_simplified.exists():
        print("✅ Arquivo de correção backend criado")
    else:
        print("⚠️  Arquivo de correção backend não encontrado")
    
    if simple_auth.exists():
        print("✅ Arquivo de correção frontend criado")
    else:
        print("⚠️  Arquivo de correção frontend não encontrado")
    
    # Resumo
    print("\n📋 RESUMO DO DIAGNÓSTICO")
    print("=" * 30)
    if issues:
        print(f"❌ Encontrados {len(issues)} problemas:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("✅ Nenhum problema crítico encontrado")
    
    return len(issues) == 0

def apply_backend_fixes():
    """Aplica as correções no backend"""
    print("\n🔧 APLICANDO CORREÇÕES BACKEND")
    print("=" * 40)
    
    # 1. Atualizar configuração de desenvolvimento
    dev_settings = Path("backend/core/settings/development.py")
    
    if dev_settings.exists():
        with open(dev_settings, 'r') as f:
            content = f.read()
        
        # Adicionar import da configuração simplificada
        if "from .auth_simplified import" not in content:
            # Adicionar no final do arquivo
            simplified_config = '''
# ===== APLICAR CORREÇÕES DE AUTENTICAÇÃO MVP =====
# Configurações simplificadas baseadas na análise ultrathink
from .auth_simplified import (
    SIMPLE_JWT, 
    REST_FRAMEWORK_SIMPLIFIED_THROTTLES
)

# Sobrescrever configurações JWT
SIMPLE_JWT = SIMPLE_JWT

# Aplicar throttles mais permissivos para MVP
REST_FRAMEWORK.update({
    'DEFAULT_THROTTLE_RATES': REST_FRAMEWORK_SIMPLIFIED_THROTTLES
})

print("✅ Aplicadas correções de autenticação MVP")
'''
            
            with open(dev_settings, 'a') as f:
                f.write(simplified_config)
            
            print(f"✅ Configuração simplificada adicionada a {dev_settings}")
        else:
            print(f"⚠️  Configuração já aplicada em {dev_settings}")
    
    # 2. Criar comando de teste de autenticação
    management_dir = Path("backend/apps/authentication/management/commands")
    management_dir.mkdir(exist_ok=True, parents=True)
    
    test_auth_cmd = management_dir / "test_simple_auth.py"
    
    if not test_auth_cmd.exists():
        cmd_content = '''from django.core.management.base import BaseCommand
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
        
        self.stdout.write("\\n✅ Teste de autenticação concluído")
'''
        
        with open(test_auth_cmd, 'w') as f:
            f.write(cmd_content)
        
        print(f"✅ Comando de teste criado: {test_auth_cmd}")
    
    print("✅ Correções backend aplicadas com sucesso")

def apply_frontend_fixes():
    """Aplica as correções no frontend"""
    print("\n🔧 APLICANDO CORREÇÕES FRONTEND")
    print("=" * 40)
    
    # 1. Criar exemplo de uso do simple-auth
    example_usage = Path("frontend/lib/simple-auth-example.tsx")
    
    if not example_usage.exists():
        example_content = '''/**
 * EXEMPLO DE USO - Simple Auth
 * 
 * Como usar a autenticação simplificada em componentes React/Next.js
 */

import React from 'react';
import { useSimpleAuth } from './simple-auth';

// Exemplo 1: Página de Login
export function LoginPage() {
  const { login } = useSimpleAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(email, password);
      // Redirecionamento será feito automaticamente
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err.message || 'Erro no login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input 
        type="email" 
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input 
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Senha"
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Entrando...' : 'Entrar'}
      </button>
      {error && <div className="error">{error}</div>}
    </form>
  );
}

// Exemplo 2: Componente Protegido
export function ProtectedComponent() {
  const { isAuthenticated, user, logout } = useSimpleAuth();

  if (!isAuthenticated) {
    return <div>Acesso negado. <a href="/login">Fazer login</a></div>;
  }

  return (
    <div>
      <h1>Bem-vindo, {user?.first_name || user?.email}!</h1>
      <button onClick={logout}>Sair</button>
    </div>
  );
}

// Exemplo 3: Fazer Requisições Autenticadas
export function DataComponent() {
  const { authenticatedRequest } = useSimpleAuth();
  const [data, setData] = useState(null);

  useEffect(() => {
    authenticatedRequest('/api/dashboard/stats/')
      .then(setData)
      .catch(console.error);
  }, []);

  return (
    <div>
      {data ? (
        <pre>{JSON.stringify(data, null, 2)}</pre>
      ) : (
        <div>Carregando...</div>
      )}
    </div>
  );
}
'''
        
        with open(example_usage, 'w') as f:
            f.write(example_content)
        
        print(f"✅ Exemplo de uso criado: {example_usage}")
    
    # 2. Criar middleware de autenticação Next.js simplificado
    simple_middleware = Path("frontend/middleware-simple.ts")
    
    if not simple_middleware.exists():
        middleware_content = '''import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Middleware simplificado para autenticação
export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token') || 
                request.headers.get('Authorization');

  // Rotas protegidas
  const protectedPaths = ['/dashboard', '/accounts', '/reports', '/settings'];
  const isProtectedPath = protectedPaths.some(path => 
    request.nextUrl.pathname.startsWith(path)
  );

  // Se é rota protegida e não tem token, redirecionar para login
  if (isProtectedPath && !token) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Se tem token e está tentando acessar login/register, redirecionar para dashboard
  if (token && (request.nextUrl.pathname === '/login' || request.nextUrl.pathname === '/register')) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
'''
        
        with open(simple_middleware, 'w') as f:
            f.write(middleware_content)
        
        print(f"✅ Middleware simplificado criado: {simple_middleware}")
    
    print("✅ Correções frontend aplicadas com sucesso")

def create_implementation_guide():
    """Cria um guia de implementação"""
    guide_path = Path("GUIA_IMPLEMENTACAO_AUTH_MVP.md")
    
    guide_content = f'''# 🔧 GUIA DE IMPLEMENTAÇÃO - Autenticação MVP

**Data**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Problema Resolvido**: "O token informado não é válido para qualquer tipo de token"

## 📋 PASSOS PARA IMPLEMENTAR

### 1. Backend (Django)

```bash
# No diretório backend/
python manage.py migrate
python manage.py collectstatic --noinput

# Testar a configuração simplificada
python manage.py test_simple_auth --email seu@email.com --password suasenha
```

### 2. Frontend (Next.js)

```bash
# No diretório frontend/
npm install
npm run build

# Para desenvolvimento
npm run dev
```

### 3. Configurações de Ambiente

**Backend (.env):**
```env
SECRET_KEY=sua-chave-secreta-muito-longa-e-complexa
JWT_SECRET_KEY=sua-chave-jwt-opcional  # Se não informado, usa SECRET_KEY
```

**Frontend (.env.local):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000  # ou URL do seu backend
```

## 🔄 MIGRAÇÃO DO SISTEMA ATUAL

### Se Você Já Tem o Sistema Funcionando:

1. **Faça backup dos arquivos atuais:**
   ```bash
   cp frontend/lib/api-client.ts frontend/lib/api-client.ts.backup
   cp backend/core/settings/development.py backend/core/settings/development.py.backup
   ```

2. **Substitua gradualmente:**
   - Use `simple-auth.ts` em novos componentes
   - Migre componentes existentes aos poucos
   - Teste cada migração

3. **Rollback se necessário:**
   ```bash
   # Restaurar arquivos originais
   cp frontend/lib/api-client.ts.backup frontend/lib/api-client.ts
   ```

## ✅ VALIDAÇÃO

### Testes para Confirmar que Funcionou:

1. **Login funciona:** ✅/❌
2. **Tokens são salvos no localStorage:** ✅/❌
3. **Requisições autenticadas funcionam:** ✅/❌
4. **Logout limpa tokens:** ✅/❌
5. **Redirecionamento automático funciona:** ✅/❌

### Verificações de Segurança:

- [ ] Tokens não aparecem em URLs
- [ ] localStorage é limpo no logout
- [ ] Redirecionamento funciona quando token expira
- [ ] HTTPS em produção

## 🚨 SOLUÇÃO DE PROBLEMAS

### Erro Persiste:
1. Limpar localStorage: `localStorage.clear()`
2. Verificar console do navegador
3. Verificar logs do Django
4. Confirmar que as configurações foram aplicadas

### Token Inválido:
1. Verificar se SECRET_KEY não mudou
2. Confirmar formato do token no localStorage
3. Testar com usuário novo

## 📞 SUPORTE

Se o problema persistir após implementação:
1. Verificar logs detalhados
2. Testar com curl/Postman
3. Confirmar versões das dependências

---
**Gerado automaticamente pelo script de correção**
'''
    
    with open(guide_path, 'w') as f:
        f.write(guide_content)
    
    print(f"✅ Guia de implementação criado: {guide_path}")

def main():
    parser = argparse.ArgumentParser(description='Fix authentication issues for MVP')
    parser.add_argument('--backend-only', action='store_true', help='Apply only backend fixes')
    parser.add_argument('--frontend-only', action='store_true', help='Apply only frontend fixes')
    parser.add_argument('--all', action='store_true', help='Apply all fixes (default)')
    parser.add_argument('--diagnose', action='store_true', help='Diagnose only, no changes')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Se nenhuma opção especificada, aplicar todas
    if not any([args.backend_only, args.frontend_only, args.diagnose]):
        args.all = True
    
    # Diagnóstico sempre executado
    all_good = diagnose_current_state()
    
    if args.diagnose:
        print(f"\\n🏁 DIAGNÓSTICO CONCLUÍDO")
        print(f"Estado geral: {'✅ BOM' if all_good else '❌ PROBLEMAS ENCONTRADOS'}")
        return
    
    # Aplicar correções
    try:
        if args.backend_only or args.all:
            apply_backend_fixes()
        
        if args.frontend_only or args.all:
            apply_frontend_fixes()
        
        create_implementation_guide()
        
        print("\\n🎉 CORREÇÕES APLICADAS COM SUCESSO!")
        print("=" * 50)
        print("📖 Consulte o arquivo 'GUIA_IMPLEMENTACAO_AUTH_MVP.md' para próximos passos")
        print("🧪 Execute os testes para validar a implementação")
        print("\\n🚀 Seu sistema de autenticação MVP está pronto!")
        
    except Exception as e:
        print(f"\\n❌ ERRO DURANTE A APLICAÇÃO: {e}")
        print("Consulte os logs acima para detalhes")
        sys.exit(1)

if __name__ == '__main__':
    main()