#!/usr/bin/env python
"""
Script para corrigir dependências de migração em produção
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

def fix_migration_dependencies():
    """Corrige dependências de migração"""
    
    try:
        recorder = MigrationRecorder(connection)
        applied_migrations = set(recorder.applied_migrations())
        
        print("🔍 Migrações aplicadas:")
        for app, name in sorted(applied_migrations):
            if app in ['companies', 'authentication']:
                print(f"  ✅ {app}.{name}")
        
        # Verificar se 0008 está aplicada mas 0009 foi aplicada antes
        companies_0008 = ('companies', '0008_alter_resourceusage_options_and_more')
        companies_0009 = ('companies', '0009_add_early_access')
        
        if companies_0009 in applied_migrations and companies_0008 not in applied_migrations:
            print(f"\n⚠️  Problema detectado: {companies_0009[1]} aplicada sem {companies_0008[1]}")
            
            # Verificar se tabela resourceusage tem as colunas da migração 0008
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'resourceusage' 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """)
                columns = [row[0] for row in cursor.fetchall()]
                print(f"📊 Colunas da tabela resourceusage: {columns}")
                
                # Se as alterações da 0008 já existem, marcar como aplicada
                if 'created_at' in columns and 'updated_at' in columns:
                    print("✅ Tabela resourceusage já tem as colunas necessárias")
                    print("🔧 Marcando migração 0008 como aplicada...")
                    
                    recorder.record_applied(companies_0008[0], companies_0008[1])
                    print("✅ Migração 0008 marcada como aplicada")
                else:
                    print("❌ Tabela resourceusage não tem as colunas necessárias")
        
        # Verificar tabela email_verifications
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'email_verifications';
            """)
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                print("\n⚠️  Tabela email_verifications não existe, criando...")
                
                # Criar tabela
                cursor.execute("""
                    CREATE TABLE email_verifications (
                        id BIGSERIAL PRIMARY KEY,
                        token VARCHAR(100) UNIQUE NOT NULL,
                        is_used BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        expires_at TIMESTAMPTZ NOT NULL,
                        user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
                    );
                """)
                
                # Criar índices
                cursor.execute('CREATE INDEX email_verif_user_id_f77c27_idx ON email_verifications (user_id, is_used);')
                cursor.execute('CREATE INDEX email_verif_token_403404_idx ON email_verifications (token);')
                cursor.execute('CREATE INDEX email_verif_expires_fdd67c_idx ON email_verifications (expires_at);')
                
                # Marcar migração como aplicada
                recorder.record_applied('authentication', '0003_emailverification')
                
                print("✅ Tabela email_verifications criada e migração marcada como aplicada")
            else:
                print("\n✅ Tabela email_verifications já existe")
        
        print("\n🎉 Correção de dependências concluída!")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Corrigindo dependências de migração...")
    fix_migration_dependencies()