#!/usr/bin/env python3
"""
Script de Validação - Migração Early Access
==========================================

Este script valida se a migração 0009_add_early_access foi aplicada corretamente
em produção e se todos os campos e modelos estão funcionando.

Uso:
    python validate_early_access_migration.py

Em produção via Railway:
    railway run python validate_early_access_migration.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from apps.companies.models import Company, EarlyAccessInvite
from django.contrib.auth import get_user_model

User = get_user_model()

def check_database_schema():
    """Verificar se as colunas existem no banco de dados"""
    print("🔍 Verificando schema do banco de dados...")
    
    with connection.cursor() as cursor:
        # Verificar colunas da tabela companies
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'companies' 
            AND column_name IN ('is_early_access', 'early_access_expires_at', 'used_invite_code')
            ORDER BY column_name;
        """)
        
        columns = cursor.fetchall()
        
        expected_columns = {
            'is_early_access': 'boolean',
            'early_access_expires_at': 'timestamp with time zone',
            'used_invite_code': 'character varying'
        }
        
        found_columns = {col[0]: col[1] for col in columns}
        
        print(f"   Colunas encontradas: {len(found_columns)}/3")
        
        for col_name, expected_type in expected_columns.items():
            if col_name in found_columns:
                print(f"   ✅ {col_name}: {found_columns[col_name]}")
            else:
                print(f"   ❌ {col_name}: NÃO ENCONTRADA")
                return False
        
        # Verificar tabela early_access_invites
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'early_access_invites';
        """)
        
        invite_table = cursor.fetchone()
        if invite_table:
            print(f"   ✅ Tabela early_access_invites: EXISTE")
        else:
            print(f"   ❌ Tabela early_access_invites: NÃO ENCONTRADA")
            return False
    
    return True

def check_django_models():
    """Verificar se os modelos Django estão funcionando"""
    print("\n🔍 Verificando modelos Django...")
    
    try:
        # Verificar campos no modelo Company
        company_fields = [field.name for field in Company._meta.fields]
        required_fields = ['is_early_access', 'early_access_expires_at', 'used_invite_code']
        
        for field in required_fields:
            if field in company_fields:
                print(f"   ✅ Company.{field}: EXISTE")
            else:
                print(f"   ❌ Company.{field}: NÃO ENCONTRADO")
                return False
        
        # Verificar modelo EarlyAccessInvite
        try:
            EarlyAccessInvite._meta.get_field('invite_code')
            print(f"   ✅ EarlyAccessInvite modelo: FUNCIONAL")
        except:
            print(f"   ❌ EarlyAccessInvite modelo: ERRO")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro ao verificar modelos: {e}")
        return False
    
    return True

def check_migration_status():
    """Verificar se a migração foi aplicada"""
    print("\n🔍 Verificando status da migração...")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name, applied 
            FROM django_migrations 
            WHERE app = 'companies' AND name = '0009_add_early_access';
        """)
        
        migration = cursor.fetchone()
        
        if migration:
            print(f"   ✅ Migração 0009_add_early_access: APLICADA em {migration[1]}")
            return True
        else:
            print(f"   ❌ Migração 0009_add_early_access: NÃO APLICADA")
            return False

def test_model_functionality():
    """Testar funcionalidade dos modelos"""
    print("\n🔍 Testando funcionalidade dos modelos...")
    
    try:
        # Teste 1: Criar empresa com early access
        print("   Teste 1: Criar empresa com early access...")
        company_count = Company.objects.count()
        
        # Não vamos salvar, apenas validar que o modelo aceita os campos
        from django.utils import timezone
        from datetime import timedelta
        
        company = Company(
            name="Test Company",
            trade_name="Test",
            is_early_access=True,
            early_access_expires_at=timezone.now() + timedelta(days=30),
            used_invite_code="TEST123"
        )
        
        # Validar campos sem salvar
        if hasattr(company, 'is_early_access') and hasattr(company, 'early_access_expires_at'):
            print(f"      ✅ Campos early access funcionam")
        else:
            print(f"      ❌ Campos early access não funcionam")
            return False
        
        # Teste 2: Testar propriedades
        print("   Teste 2: Testar propriedades do modelo...")
        if hasattr(company, 'is_early_access_active'):
            result = company.is_early_access_active
            print(f"      ✅ Propriedade is_early_access_active: {result}")
        else:
            print(f"      ❌ Propriedade is_early_access_active não existe")
            return False
        
        # Teste 3: Verificar choices do subscription_status
        print("   Teste 3: Verificar choices de subscription_status...")
        choices = dict(Company._meta.get_field('subscription_status').choices)
        if 'early_access' in choices:
            print(f"      ✅ Choice 'early_access': {choices['early_access']}")
        else:
            print(f"      ❌ Choice 'early_access' não encontrada")
            return False
        
    except Exception as e:
        print(f"   ❌ Erro ao testar funcionalidade: {e}")
        return False
    
    return True

def create_test_invite():
    """Criar um convite de teste (se não existe admin)"""
    print("\n🔍 Testando criação de convite early access...")
    
    try:
        # Verificar se existe algum usuário admin
        admin_user = User.objects.filter(is_superuser=True).first()
        
        if not admin_user:
            print("   ⚠️  Nenhum usuário admin encontrado - pulando teste de criação")
            return True
        
        # Verificar se já existe convite de teste
        test_invite = EarlyAccessInvite.objects.filter(invite_code='VALIDATION_TEST').first()
        
        if test_invite:
            print(f"   ✅ Convite de teste já existe: {test_invite}")
            return True
        
        # Criar convite de teste
        from django.utils import timezone
        from datetime import timedelta
        
        invite = EarlyAccessInvite.objects.create(
            invite_code='VALIDATION_TEST',
            expires_at=timezone.now() + timedelta(days=30),
            created_by=admin_user,
            notes='Convite criado durante validação da migração'
        )
        
        print(f"   ✅ Convite de teste criado: {invite}")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao criar convite de teste: {e}")
        return False

def main():
    """Função principal de validação"""
    print("🚀 Iniciando validação da migração Early Access...")
    print("=" * 60)
    
    all_tests_passed = True
    
    # 1. Verificar schema do banco
    if not check_database_schema():
        all_tests_passed = False
    
    # 2. Verificar modelos Django
    if not check_django_models():
        all_tests_passed = False
    
    # 3. Verificar status da migração
    if not check_migration_status():
        all_tests_passed = False
    
    # 4. Testar funcionalidade
    if not test_model_functionality():
        all_tests_passed = False
    
    # 5. Testar criação de convite
    if not create_test_invite():
        all_tests_passed = False
    
    print("\n" + "=" * 60)
    
    if all_tests_passed:
        print("🎉 VALIDAÇÃO COMPLETA: Migração aplicada com sucesso!")
        print("✅ Todos os testes passaram")
        print("✅ Sistema de Early Access está funcionando")
        print("✅ Registro de usuários deve funcionar agora")
        sys.exit(0)
    else:
        print("❌ VALIDAÇÃO FALHOU: Problemas encontrados")
        print("🚨 Migração precisa ser aplicada ou corrigida")
        print("🚨 Sistema de registro pode ainda estar quebrado")
        sys.exit(1)

if __name__ == "__main__":
    main()