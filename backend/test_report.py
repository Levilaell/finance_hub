#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.reports.report_generator import ReportGenerator
from apps.companies.models import Company
from datetime import datetime, timedelta
import json

# Get the first company
company = Company.objects.first()
if not company:
    print('No company found')
    sys.exit(1)

generator = ReportGenerator(company)
end_date = datetime.now().date()
start_date = end_date - timedelta(days=30)

# Generate a category analysis report in PDF format
print(f"Generating report for company: {company.name}")
print(f"Period: {start_date} to {end_date}")

buffer = generator.generate_category_analysis_report(
    start_date=start_date,
    end_date=end_date,
    format='pdf',
    filters=None
)

# Save the PDF for inspection
buffer.seek(0)
content = buffer.read()

output_path = '/tmp/test_category_report.pdf'
with open(output_path, 'wb') as f:
    f.write(content)

print(f"\n✓ Report generated successfully!")
print(f"  - Size: {len(content):,} bytes")
print(f"  - Saved to: {output_path}")

# Also test that we get the report data correctly
# Let's check if there's a method to get just the data
print("\n=== CHECKING REPORT DATA ===")

# Re-read the file to check current implementation
import importlib
import inspect

# Get the method source to understand better
method = generator.generate_category_analysis_report
print(f"Method signature: {inspect.signature(method)}")