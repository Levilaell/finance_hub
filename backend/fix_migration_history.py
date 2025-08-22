#!/usr/bin/env python
"""
Script para corrigir histórico inconsistente de migrações em produção
Criado para resolver: Migration companies.0009_add_early_access is applied before its dependency companies.0008_alter_resourceusage_options_and_more
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.db import connection, transaction
from django.db.migrations.recorder import MigrationRecorder
from django.core.management import execute_from_command_line

def fix_migration_history():
    """Corrige o histórico inconsistente de migrações"""
    
    print("🔧 [MIGRATION-FIX] Iniciando correção do histórico de migrações...")
    
    try:
        with transaction.atomic():
            recorder = MigrationRecorder(connection)
            
            # Verificar migrações aplicadas
            applied_migrations = set(recorder.applied_migrations())
            
            print(f"📋 [MIGRATION-FIX] Migrações aplicadas atualmente: {len(applied_migrations)}")
            
            # Verificar se o problema existe
            companies_0008 = ('companies', '0008_alter_resourceusage_options_and_more')
            companies_0009 = ('companies', '0009_add_early_access')
            
            if companies_0009 in applied_migrations and companies_0008 not in applied_migrations:
                print("⚠️  [MIGRATION-FIX] Problema detectado: 0009 aplicada mas 0008 não está no histórico")
                
                # Verificar se a estrutura da 0008 já existe
                with connection.cursor() as cursor:
                    # Verificar se as colunas/mudanças da 0008 já existem
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'companies_resourceusage'
                    """)
                    columns = [row[0] for row in cursor.fetchall()]
                    
                    has_created_at = 'created_at' in columns
                    has_updated_at = 'updated_at' in columns
                    
                    print(f"📊 [MIGRATION-FIX] ResourceUsage tem created_at: {has_created_at}")
                    print(f"📊 [MIGRATION-FIX] ResourceUsage tem updated_at: {has_updated_at}")
                    
                    if has_created_at and has_updated_at:
                        # A estrutura já existe, podemos marcar como aplicada
                        recorder.record_applied(companies_0008[0], companies_0008[1])
                        print("✅ [MIGRATION-FIX] Migração 0008 marcada como aplicada no histórico")
                        
                        # Verificar outras migrações pendentes que podem ter dependências similares
                        other_pending = [
                            ('banking', '0010_add_encrypted_parameter'),
                            ('notifications', '0002_add_event_key'),
                            ('notifications', '0003_cleanup_old_fields'),
                        ]
                        
                        for app, migration in other_pending:
                            migration_tuple = (app, migration)
                            if migration_tuple not in applied_migrations:
                                # Verificar se a estrutura já existe para essas migrações também
                                if app == 'banking' and migration == '0010_add_encrypted_parameter':
                                    cursor.execute("""
                                        SELECT column_name 
                                        FROM information_schema.columns 
                                        WHERE table_name = 'banking_pluggyitem' AND column_name = 'encrypted_parameter'
                                    """)
                                    if cursor.fetchone():
                                        recorder.record_applied(app, migration)
                                        print(f"✅ [MIGRATION-FIX] Migração {app}.{migration} marcada como aplicada")
                                
                                elif app == 'notifications' and migration == '0002_add_event_key':
                                    cursor.execute("""
                                        SELECT column_name 
                                        FROM information_schema.columns 
                                        WHERE table_name = 'notifications_notification' AND column_name = 'event_key'
                                    """)
                                    if cursor.fetchone():
                                        recorder.record_applied(app, migration)
                                        print(f"✅ [MIGRATION-FIX] Migração {app}.{migration} marcada como aplicada")
                                
                                elif app == 'notifications' and migration == '0003_cleanup_old_fields':
                                    # Verificar se campos antigos foram removidos
                                    cursor.execute("""
                                        SELECT column_name 
                                        FROM information_schema.columns 
                                        WHERE table_name = 'notifications_notification' AND column_name = 'notification_type'
                                    """)
                                    if not cursor.fetchone():  # Campo antigo removido
                                        recorder.record_applied(app, migration)
                                        print(f"✅ [MIGRATION-FIX] Migração {app}.{migration} marcada como aplicada")
                        
                        return True
                    else:
                        print("❌ [MIGRATION-FIX] Estrutura da 0008 não existe, não é seguro marcar como aplicada")
                        return False
            else:
                print("✅ [MIGRATION-FIX] Histórico consistente, nenhuma correção necessária")
                return True
                
    except Exception as e:
        print(f"❌ [MIGRATION-FIX] Erro durante correção: {e}")
        return False

def apply_remaining_migrations():
    """Aplica as migrações restantes após correção do histórico"""
    
    print("🔄 [MIGRATION-FIX] Aplicando migrações restantes...")
    
    try:
        # Aplicar migrações normalmente
        execute_from_command_line(['manage.py', 'migrate', '--verbosity=2'])
        print("✅ [MIGRATION-FIX] Todas as migrações aplicadas com sucesso")
        return True
    except Exception as e:
        print(f"❌ [MIGRATION-FIX] Erro ao aplicar migrações: {e}")
        return False

def main():
    """Função principal"""
    
    print("🚀 [MIGRATION-FIX] Iniciando correção completa do histórico de migrações")
    
    # Passo 1: Corrigir histórico
    if not fix_migration_history():
        print("❌ [MIGRATION-FIX] Falha na correção do histórico")
        sys.exit(1)
    
    # Passo 2: Aplicar migrações restantes
    if not apply_remaining_migrations():
        print("❌ [MIGRATION-FIX] Falha na aplicação das migrações")
        sys.exit(1)
    
    print("🎉 [MIGRATION-FIX] Correção completa realizada com sucesso!")
    
    # Passo 3: Verificar status final
    try:
        execute_from_command_line(['manage.py', 'showmigrations'])
    except:
        pass  # Não falhar se showmigrations der erro

if __name__ == '__main__':
    main()