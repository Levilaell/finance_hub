# Generated database indexes for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0005_bankaccount_pluggy_item_id'),
    ]

    operations = [
        # Transaction performance indexes - SQLite compatible
        migrations.RunSQL([
            "CREATE INDEX IF NOT EXISTS idx_transaction_company_date ON banking_transaction(company_id, transaction_date);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_bank_account_date ON banking_transaction(bank_account_id, transaction_date);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_category_date ON banking_transaction(category_id, transaction_date);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_amount_type ON banking_transaction(transaction_type, amount);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_external_id ON banking_transaction(external_id);",
        ], [
            "DROP INDEX IF EXISTS idx_transaction_company_date;",
            "DROP INDEX IF EXISTS idx_transaction_bank_account_date;",
            "DROP INDEX IF EXISTS idx_transaction_category_date;",
            "DROP INDEX IF EXISTS idx_transaction_amount_type;",
            "DROP INDEX IF EXISTS idx_transaction_external_id;",
        ]),
        
        # Bank account indexes
        migrations.RunSQL([
            "CREATE INDEX IF NOT EXISTS idx_bank_account_company_active ON banking_bankaccount(company_id, is_active);",
            "CREATE INDEX IF NOT EXISTS idx_bank_account_status ON banking_bankaccount(status);",
            "CREATE INDEX IF NOT EXISTS idx_bank_account_provider ON banking_bankaccount(bank_provider_id);",
        ], [
            "DROP INDEX IF EXISTS idx_bank_account_company_active;",
            "DROP INDEX IF EXISTS idx_bank_account_status;",
            "DROP INDEX IF EXISTS idx_bank_account_provider;",
        ]),
        
        # Budget and goal indexes
        migrations.RunSQL([
            "CREATE INDEX IF NOT EXISTS idx_budget_company_period ON banking_budget(company_id, period_start, period_end);",
            "CREATE INDEX IF NOT EXISTS idx_financial_goal_company_status ON banking_financialgoal(company_id, status);",
        ], [
            "DROP INDEX IF EXISTS idx_budget_company_period;",
            "DROP INDEX IF EXISTS idx_financial_goal_company_status;",
        ]),
    ]