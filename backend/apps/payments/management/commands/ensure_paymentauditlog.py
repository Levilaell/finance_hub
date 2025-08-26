"""
Management command to ensure PaymentAuditLog table exists and create it if needed.
This is a workaround for production where migrations may not run automatically.
"""
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Ensure PaymentAuditLog table exists in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only check if table exists without creating it',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate table even if it exists',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write("🔍 Checking PaymentAuditLog table status...")
        
        with connection.cursor() as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'payments_paymentauditlog'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if table_exists and not force:
                self.stdout.write(
                    self.style.SUCCESS("✅ PaymentAuditLog table already exists")
                )
                
                # Check record count
                cursor.execute("SELECT COUNT(*) FROM payments_paymentauditlog;")
                count = cursor.fetchone()[0]
                self.stdout.write(f"📊 Current records: {count}")
                return
            
            if dry_run:
                if table_exists:
                    self.stdout.write("✅ Table exists - no action needed")
                else:
                    self.stdout.write("❌ Table missing - would create with --no-dry-run")
                return
            
            if force and table_exists:
                self.stdout.write("⚠️ Dropping existing table...")
                cursor.execute("DROP TABLE IF EXISTS payments_paymentauditlog CASCADE;")
            
            self.stdout.write("🔨 Creating PaymentAuditLog table...")
            
            with transaction.atomic():
                # Create table
                cursor.execute("""
                    CREATE TABLE payments_paymentauditlog (
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
                        company_id BIGINT NULL,
                        user_id BIGINT NULL
                    );
                """)
                
                # Add foreign key constraints if tables exist
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'companies_company'
                    );
                """)
                if cursor.fetchone()[0]:
                    cursor.execute("""
                        ALTER TABLE payments_paymentauditlog 
                        ADD CONSTRAINT fk_paymentauditlog_company
                        FOREIGN KEY (company_id) REFERENCES companies_company(id) ON DELETE CASCADE;
                    """)
                
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name IN ('auth_user', 'users_user')
                    );
                """)
                user_table_exists = cursor.fetchone()[0]
                if user_table_exists:
                    # Check which user table exists
                    cursor.execute("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_name IN ('auth_user', 'users_user')
                        ORDER BY table_name LIMIT 1;
                    """)
                    user_table = cursor.fetchone()[0]
                    cursor.execute(f"""
                        ALTER TABLE payments_paymentauditlog 
                        ADD CONSTRAINT fk_paymentauditlog_user
                        FOREIGN KEY (user_id) REFERENCES {user_table}(id) ON DELETE SET NULL;
                    """)
                
                # Create indexes
                indexes = [
                    ("payments_paymentauditlog_action_created_at_idx", "action, created_at"),
                    ("payments_paymentauditlog_company_created_at_idx", "company_id, created_at"),
                    ("payments_paymentauditlog_user_created_at_idx", "user_id, created_at"),
                    ("payments_paymentauditlog_severity_idx", "severity"),
                    ("payments_paymentauditlog_status_idx", "status"),
                    ("payments_paymentauditlog_session_id_idx", "session_id"),
                    ("payments_paymentauditlog_request_id_idx", "request_id"),
                ]
                
                for index_name, columns in indexes:
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON payments_paymentauditlog ({columns});
                    """)
                
                # Add constraints
                cursor.execute("""
                    ALTER TABLE payments_paymentauditlog 
                    ADD CONSTRAINT IF NOT EXISTS payments_paymentauditlog_action_check 
                    CHECK (action IN (
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
                """)
                
                cursor.execute("""
                    ALTER TABLE payments_paymentauditlog 
                    ADD CONSTRAINT IF NOT EXISTS payments_paymentauditlog_severity_check 
                    CHECK (severity IN ('low', 'medium', 'high', 'critical'));
                """)
                
                cursor.execute("""
                    ALTER TABLE payments_paymentauditlog 
                    ADD CONSTRAINT IF NOT EXISTS payments_paymentauditlog_status_check 
                    CHECK (status IN ('success', 'failed', 'pending', 'cancelled', 'timeout'));
                """)
                
                # Register migration if django_migrations exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'django_migrations'
                    );
                """)
                if cursor.fetchone()[0]:
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied)
                        SELECT 'payments', '0003_add_paymentauditlog', NOW()
                        WHERE NOT EXISTS (
                            SELECT 1 FROM django_migrations 
                            WHERE app = 'payments' AND name = '0003_add_paymentauditlog'
                        );
                    """)
            
            self.stdout.write(
                self.style.SUCCESS("✅ PaymentAuditLog table created successfully!")
            )
            
            # Verify creation
            cursor.execute("SELECT COUNT(*) FROM payments_paymentauditlog;")
            self.stdout.write(f"📊 Table is ready with {cursor.fetchone()[0]} records")
            
    def test_table_functionality(self):
        """Test if we can create and read from the table"""
        try:
            from ..models_audit import PaymentAuditLog
            
            # Try to create a test record
            test_log = PaymentAuditLog.objects.create(
                action='system_test',
                severity='low',
                status='success',
                metadata={'test': True}
            )
            
            # Clean up
            test_log.delete()
            
            self.stdout.write(
                self.style.SUCCESS("✅ Table functionality test passed")
            )
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Table functionality test failed: {e}")
            )
            return False