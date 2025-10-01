"""
Subscription models
"""
from django.db import models
from apps.authentication.models import User


class TrialUsageTracking(models.Model):
    """Track if user has already used trial period"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='trial_tracking'
    )
    has_used_trial = models.BooleanField(default=False)
    first_trial_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'trial_usage_tracking'

    def __str__(self):
        return f"{self.user.email} - Trial used: {self.has_used_trial}"
