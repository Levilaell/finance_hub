# Report Generation 500 Error - Root Cause Analysis and Fixes

## Issues Found and Fixed

### 1. Missing Module Imports in error_handlers.py
- **Issue**: `timezone` and `uuid` were used but not imported
- **Fix**: Added imports for `timezone` from `django.utils` and `uuid`
- **File**: `/backend/core/error_handlers.py`

### 2. Missing Default Value for file_format Field
- **Issue**: Report model's `file_format` field had no default value
- **Fix**: Added `default='pdf'` to the field definition
- **File**: `/backend/apps/reports/models.py`
- **Migration**: Created and applied migration `0003_add_file_format_default`

### 3. Non-existent Model Fields in tasks.py
- **Issue**: Code referenced `report.status` and `report.format` fields that don't exist
- **Fix**: 
  - Replaced `report.status` with `report.is_generated`
  - Replaced `report.format` with `report.file_format`
  - Removed references to non-existent fields like `completed_at`
- **File**: `/backend/apps/reports/tasks.py`

### 4. Incorrect Model Relationships
- **Issue**: `Transaction.objects.filter(company=self.company)` but Transaction doesn't have a direct company field
- **Fix**: Changed to `Transaction.objects.filter(bank_account__company=self.company)`
- **File**: `/backend/apps/reports/report_generator.py`

### 5. Wrong Import Path
- **Issue**: Importing `Category` from `apps.categories.models` when it should be `TransactionCategory` from `apps.banking.models`
- **Fix**: Updated import statement
- **File**: `/backend/apps/reports/report_generator.py`

### 6. Report Type Mismatches
- **Issue**: 
  - View used 'quarterly' and 'annual' but model expected 'quarterly_report' and 'annual_report'
  - tasks.py checked for 'transaction_report' and 'account_statement' which don't exist in model choices
- **Fix**: 
  - Updated view to use correct report type values
  - Simplified task to use transaction report generator for all report types
- **Files**: `/backend/apps/reports/views.py`, `/backend/apps/reports/tasks.py`

### 7. Missing Python Dependencies
- **Issue**: `xlsxwriter` module was not installed despite being in requirements.txt
- **Fix**: Installed xlsxwriter using pip

### 8. Non-existent ReportSchedule Fields
- **Issue**: Code referenced `is_due()`, `last_run_date`, and `run_count` which don't exist
- **Fix**: 
  - Replaced `is_due()` with direct comparison of `next_run_at`
  - Changed `last_run_date` to `last_run_at`
  - Removed `run_count` references
- **File**: `/backend/apps/reports/tasks.py`

## Testing Results

After applying all fixes:
- Report creation via API endpoint works correctly
- Report generation task executes successfully
- PDF reports are generated without errors
- Email notifications are sent correctly
- No 500 errors occur

## Recommendations

1. **Add Tests**: Create comprehensive tests for the reports app to catch these issues early
2. **Update Dependencies**: Ensure all Python packages in requirements.txt are installed in the environment
3. **Model Validation**: Add model validation to ensure required fields have proper defaults
4. **Error Logging**: The error handling is now properly configured to log detailed errors
5. **Code Review**: Review other apps for similar issues with missing imports or field references

## Commands to Apply Fixes

```bash
# Install missing dependencies
pip install xlsxwriter reportlab

# Apply migrations
python manage.py migrate reports

# Restart the application
python manage.py runserver
```

The 500 error on POST `/api/reports/reports/` should now be resolved.