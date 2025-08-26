-- URGENT: Create PaymentAuditLog table in production
-- This fixes the error: relation "payments_paymentauditlog" does not exist
-- Execute this SQL directly in Railway database console

-- 1. Create the payments_paymentauditlog table
CREATE TABLE IF NOT EXISTS payments_paymentauditlog (
    id BIGSERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium' NOT NULL,
    status VARCHAR(20) NOT NULL,
    ip_address INET NULL,
    user_agent TEXT DEFAULT '' NOT NULL,
    request_id VARCHAR(100) DEFAULT '' NOT NULL,
    session_id VARCHAR(100) DEFAULT '' NOT NULL,
    amount DECIMAL(10,2) NULL,
    currency VARCHAR(3) DEFAULT '' NOT NULL,
    payment_method VARCHAR(50) DEFAULT '' NOT NULL,
    gateway_response JSONB DEFAULT '{}' NOT NULL,
    metadata JSONB DEFAULT '{}' NOT NULL,
    error_code VARCHAR(50) DEFAULT '' NOT NULL,
    error_message TEXT DEFAULT '' NOT NULL,
    processing_time INTEGER NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    company_id BIGINT NULL REFERENCES companies_company(id) ON DELETE CASCADE,
    user_id BIGINT NULL REFERENCES users_user(id) ON DELETE SET NULL
);

-- 2. Create indexes for performance
CREATE INDEX IF NOT EXISTS payments_paymentauditlog_action_created_at_idx 
    ON payments_paymentauditlog (action, created_at);

CREATE INDEX IF NOT EXISTS payments_paymentauditlog_company_created_at_idx 
    ON payments_paymentauditlog (company_id, created_at);

CREATE INDEX IF NOT EXISTS payments_paymentauditlog_user_created_at_idx 
    ON payments_paymentauditlog (user_id, created_at);

CREATE INDEX IF NOT EXISTS payments_paymentauditlog_severity_idx 
    ON payments_paymentauditlog (severity);

CREATE INDEX IF NOT EXISTS payments_paymentauditlog_status_idx 
    ON payments_paymentauditlog (status);

CREATE INDEX IF NOT EXISTS payments_paymentauditlog_session_id_idx 
    ON payments_paymentauditlog (session_id);

CREATE INDEX IF NOT EXISTS payments_paymentauditlog_request_id_idx 
    ON payments_paymentauditlog (request_id);

-- 3. Add constraints for action choices
ALTER TABLE payments_paymentauditlog ADD CONSTRAINT IF NOT EXISTS 
    payments_paymentauditlog_action_check CHECK (action IN (
        'subscription_created', 'subscription_activated', 'subscription_cancelled',
        'subscription_expired', 'subscription_plan_changed', 'payment_initiated',
        'payment_succeeded', 'payment_failed', 'payment_validated', 'payment_refunded',
        'payment_disputed', 'payment_method_added', 'payment_method_updated',
        'payment_method_removed', 'invoice_created', 'invoice_paid', 'invoice_failed',
        'trial_started', 'trial_ended', 'trial_extended', 'webhook_received',
        'webhook_processed', 'webhook_failed', 'security_alert', 'fraud_detected',
        'compliance_check', 'data_export', 'data_deletion', 'admin_action',
        'api_call', 'rate_limit_exceeded', 'system_error', 'maintenance_mode'
    ));

-- 4. Add constraints for severity choices  
ALTER TABLE payments_paymentauditlog ADD CONSTRAINT IF NOT EXISTS
    payments_paymentauditlog_severity_check CHECK (severity IN (
        'low', 'medium', 'high', 'critical'
    ));

-- 5. Add constraints for status choices
ALTER TABLE payments_paymentauditlog ADD CONSTRAINT IF NOT EXISTS
    payments_paymentauditlog_status_check CHECK (status IN (
        'success', 'failed', 'pending', 'cancelled', 'timeout'
    ));

-- 6. Register migration as applied (if django_migrations table exists)
INSERT INTO django_migrations (app, name, applied)
SELECT 'payments', '0003_add_paymentauditlog', NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM django_migrations 
    WHERE app = 'payments' AND name = '0003_add_paymentauditlog'
) AND EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_name = 'django_migrations'
);

-- 7. Verify table was created
SELECT 
    'PaymentAuditLog table created successfully' as status,
    COUNT(*) as current_records
FROM payments_paymentauditlog;