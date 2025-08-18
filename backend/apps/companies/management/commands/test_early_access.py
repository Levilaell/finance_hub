"""
Test early access system functionality
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.companies.models import EarlyAccessInvite, Company
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Test early access system functionality'
    
    def handle(self, *args, **options):
        self.stdout.write("🧪 Testing Early Access System...")
        self.stdout.write("")
        
        # Test 1: Check invites
        self._test_invites()
        
        # Test 2: Check companies with early access
        self._test_companies()
        
        # Test 3: Summary
        self._show_summary()
        
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("✅ Early Access System Test Complete!"))
    
    def _test_invites(self):
        self.stdout.write("📋 Testing Invites:")
        
        invites = EarlyAccessInvite.objects.all()
        if not invites:
            self.stdout.write("   ❌ No invites found. Run: python manage.py create_early_access_invites --count 5 --expires-date '2025-12-31'")
            return
        
        for invite in invites[:5]:  # Show first 5
            status = "🟢 Available" if not invite.is_used else "🟠 Used"
            days = invite.days_until_expiry
            expires = invite.expires_at.strftime('%Y-%m-%d')
            
            self.stdout.write(f"   • {invite.invite_code}: {status} (expires {expires}, {days} days left)")
            
            # Test validation
            if invite.is_valid:
                self.stdout.write(f"     ✅ Validation: Valid")
            else:
                reason = "Used" if invite.is_used else "Expired"
                self.stdout.write(f"     ❌ Validation: Invalid ({reason})")
        
        total = invites.count()
        available = invites.filter(is_used=False).count()
        used = invites.filter(is_used=True).count()
        
        self.stdout.write(f"   📊 Total: {total} | Available: {available} | Used: {used}")
        self.stdout.write("")
    
    def _test_companies(self):
        self.stdout.write("🏢 Testing Companies:")
        
        early_access_companies = Company.objects.filter(is_early_access=True)
        
        if not early_access_companies:
            self.stdout.write("   ℹ️  No early access companies yet")
            self.stdout.write("")
            return
        
        for company in early_access_companies[:5]:  # Show first 5
            days = company.days_until_trial_ends
            status = "🟢 Active" if company.is_early_access_active else "🔴 Expired"
            
            self.stdout.write(f"   • {company.name} ({company.owner.email})")
            self.stdout.write(f"     Status: {status}")
            self.stdout.write(f"     Code used: {company.used_invite_code}")
            self.stdout.write(f"     Days left: {days}")
            self.stdout.write(f"     Expires: {company.early_access_expires_at.strftime('%Y-%m-%d %H:%M')}")
            
        self.stdout.write(f"   📊 Total Early Access Companies: {early_access_companies.count()}")
        self.stdout.write("")
    
    def _show_summary(self):
        self.stdout.write("📈 System Summary:")
        
        total_invites = EarlyAccessInvite.objects.count()
        available_invites = EarlyAccessInvite.objects.filter(is_used=False).count()
        used_invites = EarlyAccessInvite.objects.filter(is_used=True).count()
        
        total_companies = Company.objects.count()
        early_access_companies = Company.objects.filter(is_early_access=True).count()
        active_early_access = Company.objects.filter(
            is_early_access=True,
            early_access_expires_at__gt=timezone.now()
        ).count()
        
        self.stdout.write(f"   📋 Invites: {total_invites} total, {available_invites} available, {used_invites} used")
        self.stdout.write(f"   🏢 Companies: {total_companies} total, {early_access_companies} early access, {active_early_access} active early access")
        
        if available_invites > 0:
            sample_code = EarlyAccessInvite.objects.filter(is_used=False).first().invite_code
            self.stdout.write("")
            self.stdout.write("🔗 Test Registration:")
            self.stdout.write(f"   URL: http://localhost:3000/early-access?code={sample_code}")
            self.stdout.write(f"   API: POST /api/auth/early-access/register/ with invite_code: {sample_code}")
        
        self.stdout.write("")
        self.stdout.write("🎛️  Admin Panel:")
        self.stdout.write("   URL: http://localhost:8000/admin/companies/earlyaccessinvite/")
        self.stdout.write("   View and manage all invites and early access users")