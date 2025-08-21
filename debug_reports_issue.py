#!/usr/bin/env python
"""
Debug script for reports loading issue
Run this in production to diagnose the exact problem
"""

import os
import django
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

User = get_user_model()

def debug_reports_issue():
    print("🔍 DEBUGGING REPORTS ISSUE")
    print("=" * 50)
    
    # Find the user with the email you're using
    email = "arabel.bebel@hotmail.com"  # Your email from the previous message
    
    try:
        user = User.objects.get(email=email)
        print(f"✅ User found: {user.email}")
    except User.DoesNotExist:
        print(f"❌ User with email {email} not found")
        return
    
    # Check company
    if hasattr(user, 'company') and user.company:
        company = user.company
        print(f"✅ Company: {company.name} (ID: {company.id})")
        print(f"📋 Plan: {company.subscription_plan.name if company.subscription_plan else 'None'}")
        print(f"📊 Status: {company.subscription_status}")
        
        if company.subscription_plan:
            print(f"🔧 has_advanced_reports: {company.subscription_plan.has_advanced_reports}")
        
    else:
        print("❌ User has no company associated")
        return
    
    # Check Reports
    from apps.reports.models import Report
    print("\n📊 REPORTS ANALYSIS")
    print("-" * 30)
    
    all_reports = Report.objects.all()
    company_reports = Report.objects.filter(company=company)
    
    print(f"Total reports in DB: {all_reports.count()}")
    print(f"Reports for your company: {company_reports.count()}")
    
    if company_reports.exists():
        print("Your company's reports:")
        for report in company_reports[:5]:
            print(f"  - {report.title} ({report.report_type}) - {report.created_at}")
    
    # Check ReportTemplates
    from apps.reports.models import ReportTemplate
    print("\n📋 REPORT TEMPLATES ANALYSIS")
    print("-" * 30)
    
    all_templates = ReportTemplate.objects.all()
    public_templates = ReportTemplate.objects.filter(is_public=True, is_active=True)
    company_templates = ReportTemplate.objects.filter(company=company, is_active=True)
    
    print(f"Total templates in DB: {all_templates.count()}")
    print(f"Public templates: {public_templates.count()}")
    print(f"Your company templates: {company_templates.count()}")
    
    # Test the exact queryset used by ReportViewSet
    print("\n🔍 TESTING REPORTVIEWSET QUERYSET")
    print("-" * 30)
    
    queryset = Report.objects.filter(company=company).select_related(
        'created_by', 'company', 'company__subscription'
    ).order_by('-created_at')
    
    print(f"ReportViewSet queryset count: {queryset.count()}")
    
    # Test the exact queryset used by ReportTemplateViewSet  
    print("\n🔍 TESTING REPORTTEMPLATEVIEWSET QUERYSET")
    print("-" * 30)
    
    if company:
        template_queryset = ReportTemplate.objects.filter(
            Q(company=company) | Q(is_public=True),
            is_active=True
        ).select_related('company', 'created_by').order_by('name')
    else:
        template_queryset = ReportTemplate.objects.filter(
            is_public=True, is_active=True
        ).select_related('company', 'created_by').order_by('name')
    
    from django.db.models import Q
    print(f"ReportTemplateViewSet queryset count: {template_queryset.count()}")
    
    if template_queryset.exists():
        print("Available templates:")
        for template in template_queryset:
            visibility = "Public" if template.is_public else f"Company: {template.company.name}"
            print(f"  - {template.name} ({visibility})")
    
    # Test subscription plan features
    print("\n💳 SUBSCRIPTION PLAN ANALYSIS")
    print("-" * 30)
    
    if company.subscription_plan:
        plan = company.subscription_plan
        print(f"Plan name: {plan.name}")
        print(f"Plan type: {plan.plan_type}")
        print(f"has_advanced_reports: {plan.has_advanced_reports}")
        print(f"max_reports: {getattr(plan, 'max_reports', 'N/A')}")
    else:
        print("❌ No subscription plan assigned")
    
    print("\n✅ Diagnosis complete!")
    print("\nIf templates show 0 count but public_templates > 0,")
    print("there might be an import issue with Q in the views.py")

if __name__ == "__main__":
    debug_reports_issue()