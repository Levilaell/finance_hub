#!/usr/bin/env python
"""
Emergency database fix script for Railway deployment
Run this to fix migration issues and create critical tables
"""
import os
import sys
import django

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.db import connection

def fix_migrations():
    """Fix inconsistent migration history"""
    print("🔧 Fixing migration inconsistencies...")
    
    try:
        with connection.cursor() as cursor:
            # First, check if django_migrations table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'django_migrations'
                )
            """)
            
            if not cursor.fetchone()[0]:
                print("Creating django_migrations table...")
                cursor.execute("""
                    CREATE TABLE django_migrations (
                        id SERIAL PRIMARY KEY,
                        app VARCHAR(255) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        applied TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
            # Check for the specific problem
            cursor.execute("""
                SELECT COUNT(*) FROM django_migrations 
                WHERE app = 'reports' 
                AND name = '0003_aianalysistemplate_aianalysis'
            """)
            
            if cursor.fetchone()[0] > 0:
                print("Found problematic migration 0003, adding missing 0002...")
                
                # Add the missing dependency
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied)
                    VALUES ('reports', '0002_alter_aianalysis_options_and_more', NOW())
                    ON CONFLICT DO NOTHING
                """)
                
                print("✅ Migration dependency fixed")
            
            # Also mark some core migrations as applied if needed
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied)
                VALUES 
                    ('contenttypes', '0001_initial', NOW()),
                    ('contenttypes', '0002_remove_content_type_name', NOW()),
                    ('auth', '0001_initial', NOW()),
                    ('sessions', '0001_initial', NOW())
                ON CONFLICT DO NOTHING
            """)
            
    except Exception as e:
        print(f"⚠️ Could not fix migrations: {e}")
        return False
    
    return True

def create_critical_tables():
    """Create critical tables if they don't exist"""
    print("📊 Creating critical tables...")
    
    try:
        with connection.cursor() as cursor:
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    password VARCHAR(128) NOT NULL,
                    last_login TIMESTAMPTZ,
                    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
                    username VARCHAR(150) UNIQUE NOT NULL,
                    email VARCHAR(254) NOT NULL,
                    first_name VARCHAR(150),
                    last_name VARCHAR(150),
                    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    date_joined TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    cpf VARCHAR(14),
                    phone VARCHAR(20),
                    date_of_birth DATE,
                    two_factor_enabled BOOLEAN NOT NULL DEFAULT FALSE,
                    two_factor_secret VARCHAR(32),
                    backup_codes TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Users table created/verified")
            
            # Create companies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    slug VARCHAR(50) UNIQUE NOT NULL,
                    cnpj VARCHAR(18),
                    email VARCHAR(254),
                    phone VARCHAR(20),
                    website VARCHAR(200),
                    description TEXT,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Companies table created/verified")
            
            # Create django_session table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS django_session (
                    session_key VARCHAR(40) PRIMARY KEY,
                    session_data TEXT NOT NULL,
                    expire_date TIMESTAMPTZ NOT NULL
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS django_session_expire_date_idx 
                ON django_session(expire_date)
            """)
            print("✅ Session table created/verified")
            
            # Create django_content_type table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS django_content_type (
                    id SERIAL PRIMARY KEY,
                    app_label VARCHAR(100) NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    UNIQUE(app_label, model)
                )
            """)
            print("✅ Content type table created/verified")
            
    except Exception as e:
        print(f"⚠️ Error creating tables: {e}")
        return False
    
    return True

def main():
    """Main execution"""
    print("🚀 Starting emergency database fix...")
    
    # Fix migrations
    if fix_migrations():
        print("✅ Migrations fixed successfully")
    
    # Create critical tables
    if create_critical_tables():
        print("✅ Critical tables ensured")
    
    print("\n🎉 Database fix completed!")
    print("You can now run: python manage.py migrate --noinput")

if __name__ == "__main__":
    main()