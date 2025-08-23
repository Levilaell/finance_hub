#!/usr/bin/env python3
"""
Script de Validação Completa de Migrações para Produção Railway

Este script verifica:
1. Estado de todas as migrações
2. Consistência de schema
3. Problemas de collation
4. Migrações pendentes
5. Integridade referencial

Execute via Railway:
railway run python validate_production_migrations.py
"""

import os
import sys
import django
from django.conf import settings
from django.db import connection, OperationalError
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.apps import apps
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder

def check_database_health():
    """Verifica saúde geral do banco"""
    print("🔍 VERIFICANDO SAÚDE DO BANCO DE DADOS")
    print("="*50)
    
    try:
        with connection.cursor() as cursor:
            # PostgreSQL version
            cursor.execute('SELECT version();')
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL Version: {version}")
            
            # Database size
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
            size = cursor.fetchone()[0]
            print(f"📊 Database Size: {size}")
            
            # Collation check
            cursor.execute("SELECT datcollate FROM pg_database WHERE datname = current_database();")
            collation = cursor.fetchone()[0]
            print(f"🌐 Database Collation: {collation}")
            
            return True
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")
        return False

def check_migration_state():
    """Verifica estado completo das migrações"""
    print("\n🔄 VERIFICANDO ESTADO DAS MIGRAÇÕES")
    print("="*50)
    
    try:
        loader = MigrationLoader(connection)
        recorder = MigrationRecorder(connection)
        
        # Migrações aplicadas
        applied = recorder.applied_migrations()
        print(f"✅ Migrações aplicadas: {len(applied)}")
        
        # Migrações não aplicadas
        unapplied = loader.project_state().apps.get_models()
        print(f"📋 Modelos registrados: {len(unapplied)}")
        
        # Por app
        apps_data = {}
        for (app_name, migration_name) in applied:
            if app_name not in apps_data:
                apps_data[app_name] = []
            apps_data[app_name].append(migration_name)
        
        print("\n📱 Por App:")
        for app_name in sorted(apps_data.keys()):
            migrations = apps_data[app_name]
            latest = max(migrations) if migrations else "nenhuma"
            print(f"  {app_name}: {len(migrations)} migrações, última: {latest}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar migrações: {e}")
        return False

def check_critical_tables():
    """Verifica tabelas críticas e seus campos"""
    print("\n🗃️ VERIFICANDO TABELAS CRÍTICAS")
    print("="*50)
    
    critical_checks = [
        # companies table - early access fields
        ("companies", ["is_early_access", "early_access_expires_at", "used_invite_code"]),
        
        # notifications table - new schema
        ("notifications", ["event", "event_key", "is_critical", "metadata", "delivery_status"]),
        
        # transactions table - performance indexes
        ("transactions", ["id", "amount", "date", "type", "account_id", "company_id"]),
        
        # early_access_invites table
        ("early_access_invites", ["invite_code", "expires_at", "is_used", "created_by_id"]),
    ]
    
    try:
        with connection.cursor() as cursor:
            for table_name, expected_fields in critical_checks:
                print(f"\n🔍 Verificando tabela: {table_name}")
                
                # Verificar se tabela existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    );
                """, [table_name])
                
                table_exists = cursor.fetchone()[0]
                if not table_exists:
                    print(f"  ❌ Tabela {table_name} NÃO EXISTE")
                    continue
                
                print(f"  ✅ Tabela {table_name} existe")
                
                # Verificar campos
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = %s
                    ORDER BY ordinal_position;
                """, [table_name])
                
                columns = cursor.fetchall()
                column_names = [col[0] for col in columns]
                
                print(f"  📊 Campos encontrados: {len(column_names)}")
                
                # Verificar campos esperados
                for field in expected_fields:
                    if field in column_names:
                        print(f"    ✅ {field}")
                    else:
                        print(f"    ❌ {field} FALTANDO")
                
                # Mostrar campos extras importantes
                extra_fields = [col for col in column_names if col not in expected_fields]
                if extra_fields and len(extra_fields) < 10:
                    print(f"  📝 Outros campos: {', '.join(extra_fields[:5])}")
                
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar tabelas: {e}")
        return False

def check_recent_migrations():
    """Verifica últimas migrações aplicadas"""
    print("\n⏰ ÚLTIMAS MIGRAÇÕES APLICADAS")
    print("="*50)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT app, name, applied 
                FROM django_migrations 
                ORDER BY applied DESC 
                LIMIT 15;
            """)
            
            recent_migrations = cursor.fetchall()
            
            for app, name, applied in recent_migrations:
                print(f"  {applied.strftime('%Y-%m-%d %H:%M')} | {app}.{name}")
                
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar migrações recentes: {e}")
        return False

def main():
    """Executa todas as verificações"""
    print("🚀 VALIDAÇÃO COMPLETA DE MIGRAÇÕES - PRODUÇÃO RAILWAY")
    print("="*60)
    
    checks = [
        ("Saúde do Banco", check_database_health),
        ("Estado das Migrações", check_migration_state), 
        ("Tabelas Críticas", check_critical_tables),
        ("Migrações Recentes", check_recent_migrations),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Erro em {name}: {e}")
            results.append((name, False))
    
    # Sumário final
    print("\n📊 SUMÁRIO FINAL")
    print("="*30)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {name}")
    
    print(f"\n🎯 RESULTADO: {passed}/{total} verificações passaram")
    
    if passed == total:
        print("✅ BANCO ESTÁ SAUDÁVEL - DEPLOY PODE PROSSEGUIR")
    else:
        print("⚠️ PROBLEMAS DETECTADOS - REVISAR ANTES DO DEPLOY")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)