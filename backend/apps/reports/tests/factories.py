"""
Test factories for reports app - imports from companies app factories
"""
# Import all factories from companies app
from apps.companies.tests.factories import (
    UserFactory,
    CompanyFactory, 
    SubscriptionPlanFactory,
    BasicPlanFactory,
    PremiumPlanFactory,
    EnterprisePlanFactory,
    TrialCompanyFactory,
    ActiveCompanyFactory,
    ResourceUsageFactory
)

# Import other needed factories
from apps.banking.tests.factories import BankAccountFactory, TransactionFactory
from apps.categories.tests.factories import CategoryFactory

# Reports-specific factories
import factory
from datetime import timedelta
from django.utils import timezone
from apps.reports.models import Report, ReportTemplate

class ReportFactory(factory.django.DjangoModelFactory):
    """Factory for creating Report instances"""
    
    class Meta:
        model = Report
    
    company = factory.SubFactory(CompanyFactory)
    report_type = factory.Iterator([
        'monthly_summary',
        'cash_flow', 
        'profit_loss',
        'category_analysis'
    ])
    
    title = factory.LazyAttribute(
        lambda obj: f"{obj.report_type.replace('_', ' ').title()} Report"
    )
    
    description = factory.LazyAttribute(
        lambda obj: f"Test {obj.report_type} report"
    )
    
    period_start = factory.LazyFunction(
        lambda: timezone.now().date().replace(day=1)
    )
    
    period_end = factory.LazyAttribute(
        lambda obj: obj.period_start.replace(day=28) + timedelta(days=4)
    )
    
    file_format = 'pdf'
    is_generated = False
    
    created_by = factory.SubFactory(UserFactory)


class ReportTemplateFactory(factory.django.DjangoModelFactory):
    """Factory for creating ReportTemplate instances"""
    
    class Meta:
        model = ReportTemplate
    
    company = factory.SubFactory(CompanyFactory)
    name = factory.Iterator([
        'Monthly Summary Template',
        'Cash Flow Template',
        'Profit Loss Template'
    ])
    
    report_type = 'monthly_summary'
    is_active = True
    
    created_by = factory.SubFactory(UserFactory)


# Helper function for test data
def create_test_company_with_subscription(plan_type="premium"):
    """Create a company with proper subscription setup"""
    if plan_type == "premium":
        plan_factory = PremiumPlanFactory
    elif plan_type == "enterprise":
        plan_factory = EnterprisePlanFactory
    else:
        plan_factory = BasicPlanFactory
        
    subscription_plan = plan_factory()
    company = CompanyFactory(
        subscription_plan=subscription_plan,
        subscription_status='active'
    )
    
    return company, subscription_plan
