#!/usr/bin/env python
"""
Emergency script to force creation of users table
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.db import connection
from django.core.management import call_command
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def table_exists(table_name):
    """Check if a table exists in the database"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, [table_name])
        return cursor.fetchone()[0]

def create_users_table_sql():
    """Create users table using raw SQL"""
    sql = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        password VARCHAR(128),
        last_login TIMESTAMP WITH TIME ZONE,
        is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
        username VARCHAR(150) UNIQUE NOT NULL,
        first_name VARCHAR(150),
        last_name VARCHAR(150),
        email VARCHAR(254) UNIQUE NOT NULL,
        is_staff BOOLEAN NOT NULL DEFAULT FALSE,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create indexes
    CREATE INDEX IF NOT EXISTS users_username_idx ON users(username);
    CREATE INDEX IF NOT EXISTS users_email_idx ON users(email);
    
    -- Create auth tables if they don't exist
    CREATE TABLE IF NOT EXISTS auth_group (
        id SERIAL PRIMARY KEY,
        name VARCHAR(150) UNIQUE NOT NULL
    );
    
    CREATE TABLE IF NOT EXISTS auth_permission (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        content_type_id INTEGER NOT NULL,
        codename VARCHAR(100) NOT NULL
    );
    
    CREATE TABLE IF NOT EXISTS auth_group_permissions (
        id SERIAL PRIMARY KEY,
        group_id INTEGER NOT NULL REFERENCES auth_group(id),
        permission_id INTEGER NOT NULL REFERENCES auth_permission(id),
        UNIQUE(group_id, permission_id)
    );
    
    CREATE TABLE IF NOT EXISTS users_groups (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        group_id INTEGER NOT NULL REFERENCES auth_group(id),
        UNIQUE(user_id, group_id)
    );
    
    CREATE TABLE IF NOT EXISTS users_user_permissions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        permission_id INTEGER NOT NULL REFERENCES auth_permission(id),
        UNIQUE(user_id, permission_id)
    );
    """
    
    with connection.cursor() as cursor:
        cursor.execute(sql)
        logger.info("Users table and related auth tables created successfully")

def main():
    try:
        # Check if users table exists
        if not table_exists('users'):
            logger.warning("Users table does not exist, creating it...")
            create_users_table_sql()
            logger.info("Users table created successfully")
        else:
            logger.info("Users table already exists")
        
        # Check django_content_type table
        if not table_exists('django_content_type'):
            logger.warning("django_content_type table missing, creating...")
            with connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS django_content_type (
                        id SERIAL PRIMARY KEY,
                        app_label VARCHAR(100) NOT NULL,
                        model VARCHAR(100) NOT NULL,
                        UNIQUE(app_label, model)
                    );
                """)
            logger.info("django_content_type table created")
        
        # Mark migrations as needing to be faked since we created tables manually
        logger.info("Marking authentication migrations as applied...")
        with connection.cursor() as cursor:
            # Check if migration record exists
            cursor.execute("""
                SELECT COUNT(*) FROM django_migrations 
                WHERE app = 'authentication' AND name = '0001_initial'
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied)
                    VALUES ('authentication', '0001_initial', CURRENT_TIMESTAMP)
                """)
                logger.info("Marked authentication 0001_initial as applied")
        
        logger.info("✅ Database tables ready!")
        return True
        
    except Exception as e:
        logger.error(f"Error creating users table: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)