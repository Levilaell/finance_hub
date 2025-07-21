#!/usr/bin/env python
"""
Script de teste para validar as mensagens de erro personalizadas no registro
"""
import requests
import json

# URL da API (ajuste conforme necessário)
BASE_URL = "http://localhost:8000/api/auth/register/"

def test_registration_validation():
    """Testa diferentes cenários de validação"""
    
    print("=== TESTE DE VALIDAÇÕES DE REGISTRO ===\n")
    
    # Teste 1: Campos obrigatórios vazios
    print("1. Testando campos obrigatórios vazios:")
    response = requests.post(BASE_URL, json={})
    if response.status_code == 400:
        errors = response.json()
        print(json.dumps(errors, indent=2, ensure_ascii=False))
    print("\n" + "-"*50 + "\n")
    
    # Teste 2: Email inválido
    print("2. Testando email inválido:")
    response = requests.post(BASE_URL, json={
        "email": "email_invalido",
        "password": "senha123",
        "password2": "senha123",
        "first_name": "João",
        "last_name": "Silva",
        "phone": "11999999999",
        "company_name": "Empresa Teste",
        "company_cnpj": "11222333000181",
        "company_type": "ltda",
        "business_sector": "tecnologia"
    })
    if response.status_code == 400:
        errors = response.json()
        print(json.dumps(errors, indent=2, ensure_ascii=False))
    print("\n" + "-"*50 + "\n")
    
    # Teste 3: Senhas não coincidem
    print("3. Testando senhas que não coincidem:")
    response = requests.post(BASE_URL, json={
        "email": "teste@example.com",
        "password": "senha123",
        "password2": "senha456",
        "first_name": "João",
        "last_name": "Silva",
        "phone": "11999999999",
        "company_name": "Empresa Teste",
        "company_cnpj": "11222333000181",
        "company_type": "ltda",
        "business_sector": "tecnologia"
    })
    if response.status_code == 400:
        errors = response.json()
        print(json.dumps(errors, indent=2, ensure_ascii=False))
    print("\n" + "-"*50 + "\n")
    
    # Teste 4: Senha fraca
    print("4. Testando senha fraca (apenas números):")
    response = requests.post(BASE_URL, json={
        "email": "teste@example.com",
        "password": "12345678",
        "password2": "12345678",
        "first_name": "João",
        "last_name": "Silva",
        "phone": "11999999999",
        "company_name": "Empresa Teste",
        "company_cnpj": "11222333000181",
        "company_type": "ltda",
        "business_sector": "tecnologia"
    })
    if response.status_code == 400:
        errors = response.json()
        print(json.dumps(errors, indent=2, ensure_ascii=False))
    print("\n" + "-"*50 + "\n")
    
    # Teste 5: CNPJ inválido
    print("5. Testando CNPJ inválido:")
    response = requests.post(BASE_URL, json={
        "email": "teste@example.com",
        "password": "SenhaForte123!",
        "password2": "SenhaForte123!",
        "first_name": "João",
        "last_name": "Silva",
        "phone": "11999999999",
        "company_name": "Empresa Teste",
        "company_cnpj": "11111111111111",
        "company_type": "ltda",
        "business_sector": "tecnologia"
    })
    if response.status_code == 400:
        errors = response.json()
        print(json.dumps(errors, indent=2, ensure_ascii=False))
    print("\n" + "-"*50 + "\n")
    
    # Teste 6: Telefone inválido
    print("6. Testando telefone inválido:")
    response = requests.post(BASE_URL, json={
        "email": "teste@example.com",
        "password": "SenhaForte123!",
        "password2": "SenhaForte123!",
        "first_name": "João",
        "last_name": "Silva",
        "phone": "123",
        "company_name": "Empresa Teste",
        "company_cnpj": "11222333000181",
        "company_type": "ltda",
        "business_sector": "tecnologia"
    })
    if response.status_code == 400:
        errors = response.json()
        print(json.dumps(errors, indent=2, ensure_ascii=False))
    print("\n" + "-"*50 + "\n")
    
    # Teste 7: Nome inválido
    print("7. Testando nome inválido (números):")
    response = requests.post(BASE_URL, json={
        "email": "teste@example.com",
        "password": "SenhaForte123!",
        "password2": "SenhaForte123!",
        "first_name": "João123",
        "last_name": "Silva456",
        "phone": "11999999999",
        "company_name": "Empresa Teste",
        "company_cnpj": "11222333000181",
        "company_type": "ltda",
        "business_sector": "tecnologia"
    })
    if response.status_code == 400:
        errors = response.json()
        print(json.dumps(errors, indent=2, ensure_ascii=False))
    print("\n" + "-"*50 + "\n")
    
    # Teste 8: Email já cadastrado (se houver algum no banco)
    print("8. Testando email já cadastrado:")
    # Primeiro tenta criar um usuário
    response = requests.post(BASE_URL, json={
        "email": "usuario_teste@example.com",
        "password": "SenhaForte123!",
        "password2": "SenhaForte123!",
        "first_name": "João",
        "last_name": "Silva",
        "phone": "11999999999",
        "company_name": "Empresa Teste",
        "company_cnpj": "11222333000181",
        "company_type": "ltda",
        "business_sector": "tecnologia"
    })
    
    # Tenta criar novamente com o mesmo email
    response = requests.post(BASE_URL, json={
        "email": "usuario_teste@example.com",
        "password": "OutraSenha456!",
        "password2": "OutraSenha456!",
        "first_name": "Maria",
        "last_name": "Santos",
        "phone": "21988888888",
        "company_name": "Outra Empresa",
        "company_cnpj": "22333444000195",
        "company_type": "ltda",
        "business_sector": "comercio"
    })
    if response.status_code == 400:
        errors = response.json()
        print(json.dumps(errors, indent=2, ensure_ascii=False))
    print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    test_registration_validation()