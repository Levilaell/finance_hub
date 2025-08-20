#!/usr/bin/env python
"""
Script para aplicar a migração email_verification em produção
Executa diretamente o SQL necessário para criar a tabela
"""
import os
import sys
import django
from django.db import connection
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

def apply_email_verification_migration():
    """Aplica a migração email_verification via SQL direto"""
    
    sql_commands = [
        """
        CREATE TABLE IF NOT EXISTS email_verifications (
            id BIGSERIAL PRIMARY KEY,
            token VARCHAR(100) UNIQUE NOT NULL,
            is_used BOOLEAN DEFAULT FALSE NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
        );
        """,
        "CREATE INDEX IF NOT EXISTS email_verif_user_id_f77c27_idx ON email_verifications (user_id, is_used);",
        "CREATE INDEX IF NOT EXISTS email_verif_token_403404_idx ON email_verifications (token);",
        "CREATE INDEX IF NOT EXISTS email_verif_expires_fdd67c_idx ON email_verifications (expires_at);",
        """
        INSERT INTO django_migrations (app, name, applied) 
        VALUES ('authentication', '0003_emailverification', NOW())
        ON CONFLICT (app, name) DO NOTHING;
        """
    ]
    
    try:
        with connection.cursor() as cursor:
            for sql in sql_commands:
                print(f"Executando: {sql.strip()[:50]}...")
                cursor.execute(sql)
            
        print("✅ Migração aplicada com sucesso!")
        print("✅ Tabela email_verifications criada")
        print("✅ Índices criados")
        print("✅ Migração registrada no django_migrations")
        
        # Verificar se a tabela foi criada
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'email_verifications';")
            result = cursor.fetchone()
            if result[0] > 0:
                print("✅ Verificação: Tabela email_verifications existe")
            else:
                print("❌ Erro: Tabela não foi criada")
                
    except Exception as e:
        print(f"❌ Erro ao aplicar migração: {e}")
        return False
        
    return True

if __name__ == "__main__":
    print("🔧 Aplicando migração email_verification em produção...")
    success = apply_email_verification_migration()
    sys.exit(0 if success else 1)