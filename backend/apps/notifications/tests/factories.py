"""
Factory classes for notification tests
"""
from django.contrib.auth import get_user_model
from apps.companies.models import Company
from apps.notifications.models import Notification

User = get_user_model()


def create_test_company(name="Test Company", owner=None):
    """Create a test company with all required fields"""
    if not owner:
        owner = User.objects.create_user(
            email=f"{name.lower().replace(' ', '_')}@example.com",
            username=f"{name.lower().replace(' ', '_')}",
            password="testpass123"
        )
    
    company_data = {
        'name': name,
        'owner': owner,
    }
    
    # Check if this is the old schema with additional required fields
    try:
        # Try to create with minimal fields first
        company = Company.objects.create(**company_data)
        return company, owner
    except Exception:
        # If that fails, add all the legacy required fields
        company_data.update({
            'trade_name': f"{name} Trade",
            'company_type': 'other',
            'business_sector': 'other',
            'document_number': '12345678901234',
        })
    
    # Create the company
    company = Company.objects.create(**company_data)
    return company, owner


def create_test_notification(company, user, event='report_ready', **kwargs):
    """Create a test notification with proper event_key"""
    import uuid
    
    defaults = {
        'company': company,
        'user': user,
        'event': event,
        'event_key': f"{event}:{company.id}:{user.id}:{uuid.uuid4().hex[:8]}",
        'title': kwargs.get('title', f'{event.replace("_", " ").title()}'),
        'message': kwargs.get('message', f'Test message for {event}'),
        'is_critical': event in ['payment_failed', 'account_sync_failed', 'low_balance', 'security_alert'],
    }
    
    # Update with any provided kwargs
    defaults.update(kwargs)
    
    return Notification.objects.create(**defaults)