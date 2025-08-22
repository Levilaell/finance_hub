#!/usr/bin/env python
"""
Script para aplicar as partes faltantes da migração companies.0008 
que não estão presentes na companies.0009 já aplicada.

Resolve: InconsistentMigrationHistory entre 0008 e 0009
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.db import connection, transaction
from django.db.migrations.recorder import MigrationRecorder

def apply_missing_resourceusage_changes():
    """Aplica as alterações da ResourceUsage que estão faltando da migração 0008"""
    
    print("🔧 [0008-DIFF] Aplicando mudanças faltantes na ResourceUsage...")
    
    try:
        with connection.cursor() as cursor:
            # Verificar se a tabela ResourceUsage existe
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'companies_resourceusage'
            """)
            
            if not cursor.fetchone():
                print("❌ [0008-DIFF] Tabela companies_resourceusage não encontrada")
                return False
            
            # 1. Adicionar campos de notificação se não existirem
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'companies_resourceusage' 
                AND column_name IN ('notified_80_percent', 'notified_90_percent')
            """)
            existing_notification_fields = [row[0] for row in cursor.fetchall()]
            
            if 'notified_80_percent' not in existing_notification_fields:
                print("➕ [0008-DIFF] Adicionando campo notified_80_percent...")
                cursor.execute("""
                    ALTER TABLE companies_resourceusage 
                    ADD COLUMN notified_80_percent BOOLEAN DEFAULT FALSE
                """)
                cursor.execute("""
                    COMMENT ON COLUMN companies_resourceusage.notified_80_percent 
                    IS '80% usage notification sent'
                """)
            
            if 'notified_90_percent' not in existing_notification_fields:
                print("➕ [0008-DIFF] Adicionando campo notified_90_percent...")
                cursor.execute("""
                    ALTER TABLE companies_resourceusage 
                    ADD COLUMN notified_90_percent BOOLEAN DEFAULT FALSE
                """)
                cursor.execute("""
                    COMMENT ON COLUMN companies_resourceusage.notified_90_percent 
                    IS '90% usage notification sent'
                """)
            
            # 2. Verificar e adicionar campos created_at e updated_at se necessário
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'companies_resourceusage' 
                AND column_name IN ('created_at', 'updated_at')
                ORDER BY column_name
            """)
            timestamp_fields = {row[0]: {'type': row[1], 'nullable': row[2]} for row in cursor.fetchall()}
            
            # Adicionar created_at se não existir ou estiver mal configurado
            if 'created_at' not in timestamp_fields:
                print("➕ [0008-DIFF] Adicionando campo created_at...")
                cursor.execute("""
                    ALTER TABLE companies_resourceusage 
                    ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
                """)
            elif timestamp_fields['created_at']['nullable'] == 'YES':
                print("🔧 [0008-DIFF] Corrigindo created_at para NOT NULL...")
                cursor.execute("""
                    UPDATE companies_resourceusage 
                    SET created_at = NOW() 
                    WHERE created_at IS NULL
                """)
                cursor.execute("""
                    ALTER TABLE companies_resourceusage 
                    ALTER COLUMN created_at SET NOT NULL
                """)
            
            # Adicionar updated_at se não existir ou estiver mal configurado
            if 'updated_at' not in timestamp_fields:
                print("➕ [0008-DIFF] Adicionando campo updated_at...")
                cursor.execute("""
                    ALTER TABLE companies_resourceusage 
                    ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
                """)
            elif timestamp_fields['updated_at']['nullable'] == 'YES':
                print("🔧 [0008-DIFF] Corrigindo updated_at para NOT NULL...")
                cursor.execute("""
                    UPDATE companies_resourceusage 
                    SET updated_at = NOW() 
                    WHERE updated_at IS NULL
                """)
                cursor.execute("""
                    ALTER TABLE companies_resourceusage 
                    ALTER COLUMN updated_at SET NOT NULL
                """)
            
            # 3. Verificar e ajustar outros campos se necessário
            print("🔍 [0008-DIFF] Verificando outros campos da ResourceUsage...")
            
            # Garantir que ai_requests_count, reports_generated, transactions_count não são nulos
            for field in ['ai_requests_count', 'reports_generated', 'transactions_count']:
                cursor.execute(f"""
                    UPDATE companies_resourceusage 
                    SET {field} = 0 
                    WHERE {field} IS NULL
                """)
                cursor.execute(f"""
                    ALTER TABLE companies_resourceusage 
                    ALTER COLUMN {field} SET DEFAULT 0
                """)
                cursor.execute(f"""
                    ALTER TABLE companies_resourceusage 
                    ALTER COLUMN {field} SET NOT NULL
                """)
            
            print("✅ [0008-DIFF] Mudanças na ResourceUsage aplicadas com sucesso")
            return True
            
    except Exception as e:
        print(f"❌ [0008-DIFF] Erro ao aplicar mudanças na ResourceUsage: {e}")
        return False

def mark_migration_as_applied():
    """Marca a migração 0008 como aplicada no histórico do Django"""
    
    print("📝 [0008-DIFF] Marcando migração 0008 como aplicada...")
    
    try:
        recorder = MigrationRecorder(connection)
        recorder.record_applied('companies', '0008_alter_resourceusage_options_and_more')
        print("✅ [0008-DIFF] Migração 0008 marcada como aplicada no histórico")
        return True
    except Exception as e:
        print(f"❌ [0008-DIFF] Erro ao marcar migração: {e}")
        return False

def verify_structure():
    """Verifica se a estrutura final está correta"""
    
    print("🔍 [0008-DIFF] Verificando estrutura final...")
    
    try:
        with connection.cursor() as cursor:
            # Verificar ResourceUsage
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'companies_resourceusage'
                ORDER BY column_name
            """)
            
            columns = {row[0]: {'type': row[1], 'nullable': row[2]} for row in cursor.fetchall()}
            
            required_fields = [
                'notified_80_percent',
                'notified_90_percent', 
                'created_at',
                'updated_at',
                'ai_requests_count',
                'reports_generated',
                'transactions_count'
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in columns:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"⚠️  [0008-DIFF] Campos ainda faltando: {missing_fields}")
                return False
            
            print("✅ [0008-DIFF] Estrutura da ResourceUsage está completa")
            
            # Verificar Company (já deve estar OK por causa da 0009)
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns 
                WHERE table_name = 'companies_company'
                AND column_name IN ('is_early_access', 'early_access_expires_at', 'used_invite_code')
            """)
            
            company_fields = [row[0] for row in cursor.fetchall()]
            
            if len(company_fields) >= 3:
                print("✅ [0008-DIFF] Campos da Company estão OK")
            else:
                print(f"⚠️  [0008-DIFF] Campos da Company faltando: {3 - len(company_fields)}")
            
            # Verificar EarlyAccessInvite
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'early_access_invites'
            """)
            
            if cursor.fetchone():
                print("✅ [0008-DIFF] Tabela EarlyAccessInvite existe")
            else:
                print("⚠️  [0008-DIFF] Tabela EarlyAccessInvite faltando")
            
            return True
            
    except Exception as e:
        print(f"❌ [0008-DIFF] Erro na verificação: {e}")
        return False

def main():
    """Função principal para correção diferencial da migração 0008"""
    
    print("🚀 [0008-DIFF] Iniciando correção diferencial da migração companies.0008")
    
    # Verificar se é necessário fazer a correção
    recorder = MigrationRecorder(connection)
    applied_migrations = set(recorder.applied_migrations())
    
    companies_0008 = ('companies', '0008_alter_resourceusage_options_and_more')
    companies_0009 = ('companies', '0009_add_early_access')
    
    if companies_0008 in applied_migrations:
        print("✅ [0008-DIFF] Migração 0008 já está aplicada, nenhuma correção necessária")
        return True
    
    if companies_0009 not in applied_migrations:
        print("❌ [0008-DIFF] Migração 0009 não está aplicada, situação inesperada")
        return False
    
    print("🔍 [0008-DIFF] Situação confirmada: 0009 aplicada, 0008 faltando")
    
    # Aplicar as mudanças estruturais faltantes
    if not apply_missing_resourceusage_changes():
        print("❌ [0008-DIFF] Falha ao aplicar mudanças estruturais")
        return False
    
    # Marcar migração como aplicada
    if not mark_migration_as_applied():
        print("❌ [0008-DIFF] Falha ao marcar migração como aplicada")
        return False
    
    # Verificar estrutura final
    if not verify_structure():
        print("⚠️  [0008-DIFF] Estrutura final pode ter problemas")
    
    print("🎉 [0008-DIFF] Correção diferencial da migração 0008 concluída com sucesso!")
    return True

if __name__ == '__main__':
    try:
        with transaction.atomic():
            success = main()
            if not success:
                print("❌ [0008-DIFF] Falha na correção, revertendo transação")
                sys.exit(1)
    except Exception as e:
        print(f"❌ [0008-DIFF] Erro crítico: {e}")
        sys.exit(1)