"""
Django management command for comprehensive authentication diagnostics
Usage: python manage.py diagnose_auth_issues [--fix] [--output report.json]
"""
import json
import sys
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.authentication.session_diagnostics import SessionCorruptionDiagnostics

class Command(BaseCommand):
    help = 'Comprehensive authentication and session debugging tool'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Output JSON report to specified file'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix common issues automatically'
        )
        parser.add_argument(
            '--check-production',
            action='store_true',
            help='Check if production_fix.py settings are applied'
        )
        parser.add_argument(
            '--quick',
            action='store_true',
            help='Run quick diagnostics only (skip detailed analysis)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Starting Authentication Diagnostics')
        )
        self.stdout.write('=' * 60)
        
        try:
            # Initialize diagnostics
            diagnostics = SessionCorruptionDiagnostics()
            
            if options['quick']:
                results = self._run_quick_diagnostics(diagnostics)
            else:
                results = diagnostics.run_full_diagnostics()
            
            # Display results
            self._display_results(results)
            
            # Check for production fixes
            if options['check_production']:
                self._check_production_fixes()
            
            # Attempt fixes if requested
            if options['fix']:
                self._attempt_fixes(results)
            
            # Save report if requested
            if options['output']:
                self._save_report(results, options['output'])
            
            # Exit with error code if critical issues found
            high_severity_issues = [
                issue for issue in results['issues_found']
                if issue['severity'] == 'HIGH'
            ]
            
            if high_severity_issues:
                self.stdout.write(
                    self.style.ERROR(f'\n❌ Found {len(high_severity_issues)} critical issues')
                )
                sys.exit(1)
            else:
                self.stdout.write(
                    self.style.SUCCESS('\n✅ No critical issues found')
                )
                
        except Exception as e:
            raise CommandError(f'Diagnostics failed: {e}')
    
    def _run_quick_diagnostics(self, diagnostics):
        """Run quick diagnostics for faster feedback"""
        self.stdout.write('Running quick diagnostics...')
        
        # Quick checks only
        diagnostics._check_session_backend()
        diagnostics._check_cache_connectivity()
        diagnostics._check_jwt_token_health()
        diagnostics._generate_recommendations()
        
        return diagnostics.diagnostics_data
    
    def _display_results(self, results):
        """Display diagnostic results in a user-friendly format"""
        
        # Summary
        issues = results['issues_found']
        recommendations = results.get('recommendations', [])
        
        self.stdout.write('\n📊 DIAGNOSTIC SUMMARY')
        self.stdout.write('-' * 30)
        
        if not issues:
            self.stdout.write(self.style.SUCCESS('✅ No issues found'))
        else:
            # Group by severity
            severity_counts = {}
            for issue in issues:
                severity = issue['severity']
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            for severity, count in severity_counts.items():
                color = {
                    'HIGH': self.style.ERROR,
                    'MEDIUM': self.style.WARNING,
                    'LOW': self.style.NOTICE
                }.get(severity, self.style.NOTICE)
                
                self.stdout.write(color(f'{severity}: {count} issues'))
        
        # Detailed issues
        if issues:
            self.stdout.write('\n🔍 DETAILED ISSUES')
            self.stdout.write('-' * 30)
            
            for i, issue in enumerate(issues, 1):
                severity_style = {
                    'HIGH': self.style.ERROR,
                    'MEDIUM': self.style.WARNING,
                    'LOW': self.style.NOTICE
                }.get(issue['severity'], self.style.NOTICE)
                
                self.stdout.write(
                    severity_style(
                        f'{i}. [{issue["severity"]}] {issue["component"]}: {issue["issue"]}'
                    )
                )
                self.stdout.write(f'   Description: {issue["description"]}')
                self.stdout.write('')
        
        # Configuration info
        self.stdout.write('\n⚙️ CURRENT CONFIGURATION')
        self.stdout.write('-' * 30)
        self.stdout.write(f'Session Backend: {results["session_backend"]}')
        self.stdout.write(f'Cache Backend: {results["cache_backend"]}')
        
        jwt_settings = results['jwt_settings']
        self.stdout.write(f'JWT Algorithm: {jwt_settings["algorithm"]}')
        self.stdout.write(f'Token Rotation: {jwt_settings["rotate_refresh_tokens"]}')
        self.stdout.write(f'Blacklist After Rotation: {jwt_settings["blacklist_after_rotation"]}')
        
        # Recommendations
        if recommendations:
            self.stdout.write('\n💡 RECOMMENDATIONS')
            self.stdout.write('-' * 30)
            
            for i, rec in enumerate(recommendations, 1):
                priority_style = {
                    'URGENT': self.style.ERROR,
                    'HIGH': self.style.WARNING,
                    'MEDIUM': self.style.NOTICE
                }.get(rec['priority'], self.style.NOTICE)
                
                self.stdout.write(
                    priority_style(f'{i}. [{rec["priority"]}] {rec["action"]}')
                )
                self.stdout.write(f'   {rec["description"]}')
                
                if 'commands' in rec:
                    self.stdout.write('   Commands:')
                    for cmd in rec['commands']:
                        self.stdout.write(f'     {cmd}')
                self.stdout.write('')
    
    def _check_production_fixes(self):
        """Check if production_fix.py configuration has been applied"""
        self.stdout.write('\n🚀 PRODUCTION FIXES STATUS')
        self.stdout.write('-' * 30)
        
        fixes_applied = []
        fixes_needed = []
        
        # Check session engine
        if settings.SESSION_ENGINE != 'django.contrib.sessions.backends.signed_cookies':
            fixes_applied.append('✅ Session backend: Using database/cache instead of signed_cookies')
        else:
            fixes_needed.append('❌ Session backend: Still using signed_cookies')
        
        # Check cache backend
        cache_backend = settings.CACHES['default']['BACKEND']
        if 'dummy' not in cache_backend.lower():
            fixes_applied.append('✅ Cache backend: Using functional cache')
        else:
            fixes_needed.append('❌ Cache backend: Still using dummy cache')
        
        # Check JWT settings
        jwt_settings = getattr(settings, 'SIMPLE_JWT', {})
        if jwt_settings.get('BLACKLIST_AFTER_ROTATION', False):
            fixes_applied.append('✅ JWT: Token blacklisting enabled')
        else:
            fixes_needed.append('❌ JWT: Token blacklisting disabled')
        
        # Check session timeout
        session_age = getattr(settings, 'SESSION_COOKIE_AGE', 0)
        if session_age >= 1800:  # 30 minutes
            fixes_applied.append('✅ Session timeout: Extended to 30+ minutes')
        else:
            fixes_needed.append(f'❌ Session timeout: Only {session_age//60} minutes')
        
        # Display results
        for fix in fixes_applied:
            self.stdout.write(self.style.SUCCESS(fix))
        
        for fix in fixes_needed:
            self.stdout.write(self.style.ERROR(fix))
        
        if fixes_needed:
            self.stdout.write(
                self.style.WARNING(
                    '\n💡 To apply production fixes:'
                )
            )
            self.stdout.write('   1. Deploy production_fix.py configuration')
            self.stdout.write('   2. Set REDIS_URL environment variable')
            self.stdout.write('   3. Restart application server')
    
    def _attempt_fixes(self, results):
        """Attempt to fix common issues automatically"""
        self.stdout.write('\n🔧 ATTEMPTING AUTOMATIC FIXES')
        self.stdout.write('-' * 30)
        
        fixes_attempted = 0
        
        # Clear cache issues
        try:
            from django.core.cache import cache
            cache.clear()
            self.stdout.write(self.style.SUCCESS('✅ Cleared cache'))
            fixes_attempted += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to clear cache: {e}'))
        
        # Clear expired sessions
        try:
            from django.contrib.sessions.models import Session
            from django.utils import timezone
            expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
            count = expired_sessions.count()
            expired_sessions.delete()
            self.stdout.write(self.style.SUCCESS(f'✅ Cleared {count} expired sessions'))
            fixes_attempted += 1
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ Could not clear expired sessions: {e}'))
        
        # Clear JWT blacklist if issues found
        jwt_issues = [
            issue for issue in results['issues_found']
            if 'jwt' in issue.get('component', '').lower()
        ]
        
        if jwt_issues:
            try:
                from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
                BlacklistedToken.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('✅ Cleared JWT blacklist'))
                fixes_attempted += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️ Could not clear JWT blacklist: {e}'))
        
        self.stdout.write(f'\n📊 Attempted {fixes_attempted} automatic fixes')
    
    def _save_report(self, results, output_file):
        """Save diagnostic report to JSON file"""
        try:
            # Add command metadata
            report = {
                'diagnostic_report': results,
                'generated_by': 'diagnose_auth_issues command',
                'generated_at': datetime.now().isoformat(),
                'django_settings_module': getattr(settings, 'SETTINGS_MODULE', 'unknown'),
                'debug_mode': getattr(settings, 'DEBUG', False)
            }
            
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.stdout.write(
                self.style.SUCCESS(f'📄 Report saved to {output_file}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to save report: {e}')
            )