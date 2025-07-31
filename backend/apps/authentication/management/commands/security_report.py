"""
Management command to generate security reports
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.authentication.models_enhanced import EnhancedUser, AuthenticationAuditLog, SecurityEvent
from apps.authentication.security.audit_logger import security_reporter
import json


class Command(BaseCommand):
    help = 'Generate security reports for authentication system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Generate report for specific user email',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to include in report (default: 7)',
        )
        parser.add_argument(
            '--format',
            choices=['json', 'text', 'csv'],
            default='text',
            help='Output format (default: text)',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (default: stdout)',
        )
        parser.add_argument(
            '--system',
            action='store_true',
            help='Generate system-wide security report',
        )
    
    def handle(self, *args, **options):
        user_email = options['user_email']
        days = options['days']
        output_format = options['format']
        output_file = options['output']
        system_report = options['system']
        
        if system_report:
            report = self.generate_system_report(days)
        elif user_email:
            report = self.generate_user_report(user_email, days)
        else:
            self.stderr.write('Please specify --user-email or --system')
            return
        
        # Format output
        if output_format == 'json':
            output = json.dumps(report, indent=2, default=str)
        elif output_format == 'csv':
            output = self.format_as_csv(report)
        else:
            output = self.format_as_text(report)
        
        # Write output
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            self.stdout.write(f'Report written to {output_file}')
        else:
            self.stdout.write(output)
    
    def generate_user_report(self, email, days):
        """Generate security report for specific user"""
        try:
            user = EnhancedUser.objects.get(email=email)
        except EnhancedUser.DoesNotExist:
            self.stderr.write(f'User with email {email} not found')
            return {}
        
        return security_reporter.generate_user_security_report(user, days)
    
    def generate_system_report(self, days):
        """Generate system-wide security report"""
        return security_reporter.generate_system_security_report(days)
    
    def format_as_text(self, report):
        """Format report as readable text"""
        output = []
        
        if 'user' in report:
            # User report
            user = report['user']
            stats = report['statistics']
            period = report['period']
            
            output.append("=" * 60)
            output.append(f"SECURITY REPORT FOR {user['name']} ({user['email']})")
            output.append("=" * 60)
            output.append(f"Period: {period['start_date']} to {period['end_date']} ({period['days']} days)")
            output.append("")
            
            output.append("STATISTICS:")
            output.append(f"  Total Events: {stats['total_events']}")
            output.append(f"  Successful Logins: {stats['successful_logins']}")
            output.append(f"  Failed Logins: {stats['failed_logins']}")
            output.append(f"  High Risk Events: {stats['high_risk_events']}")
            output.append(f"  Unique Countries: {stats['unique_countries']}")
            output.append(f"  Unique IP Addresses: {stats['unique_ip_addresses']}")
            output.append("")
            
            output.append("RISK ASSESSMENT:")
            risk = report['risk_assessment']
            output.append(f"  Average Risk Score: {risk['average_risk_score']:.2f}")
            output.append(f"  Maximum Risk Score: {risk['max_risk_score']:.2f}")
            output.append("")
            
            if report['security_events']:
                output.append("RECENT SECURITY EVENTS:")
                for event in report['security_events']:
                    output.append(f"  [{event['severity'].upper()}] {event['event_type']} - {event['timestamp']}")
                    if not event['resolved']:
                        output.append("    ⚠️  UNRESOLVED")
                output.append("")
            
            if report['locations']:
                output.append(f"LOCATIONS: {', '.join(report['locations'])}")
                output.append("")
            
            if report['recommendations']:
                output.append("RECOMMENDATIONS:")
                for rec in report['recommendations']:
                    output.append(f"  • {rec}")
        
        else:
            # System report
            stats = report['statistics']
            period = report['period']
            
            output.append("=" * 60)
            output.append("SYSTEM-WIDE SECURITY REPORT")
            output.append("=" * 60)
            output.append(f"Period: {period['start_date']} to {period['end_date']} ({period['days']} days)")
            output.append("")
            
            output.append("STATISTICS:")
            output.append(f"  Total Events: {stats['total_events']}")
            output.append(f"  Failed Logins: {stats['failed_logins']}")
            output.append(f"  High Risk Events: {stats['high_risk_events']}")
            output.append("")
            
            if 'security_events_by_severity' in stats:
                output.append("SECURITY EVENTS BY SEVERITY:")
                for severity, count in stats['security_events_by_severity'].items():
                    output.append(f"  {severity.capitalize()}: {count}")
                output.append("")
            
            if 'threats' in report and report['threats']['top_attacking_ips']:
                output.append("TOP ATTACKING IP ADDRESSES:")
                for ip_info in report['threats']['top_attacking_ips']:
                    output.append(f"  {ip_info['ip_address']}: {ip_info['attempt_count']} attempts")
                output.append("")
            
            if report['recommendations']:
                output.append("RECOMMENDATIONS:")
                for rec in report['recommendations']:
                    output.append(f"  • {rec}")
        
        return "\n".join(output)
    
    def format_as_csv(self, report):
        """Format report as CSV"""
        # This is a simplified CSV format
        # In production, you might want more detailed CSV formatting
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        if 'user' in report:
            # User report CSV
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['User Email', report['user']['email']])
            writer.writerow(['User Name', report['user']['name']])
            writer.writerow(['Period Days', report['period']['days']])
            
            stats = report['statistics']
            writer.writerow(['Total Events', stats['total_events']])
            writer.writerow(['Successful Logins', stats['successful_logins']])
            writer.writerow(['Failed Logins', stats['failed_logins']])
            writer.writerow(['High Risk Events', stats['high_risk_events']])
            writer.writerow(['Unique Countries', stats['unique_countries']])
            writer.writerow(['Unique IP Addresses', stats['unique_ip_addresses']])
        
        else:
            # System report CSV
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Period Days', report['period']['days']])
            
            stats = report['statistics']
            writer.writerow(['Total Events', stats['total_events']])
            writer.writerow(['Failed Logins', stats['failed_logins']])
            writer.writerow(['High Risk Events', stats['high_risk_events']])
        
        return output.getvalue()
    
    def get_summary_stats(self):
        """Get overall system statistics"""
        total_users = EnhancedUser.objects.count()
        active_users = EnhancedUser.objects.filter(is_active=True).count()
        verified_users = EnhancedUser.objects.filter(is_email_verified=True).count()
        two_fa_users = EnhancedUser.objects.filter(is_two_factor_enabled=True).count()
        locked_users = EnhancedUser.objects.filter(is_locked=True).count()
        
        # Recent activity (last 24 hours)
        yesterday = timezone.now() - timezone.timedelta(days=1)
        recent_logins = AuthenticationAuditLog.objects.filter(
            event_type='login_success',
            timestamp__gte=yesterday
        ).count()
        
        recent_failures = AuthenticationAuditLog.objects.filter(
            event_type='login_failure',
            timestamp__gte=yesterday
        ).count()
        
        unresolved_events = SecurityEvent.objects.filter(resolved=False).count()
        
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("SYSTEM SUMMARY")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Total Users: {total_users}")
        self.stdout.write(f"Active Users: {active_users}")
        self.stdout.write(f"Email Verified: {verified_users}")
        self.stdout.write(f"2FA Enabled: {two_fa_users}")
        self.stdout.write(f"Locked Accounts: {locked_users}")
        self.stdout.write(f"Recent Logins (24h): {recent_logins}")
        self.stdout.write(f"Recent Failures (24h): {recent_failures}")
        self.stdout.write(f"Unresolved Security Events: {unresolved_events}")
        self.stdout.write("=" * 50)