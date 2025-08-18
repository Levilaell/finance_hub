"""
Create early access invites for MVP testing
"""
import secrets
import string
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.companies.models import EarlyAccessInvite

User = get_user_model()


class Command(BaseCommand):
    help = 'Create early access invites for MVP testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=25,
            help='Number of invite codes to generate (default: 25)'
        )
        parser.add_argument(
            '--expires-date',
            type=str,
            required=True,
            help='Expiration date in YYYY-MM-DD format (e.g., 2025-06-30)'
        )
        parser.add_argument(
            '--prefix',
            type=str,
            default='MVP',
            help='Prefix for invite codes (default: MVP)'
        )
        parser.add_argument(
            '--save-to-file',
            action='store_true',
            help='Save generated codes to a text file'
        )
    
    def handle(self, *args, **options):
        count = options['count']
        expires_date_str = options['expires_date']
        prefix = options['prefix']
        save_to_file = options['save_to_file']
        
        # Parse expiration date
        try:
            expires_date = datetime.strptime(expires_date_str, '%Y-%m-%d')
            # Set to end of day
            expires_date = expires_date.replace(hour=23, minute=59, second=59)
            expires_date = timezone.make_aware(expires_date)
        except ValueError:
            raise CommandError(
                f"Invalid date format: {expires_date_str}. "
                "Use YYYY-MM-DD format (e.g., 2025-06-30)"
            )
        
        # Check if date is in the future
        if expires_date <= timezone.now():
            raise CommandError("Expiration date must be in the future")
        
        # Get admin user (first superuser)
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.first()  # Fallback to first user
            if not admin_user:
                raise CommandError("No users found in database")
        except Exception as e:
            raise CommandError(f"Error finding admin user: {e}")
        
        self.stdout.write(f"Creating {count} invite codes...")
        self.stdout.write(f"Expiration date: {expires_date.strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"Days until expiry: {(expires_date - timezone.now()).days}")
        self.stdout.write("")
        
        generated_codes = []
        
        for i in range(count):
            # Generate unique invite code
            code = self.generate_unique_code(prefix)
            
            # Create invite
            invite = EarlyAccessInvite.objects.create(
                invite_code=code,
                expires_at=expires_date,
                created_by=admin_user,
                notes=f'MVP test invite #{i+1} - Generated on {timezone.now().date()}'
            )
            
            generated_codes.append(code)
            self.stdout.write(f"✅ Created: {code}")
        
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(generated_codes)} invite codes!"))
        
        # Save to file if requested
        if save_to_file:
            filename = f"early_access_codes_{timezone.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write(f"Early Access Invite Codes\n")
                f.write(f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Expires: {expires_date.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Count: {len(generated_codes)}\n")
                f.write("-" * 40 + "\n")
                
                for code in generated_codes:
                    f.write(f"{code}\n")
            
            self.stdout.write(f"📄 Codes saved to: {filename}")
        
        # Show summary
        self.stdout.write("")
        self.stdout.write("📊 Summary:")
        self.stdout.write(f"   • Total codes: {len(generated_codes)}")
        self.stdout.write(f"   • Expires: {expires_date.strftime('%Y-%m-%d')}")
        self.stdout.write(f"   • Days valid: {(expires_date - timezone.now()).days}")
        self.stdout.write("")
        self.stdout.write("🔗 Example usage:")
        self.stdout.write(f"   https://yourdomain.com/early-access?code={generated_codes[0]}")
        
        if save_to_file:
            self.stdout.write("")
            self.stdout.write("💡 Next steps:")
            self.stdout.write("   1. Share the generated codes with your MVP testers")
            self.stdout.write("   2. Send them the link: /early-access?code=CODE")
            self.stdout.write("   3. Monitor usage via Django admin")
    
    def generate_unique_code(self, prefix):
        """Generate a unique invite code"""
        max_attempts = 100
        
        for _ in range(max_attempts):
            # Generate random part (8 characters)
            random_part = ''.join(
                secrets.choice(string.ascii_uppercase + string.digits) 
                for _ in range(8)
            )
            code = f"{prefix}-{random_part}"
            
            # Check if code already exists
            if not EarlyAccessInvite.objects.filter(invite_code=code).exists():
                return code
        
        raise CommandError("Failed to generate unique invite code after 100 attempts")