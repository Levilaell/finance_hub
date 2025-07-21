#!/usr/bin/env python
"""
Script para debug do erro de registro em produção
"""
import requests
import json

# URLs para teste
PROD_URL = "https://finance-backend-production-29df.up.railway.app/api/auth/register/"
DEBUG_URL = "https://finance-backend-production-29df.up.railway.app/api/auth/register/debug/"

def test_registration():
    """Testa o registro com dados válidos"""
    
    test_data = {
        "email": "teste@example.com",
        "password": "SenhaForte123!",
        "password2": "SenhaForte123!",
        "first_name": "João",
        "last_name": "Silva",
        "phone": "(11) 98765-4321",
        "company_name": "Empresa Teste Ltda",
        "company_cnpj": "11.222.333/0001-81",
        "company_type": "ltda",
        "business_sector": "tecnologia"
    }
    
    print("=== TESTE DE DEBUG DO REGISTRO ===\n")
    
    # Primeiro teste com endpoint de debug
    print("1. Testando endpoint de debug:")
    try:
        response = requests.post(DEBUG_URL, json=test_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Erro no debug: {str(e)}")
    
    print("\n" + "-"*50 + "\n")
    
    # Segundo teste com endpoint real
    print("2. Testando endpoint real de registro:")
    try:
        response = requests.post(PROD_URL, json=test_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Erro no registro: {str(e)}")
    
    print("\n" + "-"*50 + "\n")
    
    # Teste com dados mínimos
    print("3. Testando com dados mínimos:")
    minimal_data = {
        "email": "minimal@test.com",
        "password": "Test123!",
        "password2": "Test123!",
    }
    
    try:
        response = requests.post(DEBUG_URL, json=minimal_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Erro: {str(e)}")

if __name__ == "__main__":
    test_registration()