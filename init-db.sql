-- Initialization script for PostgreSQL
-- Creates necessary extensions and initial setup

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Create custom text search configuration for Portuguese
CREATE TEXT SEARCH CONFIGURATION IF NOT EXISTS portuguese_unaccent (COPY = portuguese);
ALTER TEXT SEARCH CONFIGURATION portuguese_unaccent
    ALTER MAPPING FOR hword, hword_part, word
    WITH unaccent, portuguese_stem;

-- Create indexes for better performance
-- These will be created after Django migrations run
-- Just documenting the recommended indexes here

-- For authentication_user table
-- CREATE INDEX idx_auth_user_email_trgm ON authentication_user USING gin (email gin_trgm_ops);
-- CREATE INDEX idx_auth_user_created_at ON authentication_user (created_at);

-- For banking_transaction table
-- CREATE INDEX idx_transaction_date ON banking_transaction (transaction_date);
-- CREATE INDEX idx_transaction_amount ON banking_transaction (amount);
-- CREATE INDEX idx_transaction_description_trgm ON banking_transaction USING gin (description gin_trgm_ops);
-- CREATE INDEX idx_transaction_counterpart_trgm ON banking_transaction USING gin (counterpart_name gin_trgm_ops);

-- For companies_company table
-- CREATE INDEX idx_company_cnpj ON companies_company (cnpj);
-- CREATE INDEX idx_company_name_trgm ON companies_company USING gin (name gin_trgm_ops);

-- Set default configuration
ALTER DATABASE ${DB_NAME} SET default_text_search_config = 'portuguese_unaccent';