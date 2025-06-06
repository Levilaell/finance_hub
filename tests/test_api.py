#!/usr/bin/env python3
"""
Script de teste para a API Caixa Digital
"""
import requests
import json
from datetime import datetime

# Base URL
BASE_URL = "http://127.0.0.1:8000/api"

# Cores para output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
END = '\033[0m'

def print_test(name, success, response=None):
    status = f"{GREEN}✓ PASSOU{END}" if success else f"{RED}✗ FALHOU{END}"
    print(f"\n{status} - {name}")
    if response and not success:
        print(f"   Erro: {response}")

def test_health():
    """Testa endpoint de health"""
    try:
        r = requests.get(f"{BASE_URL}/auth/health/")
        print_test("Health Check", r.status_code == 200, r.text)
        return r.status_code == 200
    except Exception as e:
        print_test("Health Check", False, str(e))
        return False

def test_register():
    """Testa registro de usuário"""
    data = {
        "email": f"teste_{datetime.now().timestamp()}@example.com",
        "password": "SenhaForte123!",
        "password2": "SenhaForte123!",
        "first_name": "Teste",
        "last_name": "Usuario",
        "phone": "11999999999",
        "company_name": "Empresa Teste",
        "company_type": "mei",
        "business_sector": "services"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/auth/register/", json=data)
        success = r.status_code == 201
        print_test("Registro de Usuário", success, r.text if not success else None)
        if success:
            return r.json()
        return None
    except Exception as e:
        print_test("Registro de Usuário", False, str(e))
        return None

def test_login(email="test@example.com", password="test123"):
    """Testa login"""
    data = {
        "email": email,
        "password": password
    }
    
    try:
        r = requests.post(f"{BASE_URL}/auth/login/", json=data)
        success = r.status_code == 200
        print_test("Login", success, r.text if not success else None)
        if success:
            return r.json()
        return None
    except Exception as e:
        print_test("Login", False, str(e))
        return None

def test_authenticated_endpoints(token):
    """Testa endpoints autenticados"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Profile
    try:
        r = requests.get(f"{BASE_URL}/auth/profile/", headers=headers)
        print_test("Perfil do Usuário", r.status_code == 200, r.text if r.status_code != 200 else None)
    except Exception as e:
        print_test("Perfil do Usuário", False, str(e))
    
    # Categories
    try:
        r = requests.get(f"{BASE_URL}/categories/", headers=headers)
        print_test("Listar Categorias", r.status_code == 200, r.text if r.status_code != 200 else None)
        if r.status_code == 200:
            categories = r.json()
            print(f"   {BLUE}Encontradas {len(categories)} categorias{END}")
    except Exception as e:
        print_test("Listar Categorias", False, str(e))
    
    # Bank Accounts
    try:
        r = requests.get(f"{BASE_URL}/banking/accounts/", headers=headers)
        print_test("Listar Contas Bancárias", r.status_code == 200, r.text if r.status_code != 200 else None)
    except Exception as e:
        print_test("Listar Contas Bancárias", False, str(e))
    
    # Transactions
    try:
        r = requests.get(f"{BASE_URL}/banking/transactions/", headers=headers)
        print_test("Listar Transações", r.status_code == 200, r.text if r.status_code != 200 else None)
    except Exception as e:
        print_test("Listar Transações", False, str(e))
    
    # Reports
    try:
        r = requests.get(f"{BASE_URL}/reports/cashflow/", headers=headers)
        print_test("Relatório de Fluxo de Caixa", r.status_code == 200, r.text if r.status_code != 200 else None)
    except Exception as e:
        print_test("Relatório de Fluxo de Caixa", False, str(e))
    
    # Notifications
    try:
        r = requests.get(f"{BASE_URL}/notifications/count/", headers=headers)
        print_test("Contagem de Notificações", r.status_code == 200, r.text if r.status_code != 200 else None)
    except Exception as e:
        print_test("Contagem de Notificações", False, str(e))

def test_websocket_health():
    """Testa health do WebSocket"""
    try:
        r = requests.get(f"{BASE_URL}/notifications/websocket/health/")
        print_test("WebSocket Health", r.status_code == 200, r.text if r.status_code != 200 else None)
    except Exception as e:
        print_test("WebSocket Health", False, str(e))

def main():
    print(f"\n{YELLOW}=== TESTE DA API CAIXA DIGITAL ==={END}")
    print(f"Base URL: {BASE_URL}\n")
    
    # 1. Health check
    if not test_health():
        print(f"\n{RED}Servidor não está respondendo. Verifique se está rodando.{END}")
        return
    
    # 2. WebSocket health
    test_websocket_health()
    
    # 3. Registro (opcional)
    print(f"\n{BLUE}--- Teste de Autenticação ---{END}")
    # user_data = test_register()
    
    # 4. Login
    login_data = test_login()
    if not login_data:
        print(f"\n{RED}Falha no login. Verifique as credenciais.{END}")
        return
    
    tokens = login_data.get('tokens', {})
    access_token = tokens.get('access')
    if not access_token:
        print(f"   {RED}Token não encontrado na resposta{END}")
        return
    print(f"   {GREEN}Token obtido com sucesso{END}")
    
    # 5. Endpoints autenticados
    print(f"\n{BLUE}--- Teste de Endpoints Autenticados ---{END}")
    test_authenticated_endpoints(access_token)
    
    print(f"\n{GREEN}=== TESTES CONCLUÍDOS ==={END}\n")

if __name__ == "__main__":
    main()