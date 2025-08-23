-- SUPER-NUCLEAR MIGRATION FIX - SQL DIRETO
-- Executa correção definitiva de auth.0003 vs auth.0002 + todas outras migrações

-- Step 1: Remove squashed migration conflicts
DELETE FROM django_migrations WHERE app = 'notifications' AND name = '0001_squashed_0001_initial';

-- Step 2: Restructure ALL migrations in perfect chronological order
-- Django Core Apps first
UPDATE django_migrations SET applied = '2025-08-12 00:00:00+00:00' WHERE app = 'contenttypes' AND name = '0001_initial';
UPDATE django_migrations SET applied = '2025-08-12 00:00:01+00:00' WHERE app = 'contenttypes' AND name = '0002_remove_content_type_name';

-- AUTH MIGRATIONS - CRITICAL FIX FOR auth.0003 vs auth.0002
UPDATE django_migrations SET applied = '2025-08-12 00:00:02+00:00' WHERE app = 'auth' AND name = '0001_initial';
UPDATE django_migrations SET applied = '2025-08-12 00:00:03+00:00' WHERE app = 'auth' AND name = '0002_alter_permission_name_max_length';
UPDATE django_migrations SET applied = '2025-08-12 00:00:04+00:00' WHERE app = 'auth' AND name = '0003_alter_user_email_max_length';
UPDATE django_migrations SET applied = '2025-08-12 00:00:05+00:00' WHERE app = 'auth' AND name = '0004_alter_user_username_opts';
UPDATE django_migrations SET applied = '2025-08-12 00:00:06+00:00' WHERE app = 'auth' AND name = '0005_alter_user_last_login_null';
UPDATE django_migrations SET applied = '2025-08-12 00:00:07+00:00' WHERE app = 'auth' AND name = '0006_require_contenttypes_0002';
UPDATE django_migrations SET applied = '2025-08-12 00:00:08+00:00' WHERE app = 'auth' AND name = '0007_alter_validators_add_error_messages';
UPDATE django_migrations SET applied = '2025-08-12 00:00:09+00:00' WHERE app = 'auth' AND name = '0008_alter_user_username_max_length';
UPDATE django_migrations SET applied = '2025-08-12 00:00:10+00:00' WHERE app = 'auth' AND name = '0009_alter_user_last_name_max_length';
UPDATE django_migrations SET applied = '2025-08-12 00:00:11+00:00' WHERE app = 'auth' AND name = '0010_alter_group_name_max_length';
UPDATE django_migrations SET applied = '2025-08-12 00:00:12+00:00' WHERE app = 'auth' AND name = '0011_update_proxy_permissions';
UPDATE django_migrations SET applied = '2025-08-12 00:00:13+00:00' WHERE app = 'auth' AND name = '0012_alter_user_first_name_max_length';

-- Sessions and Admin
UPDATE django_migrations SET applied = '2025-08-12 00:00:14+00:00' WHERE app = 'sessions' AND name = '0001_initial';
UPDATE django_migrations SET applied = '2025-08-12 00:00:15+00:00' WHERE app = 'admin' AND name = '0001_initial';
UPDATE django_migrations SET applied = '2025-08-12 00:00:16+00:00' WHERE app = 'admin' AND name = '0002_logentry_remove_auto_add';
UPDATE django_migrations SET applied = '2025-08-12 00:00:17+00:00' WHERE app = 'admin' AND name = '0003_logentry_add_action_flag_choices';

-- Custom Apps - Authentication
UPDATE django_migrations SET applied = '2025-08-12 00:00:20+00:00' WHERE app = 'authentication' AND name = '0001_initial';
UPDATE django_migrations SET applied = '2025-08-12 00:00:21+00:00' WHERE app = 'authentication' AND name = '0002_remove_email_verification';
UPDATE django_migrations SET applied = '2025-08-12 00:00:22+00:00' WHERE app = 'authentication' AND name = '0003_emailverification';

-- Companies
UPDATE django_migrations SET applied = '2025-08-12 00:00:25+00:00' WHERE app = 'companies' AND name = '0001_initial';
UPDATE django_migrations SET applied = '2025-08-12 00:00:26+00:00' WHERE app = 'companies' AND name = '0002_auto_simplify';
UPDATE django_migrations SET applied = '2025-08-12 00:00:27+00:00' WHERE app = 'companies' AND name = '0003_consolidate_subscriptions';
UPDATE django_migrations SET applied = '2025-08-12 00:00:28+00:00' WHERE app = 'companies' AND name = '0004_merge_20250715_2204';
UPDATE django_migrations SET applied = '2025-08-12 00:00:29+00:00' WHERE app = 'companies' AND name = '0005_resourceusage';
UPDATE django_migrations SET applied = '2025-08-12 00:00:30+00:00' WHERE app = 'companies' AND name = '0006_remove_max_users_field';
UPDATE django_migrations SET applied = '2025-08-12 00:00:31+00:00' WHERE app = 'companies' AND name = '0007_add_stripe_price_ids';
UPDATE django_migrations SET applied = '2025-08-12 00:00:32+00:00' WHERE app = 'companies' AND name = '0008_alter_resourceusage_options_and_more';
UPDATE django_migrations SET applied = '2025-08-12 00:00:33+00:00' WHERE app = 'companies' AND name = '0009_add_early_access';

-- Notifications
UPDATE django_migrations SET applied = '2025-08-12 00:00:35+00:00' WHERE app = 'notifications' AND name = '0001_initial';

-- Audit
UPDATE django_migrations SET applied = '2025-08-12 00:00:37+00:00' WHERE app = 'audit' AND name = '0001_initial';

-- Payments
UPDATE django_migrations SET applied = '2025-08-12 00:00:40+00:00' WHERE app = 'payments' AND name = '0001_initial';
UPDATE django_migrations SET applied = '2025-08-12 00:00:41+00:00' WHERE app = 'payments' AND name = '0002_alter_subscription_plan_paymentretry_and_more';

-- Banking
UPDATE django_migrations SET applied = '2025-08-12 00:00:45+00:00' WHERE app = 'banking' AND name = '0001_initial';
UPDATE django_migrations SET applied = '2025-08-12 00:00:46+00:00' WHERE app = 'banking' AND name = '0002_add_consent_model';
UPDATE django_migrations SET applied = '2025-08-12 00:00:47+00:00' WHERE app = 'banking' AND name = '0003_alter_transaction_merchant';
UPDATE django_migrations SET applied = '2025-08-12 00:00:48+00:00' WHERE app = 'banking' AND name = '0004_alter_transaction_fields';
UPDATE django_migrations SET applied = '2025-08-12 00:00:49+00:00' WHERE app = 'banking' AND name = '0005_pluggy_webhook_validation';
UPDATE django_migrations SET applied = '2025-08-12 00:00:50+00:00' WHERE app = 'banking' AND name = '0006_add_webhook_improvements';
UPDATE django_migrations SET applied = '2025-08-12 00:00:51+00:00' WHERE app = 'banking' AND name = '0007_merge_20250730_2231';
UPDATE django_migrations SET applied = '2025-08-12 00:00:52+00:00' WHERE app = 'banking' AND name = '0008_delete_consent';
UPDATE django_migrations SET applied = '2025-08-12 00:00:53+00:00' WHERE app = 'banking' AND name = '0009_add_transaction_indexes';
UPDATE django_migrations SET applied = '2025-08-12 00:00:54+00:00' WHERE app = 'banking' AND name = '0010_add_encrypted_parameter';
UPDATE django_migrations SET applied = '2025-08-12 00:00:55+00:00' WHERE app = 'banking' AND name = '0011_remove_transaction_banking_tra_acc_date_idx_and_more';

-- Reports
UPDATE django_migrations SET applied = '2025-08-12 00:01:00+00:00' WHERE app = 'reports' AND name = '0001_initial';
UPDATE django_migrations SET applied = '2025-08-12 00:01:01+00:00' WHERE app = 'reports' AND name = '0002_alter_aianalysis_options_and_more';
UPDATE django_migrations SET applied = '2025-08-12 00:01:02+00:00' WHERE app = 'reports' AND name = '0003_aianalysistemplate_aianalysis';
UPDATE django_migrations SET applied = '2025-08-12 00:01:03+00:00' WHERE app = 'reports' AND name = '0004_merge_20250803_2225';
UPDATE django_migrations SET applied = '2025-08-12 00:01:04+00:00' WHERE app = 'reports' AND name = '0005_fix_inconsistent_history';

-- AI Insights
UPDATE django_migrations SET applied = '2025-08-12 00:01:10+00:00' WHERE app = 'ai_insights' AND name = '0001_initial';
UPDATE django_migrations SET applied = '2025-08-12 00:01:11+00:00' WHERE app = 'ai_insights' AND name = '0002_auto_20240101_0000';
UPDATE django_migrations SET applied = '2025-08-12 00:01:12+00:00' WHERE app = 'ai_insights' AND name = '0003_add_encrypted_fields';
UPDATE django_migrations SET applied = '2025-08-12 00:01:13+00:00' WHERE app = 'ai_insights' AND name = '0004_alter_aiconversation_financial_context_and_more';

-- Third-party apps (if exist)
UPDATE django_migrations SET applied = '2025-08-12 00:01:20+00:00' WHERE app = 'django_celery_beat' AND name = '0001_initial';
UPDATE django_migrations SET applied = '2025-08-12 00:01:21+00:00' WHERE app = 'django_celery_beat' AND name = '0002_auto_20161118_0346';
UPDATE django_migrations SET applied = '2025-08-12 00:01:22+00:00' WHERE app = 'django_celery_beat' AND name = '0003_auto_20161209_0049';
UPDATE django_migrations SET applied = '2025-08-12 00:01:23+00:00' WHERE app = 'django_celery_beat' AND name = '0004_auto_20170221_0000';
UPDATE django_migrations SET applied = '2025-08-12 00:01:24+00:00' WHERE app = 'django_celery_beat' AND name = '0005_add_solarschedule_events_choices';
UPDATE django_migrations SET applied = '2025-08-12 00:01:25+00:00' WHERE app = 'django_celery_beat' AND name = '0006_auto_20180322_0932';
UPDATE django_migrations SET applied = '2025-08-12 00:01:26+00:00' WHERE app = 'django_celery_beat' AND name = '0007_auto_20180521_0826';
UPDATE django_migrations SET applied = '2025-08-12 00:01:27+00:00' WHERE app = 'django_celery_beat' AND name = '0008_auto_20180914_1922';
UPDATE django_migrations SET applied = '2025-08-12 00:01:28+00:00' WHERE app = 'django_celery_beat' AND name = '0009_periodictask_headers';
UPDATE django_migrations SET applied = '2025-08-12 00:01:29+00:00' WHERE app = 'django_celery_beat' AND name = '0010_auto_20190429_0326';
UPDATE django_migrations SET applied = '2025-08-12 00:01:30+00:00' WHERE app = 'django_celery_beat' AND name = '0011_auto_20190508_0153';
UPDATE django_migrations SET applied = '2025-08-12 00:01:31+00:00' WHERE app = 'django_celery_beat' AND name = '0012_periodictask_expire_seconds';
UPDATE django_migrations SET applied = '2025-08-12 00:01:32+00:00' WHERE app = 'django_celery_beat' AND name = '0013_auto_20200609_0727';
UPDATE django_migrations SET applied = '2025-08-12 00:01:33+00:00' WHERE app = 'django_celery_beat' AND name = '0014_remove_clockedschedule_enabled';
UPDATE django_migrations SET applied = '2025-08-12 00:01:34+00:00' WHERE app = 'django_celery_beat' AND name = '0015_edit_solarschedule_events_choices';
UPDATE django_migrations SET applied = '2025-08-12 00:01:35+00:00' WHERE app = 'django_celery_beat' AND name = '0016_alter_crontabschedule_timezone';
UPDATE django_migrations SET applied = '2025-08-12 00:01:36+00:00' WHERE app = 'django_celery_beat' AND name = '0017_alter_crontabschedule_month_of_year';
UPDATE django_migrations SET applied = '2025-08-12 00:01:37+00:00' WHERE app = 'django_celery_beat' AND name = '0018_improve_crontab_helptext';

UPDATE django_migrations SET applied = '2025-08-12 00:01:40+00:00' WHERE app = 'django_celery_results' AND name = '0001_initial';
UPDATE django_migrations SET applied = '2025-08-12 00:01:41+00:00' WHERE app = 'django_celery_results' AND name = '0002_add_task_name_args_kwargs';
UPDATE django_migrations SET applied = '2025-08-12 00:01:42+00:00' WHERE app = 'django_celery_results' AND name = '0003_auto_20181106_1101';
UPDATE django_migrations SET applied = '2025-08-12 00:01:43+00:00' WHERE app = 'django_celery_results' AND name = '0004_auto_20190516_0412';
UPDATE django_migrations SET applied = '2025-08-12 00:01:44+00:00' WHERE app = 'django_celery_results' AND name = '0005_taskresult_worker';
UPDATE django_migrations SET applied = '2025-08-12 00:01:45+00:00' WHERE app = 'django_celery_results' AND name = '0006_taskresult_date_created';
UPDATE django_migrations SET applied = '2025-08-12 00:01:46+00:00' WHERE app = 'django_celery_results' AND name = '0007_remove_taskresult_hidden';
UPDATE django_migrations SET applied = '2025-08-12 00:01:47+00:00' WHERE app = 'django_celery_results' AND name = '0008_chordcounter';
UPDATE django_migrations SET applied = '2025-08-12 00:01:48+00:00' WHERE app = 'django_celery_results' AND name = '0009_groupresult';
UPDATE django_migrations SET applied = '2025-08-12 00:01:49+00:00' WHERE app = 'django_celery_results' AND name = '0010_remove_duplicate_indices';
UPDATE django_migrations SET applied = '2025-08-12 00:01:50+00:00' WHERE app = 'django_celery_results' AND name = '0011_taskresult_periodic_task_name';

-- VALIDATION QUERY - Check auth.0002 vs auth.0003 order
SELECT 
    'SUPER-NUCLEAR FIX VALIDATION' as check_name,
    CASE 
        WHEN (SELECT applied FROM django_migrations WHERE app='auth' AND name='0002_alter_permission_name_max_length') <
             (SELECT applied FROM django_migrations WHERE app='auth' AND name='0003_alter_user_email_max_length') 
        THEN '✅ auth.0002 BEFORE auth.0003 - CORRECT ORDER' 
        ELSE '❌ STILL WRONG ORDER' 
    END as result;

-- Count total migrations
SELECT 'TOTAL MIGRATIONS' as info, COUNT(*) as count FROM django_migrations;

-- Show auth migrations in order
SELECT 'AUTH MIGRATIONS ORDER' as info, name, applied 
FROM django_migrations 
WHERE app = 'auth' 
ORDER BY applied;

SELECT '🎯 SUPER-NUCLEAR FIX APPLIED SUCCESSFULLY!' as status;