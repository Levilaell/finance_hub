#!/usr/bin/env python
"""
Script to create default report templates in production
Run with: python manage.py shell < create_report_templates.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.reports.models import ReportTemplate
from apps.companies.models import Company
from apps.authentication.models import User

print('=== CREATING DEFAULT REPORT TEMPLATES ===')

# Get a user with company for template creation (or use superuser)
user_with_company = User.objects.filter(company__isnull=False).first()
if not user_with_company:
    # Try to find a superuser
    user_with_company = User.objects.filter(is_superuser=True).first()
    if user_with_company and not hasattr(user_with_company, 'company'):
        # Create a default company for superuser
        company = Company.objects.create(
            name='Sistema',
            cnpj='00.000.000/0000-00',
            subscription_status='active'
        )
        user_with_company.company = company
        user_with_company.save()

if not user_with_company:
    print('❌ No suitable user found for template creation')
    exit(1)

company = user_with_company.company
print(f'Using company: {company.name}')

# Template configurations
templates_config = [
    {
        'name': 'DRE - Demonstração de Resultados',
        'description': 'Relatório completo de receitas e despesas por período',
        'report_type': 'profit_loss',
        'template_config': {
            'sections': ['summary', 'income', 'expenses', 'net_result'],
            'details_level': 'detailed'
        },
        'charts': [
            {'type': 'bar', 'title': 'Receitas vs Despesas', 'data_source': 'income_expenses'},
            {'type': 'pie', 'title': 'Distribuição por Categoria', 'data_source': 'categories'}
        ],
        'default_parameters': {
            'include_charts': True,
            'detailed_breakdown': True,
            'group_by_category': True
        },
        'default_filters': {
            'include_transfers': False,
            'min_amount': 0
        },
        'is_public': True,
        'is_active': True
    },
    {
        'name': 'Fluxo de Caixa',
        'description': 'Análise do fluxo de entrada e saída de recursos',
        'report_type': 'cash_flow',
        'template_config': {
            'sections': ['inflow', 'outflow', 'net_flow', 'balance'],
            'period_grouping': 'monthly'
        },
        'charts': [
            {'type': 'line', 'title': 'Fluxo de Caixa Mensal', 'data_source': 'monthly_flow'},
            {'type': 'area', 'title': 'Evolução do Saldo', 'data_source': 'balance_evolution'}
        ],
        'default_parameters': {
            'include_projections': False,
            'show_daily_breakdown': False,
            'include_pending': False
        },
        'default_filters': {
            'account_types': ['checking', 'savings'],
            'exclude_internal': True
        },
        'is_public': True,
        'is_active': True
    },
    {
        'name': 'Resumo Mensal',
        'description': 'Resumo executivo das movimentações mensais',
        'report_type': 'monthly_summary',
        'template_config': {
            'sections': ['overview', 'highlights', 'trends'],
            'summary_level': 'executive'
        },
        'charts': [
            {'type': 'bar', 'title': 'Receitas vs Despesas', 'data_source': 'income_vs_expenses'},
            {'type': 'pie', 'title': 'Top Categorias', 'data_source': 'top_categories'}
        ],
        'default_parameters': {
            'include_comparisons': True,
            'show_trends': True,
            'highlight_anomalies': True
        },
        'default_filters': {
            'exclude_small_amounts': True,
            'min_amount': 10
        },
        'is_public': True,
        'is_active': True
    },
    {
        'name': 'Análise por Categoria',
        'description': 'Detalhamento das movimentações agrupadas por categoria',
        'report_type': 'category_analysis',
        'template_config': {
            'sections': ['category_summary', 'detailed_breakdown', 'comparisons'],
            'analysis_depth': 'deep'
        },
        'charts': [
            {'type': 'pie', 'title': 'Distribuição por Categoria', 'data_source': 'category_pie'},
            {'type': 'line', 'title': 'Tendências por Categoria', 'data_source': 'category_trends'}
        ],
        'default_parameters': {
            'include_subcategories': True,
            'show_percentages': True,
            'compare_periods': True
        },
        'default_filters': {
            'exclude_transfers': True,
            'min_category_amount': 50
        },
        'is_public': True,
        'is_active': True
    }
]

created_count = 0
updated_count = 0

for template_data in templates_config:
    template_name = template_data['name']
    template_type = template_data['report_type']
    
    # Check if template already exists
    existing = ReportTemplate.objects.filter(
        name=template_name,
        report_type=template_type
    ).first()
    
    if existing:
        # Update existing template
        for key, value in template_data.items():
            if key not in ['name', 'report_type']:
                setattr(existing, key, value)
        try:
            existing.save()
            print(f'✅ Updated template: {template_name}')
            updated_count += 1
        except Exception as e:
            print(f'❌ Failed to update {template_name}: {str(e)}')
        continue
    
    try:
        # Create new template
        template = ReportTemplate.objects.create(
            company=company,
            created_by=user_with_company,
            **template_data
        )
        
        print(f'✅ Created template: {template.name}')
        created_count += 1
    except Exception as e:
        print(f'❌ Failed to create {template_name}: {str(e)}')

print(f'\n=== SUMMARY ===')
print(f'Created {created_count} new templates')
print(f'Updated {updated_count} existing templates')
print(f'Total templates: {ReportTemplate.objects.count()}')

# List all active public templates
print('\n=== PUBLIC TEMPLATES ===')
for template in ReportTemplate.objects.filter(is_public=True, is_active=True):
    print(f'- {template.name} ({template.report_type})')

print('\n✅ Script completed successfully')