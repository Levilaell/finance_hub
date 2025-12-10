"""
Signal handlers for authentication events
"""
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserActivityLog, UserSettings, User


def get_client_ip(request):
    """
    Extract client IP address from request, considering proxies
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Log user login events (excluding admin logins)
    """
    # Skip logging for admin logins
    if request.path.startswith('/admin'):
        # Only update IP, don't log the event
        user.last_login_ip = get_client_ip(request)
        user.save(update_fields=['last_login_ip'])
        return

    UserActivityLog.log_event(
        user=user,
        event_type='login',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )

    # Update last_login_ip on User model
    user.last_login_ip = get_client_ip(request)
    user.save(update_fields=['last_login_ip'])


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Log user logout events (excluding admin logouts)
    """
    # Skip logging for admin logouts
    if request.path.startswith('/admin'):
        return

    if user:  # user can be None if not authenticated
        UserActivityLog.log_event(
            user=user,
            event_type='logout',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )


@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    """
    Create UserSettings automatically when a new user is created.
    """
    if created:
        UserSettings.objects.create(user=instance)
