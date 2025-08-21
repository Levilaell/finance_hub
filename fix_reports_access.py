#!/usr/bin/env python
"""
Fix reports access issue by updating subscription plan
Run this in production if diagnosis shows plan configuration issue
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.contrib.auth import get_user_model
from apps.companies.models import SubscriptionPlan

User = get_user_model()

def fix_reports_access():
    print("🔧 FIXING REPORTS ACCESS")
    print("=" * 40)
    
    email = "arabel.bebel@hotmail.com"
    
    try:
        user = User.objects.get(email=email)
        if not (hasattr(user, 'company') and user.company):
            print("❌ User has no company - cannot fix")
            return
            
        company = user.company
        plan = company.subscription_plan
        
        if not plan:
            print("❌ No subscription plan assigned - cannot fix")
            return
            
        print(f"👤 User: {user.email}")
        print(f"🏢 Company: {company.name}")
        print(f"📋 Current Plan: {plan.name} ({plan.plan_type})")
        print(f"📊 Current has_advanced_reports: {plan.has_advanced_reports}")
        
        # Fix plan configuration
        should_have_advanced_reports = plan.plan_type in ['professional', 'enterprise']
        
        if should_have_advanced_reports and not plan.has_advanced_reports:
            print(f"\n🔧 FIXING: Enabling advanced reports for {plan.plan_type} plan")
            plan.has_advanced_reports = True
            plan.save()
            print("✅ Fixed! Plan now has advanced reports enabled")
            
        elif plan.has_advanced_reports:
            print("✅ Plan already has advanced reports enabled")
            
        else:
            print(f"ℹ️  {plan.plan_type} plan doesn't normally include advanced reports")
            print("   Consider upgrading to Professional or Enterprise")
        
        # Also check if we need to create some default public templates
        from apps.reports.models import ReportTemplate
        
        public_templates = ReportTemplate.objects.filter(is_public=True, is_active=True)
        print(f"\n📋 Public templates available: {public_templates.count()}")
        
        if public_templates.count() == 0:
            print("🔧 Creating default public templates...")
            
            # Create basic public templates
            templates = [
                {
                    'name': 'Relatório Mensal Básico',
                    'description': 'Template público para relatório mensal simples',
                    'report_type': 'monthly_summary',
                    'is_public': True,
                    'is_active': True,
                },
                {
                    'name': 'Fluxo de Caixa Simples',
                    'description': 'Template público para fluxo de caixa',
                    'report_type': 'cash_flow',
                    'is_public': True,
                    'is_active': True,
                }
            ]
            
            for template_data in templates:
                template_data['company'] = company  # Assign to current company but make public
                template = ReportTemplate.objects.create(**template_data)
                print(f"   ✅ Created: {template.name}")
                
        print(f"\n✅ Fix completed!")
        print(f"🔍 Now test the reports page again")
            
    except User.DoesNotExist:
        print(f"❌ User {email} not found")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_reports_access()