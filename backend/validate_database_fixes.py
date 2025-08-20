#!/usr/bin/env python3
"""
Validação das correções de inconsistências do banco de dados
Finance Hub - Django Database Schema Validation
"""

import os
import sys
import django
from django.db import connection
from django.core.management.color import make_style

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

# Importar modelos após setup do Django
from apps.authentication.models import User, EmailVerification, PasswordReset
from apps.companies.models import Company, SubscriptionPlan
from apps.banking.models import Transaction, BankAccount
from django.contrib.auth import get_user_model

style = make_style()

def print_status(message, status='OK'):
    """Imprimir status com cores"""
    if status == 'OK':
        print(f"✅ {style.SUCCESS(message)}")
    elif status == 'ERROR':
        print(f"❌ {style.ERROR(message)}")
    elif status == 'WARNING':
        print(f"⚠️  {style.WARNING(message)}")
    elif status == 'INFO':
        print(f"ℹ️  {style.HTTP_INFO(message)}")

def check_table_exists(table_name):
    """Verificar se uma tabela existe no banco"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, [table_name])
        return cursor.fetchone()[0]

def check_model_functionality():
    """Testar funcionalidades básicas dos modelos"""
    try:
        # Teste 1: EmailVerification deve funcionar
        print_status("Testando modelo EmailVerification...", 'INFO')
        
        # Tentar criar um EmailVerification (deve funcionar)
        test_user = User.objects.first()
        if test_user:
            # Criar uma verificação de teste
            verification = EmailVerification(
                user=test_user,
                token='test_token_123',
                expires_at=django.utils.timezone.now() + django.utils.timezone.timedelta(days=1)
            )
            # Não salvar, apenas validar que o objeto pode ser criado
            print_status("EmailVerification pode ser instanciado", 'OK')
        else:
            print_status("Nenhum usuário encontrado para teste", 'WARNING')
            
        # Teste 2: Queries básicas
        verification_count = EmailVerification.objects.count()
        print_status(f"EmailVerification.objects.count() = {verification_count}", 'OK')
        
        # Teste 3: Related queries (user.email_verifications)
        if test_user:
            related_count = test_user.email_verifications.count()
            print_status(f"user.email_verifications.count() = {related_count}", 'OK')
            
        return True
        
    except Exception as e:
        print_status(f"Erro ao testar EmailVerification: {e}", 'ERROR')
        return False

def check_database_schema():
    """Verificar schema do banco de dados"""
    print_status("=== VERIFICAÇÃO DO SCHEMA DO BANCO ===", 'INFO')
    
    critical_tables = [
        'users', 'companies', 'email_verifications', 'password_resets',
        'transactions', 'bank_accounts', 'subscriptions'
    ]
    
    missing_tables = []
    
    for table in critical_tables:
        if check_table_exists(table):
            print_status(f"Tabela '{table}' existe", 'OK')
        else:
            print_status(f"Tabela '{table}' NÃO EXISTE", 'ERROR')
            missing_tables.append(table)
    
    return len(missing_tables) == 0

def check_migrations_status():
    """Verificar status das migrações"""
    print_status("=== VERIFICAÇÃO DE MIGRAÇÕES ===", 'INFO')
    
    with connection.cursor() as cursor:
        # Verificar se a migração EmailVerification foi aplicada
        cursor.execute("""
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = 'authentication' AND name = '0003_emailverification'
        """)
        migration_applied = cursor.fetchone()[0] > 0
        
        if migration_applied:
            print_status("Migração 0003_emailverification aplicada", 'OK')
        else:
            print_status("Migração 0003_emailverification NÃO aplicada", 'ERROR')
            
        return migration_applied

def check_admin_functionality():
    """Testar se o admin funciona sem erros"""
    print_status("=== VERIFICAÇÃO DO ADMIN ===", 'INFO')
    
    try:
        # Simular query que o admin faz
        from django.contrib.admin.sites import site
        from apps.authentication.models import User
        
        # Tentar obter queryset do UserAdmin
        users_qs = User.objects.select_related('company', 'company__subscription_plan')
        user_count = users_qs.count()
        print_status(f"Admin pode listar {user_count} usuários", 'OK')
        
        # Testar se pode acessar related fields
        for user in users_qs[:3]:  # Testar apenas primeiros 3
            try:
                # Estas são as queries que causavam erro no admin
                verifications = user.email_verifications.count()
                print_status(f"User {user.email}: {verifications} verificações", 'OK')
            except Exception as e:
                print_status(f"Erro ao acessar user.email_verifications: {e}", 'ERROR')
                return False
                
        return True
        
    except Exception as e:
        print_status(f"Erro ao testar admin: {e}", 'ERROR')
        return False

def check_register_functionality():
    """Verificar se o registro de usuários funcionaria"""
    print_status("=== VERIFICAÇÃO DE REGISTRO ===", 'INFO')
    
    try:
        # Simular o que acontece no RegisterView
        from django.utils import timezone
        from datetime import timedelta
        import secrets
        
        # Criar um usuário de teste (sem salvar)
        test_user = User(
            username='test_user_validation',
            email='test@validation.com',
            first_name='Test',
            last_name='User'
        )
        
        # Simular criação de EmailVerification (sem salvar)
        verification_token = secrets.token_urlsafe(32)
        verification = EmailVerification(
            user=test_user,
            token=verification_token,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        print_status("Simulação de registro bem-sucedida", 'OK')
        return True
        
    except Exception as e:
        print_status(f"Erro na simulação de registro: {e}", 'ERROR')
        return False

def main():
    """Função principal de validação"""
    print(style.HTTP_INFO("=" * 60))
    print(style.HTTP_INFO("VALIDAÇÃO DAS CORREÇÕES DO BANCO DE DADOS"))
    print(style.HTTP_INFO("Finance Hub - Database Schema Validation"))
    print(style.HTTP_INFO("=" * 60))
    print()
    
    all_good = True
    
    # 1. Verificar schema
    if not check_database_schema():
        all_good = False
    print()
    
    # 2. Verificar migrações
    if not check_migrations_status():
        all_good = False
    print()
    
    # 3. Verificar funcionalidade dos modelos
    if not check_model_functionality():
        all_good = False
    print()
    
    # 4. Verificar admin
    if not check_admin_functionality():
        all_good = False
    print()
    
    # 5. Verificar registro
    if not check_register_functionality():
        all_good = False
    print()
    
    # Resultado final
    print(style.HTTP_INFO("=" * 60))
    if all_good:
        print_status("🎉 TODAS AS VALIDAÇÕES PASSARAM!", 'OK')
        print_status("O banco de dados está consistente e funcionando", 'OK')
    else:
        print_status("❌ ALGUMAS VALIDAÇÕES FALHARAM", 'ERROR')
        print_status("Verifique os erros acima e aplique as correções necessárias", 'ERROR')
    print(style.HTTP_INFO("=" * 60))
    
    return 0 if all_good else 1

if __name__ == '__main__':
    sys.exit(main())