-- Initialize FinanceHub Database
-- This script sets up the initial database configuration

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create initial admin user (will be created by Django)
-- This is just a placeholder for any custom SQL setup

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE financehub TO financehub;