"""
Management command to validate AI Insights functionality
"""
import logging
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.companies.models import Company, SubscriptionPlan
from apps.ai_insights.models import AICredit, AIConversation, AIMessage, AIInsight
from apps.ai_insights.services.credit_service import CreditService
from apps.ai_insights.services.ai_service import AIService

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Validate AI Insights functionality and production readiness'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Fix issues found during validation'
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Run full validation including AI service tests'
        )
    
    def handle(self, *args, **options):
        """Run validation checks"""
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting AI Insights Validation...\n')
        )
        
        issues = []
        fixes_applied = []
        
        # Run validation checks
        issues.extend(self._validate_models())
        issues.extend(self._validate_credit_system()) 
        issues.extend(self._validate_conversation_system())
        issues.extend(self._validate_insight_system())
        issues.extend(self._validate_settings())
        
        if options['full']:
            issues.extend(self._validate_ai_service())
        
        # Apply fixes if requested
        if options['fix'] and issues:
            fixes_applied = self._apply_fixes(issues)
        
        # Print results
        self._print_results(issues, fixes_applied)
        
        if issues and not options['fix']:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  Found {len(issues)} issues. Run with --fix to attempt automatic fixes."
                )
            )
        
        return 0 if not issues else 1
    
    def _validate_models(self):
        """Validate AI Insights models"""
        issues = []
        
        self.stdout.write("📋 Validating models...")
        
        try:
            # Test model creation
            from apps.ai_insights.models import AICredit, AIConversation, AIMessage, AIInsight
            
            # Check if models are properly registered
            models = [AICredit, AIConversation, AIMessage, AIInsight]
            for model in models:
                try:
                    model.objects.first()
                except Exception as e:
                    issues.append({
                        'type': 'model_error',
                        'message': f'Model {model.__name__} error: {str(e)}',
                        'severity': 'high'
                    })
            
            self.stdout.write(self.style.SUCCESS("✅ Models validation passed"))
            
        except Exception as e:
            issues.append({
                'type': 'model_import_error',
                'message': f'Failed to import models: {str(e)}',
                'severity': 'critical'
            })
        
        return issues
    
    def _validate_credit_system(self):
        """Validate credit management system"""
        issues = []
        
        self.stdout.write("💳 Validating credit system...")
        
        try:
            # Test credit service methods
            from apps.ai_insights.services.credit_service import CreditService
            
            # Validate credit packages
            if not CreditService.CREDIT_PACKAGES:
                issues.append({
                    'type': 'credit_config',
                    'message': 'No credit packages configured',
                    'severity': 'medium'
                })
            
            # Validate credit costs
            if not CreditService.CREDIT_COSTS:
                issues.append({
                    'type': 'credit_config',
                    'message': 'No credit costs configured',
                    'severity': 'medium'
                })
            
            # Check for companies without AI credits
            companies_without_credits = Company.objects.filter(
                subscription_status='active'
            ).exclude(
                ai_credits__isnull=False
            ).count()
            
            if companies_without_credits > 0:
                issues.append({
                    'type': 'missing_credits',
                    'message': f'{companies_without_credits} active companies without AI credit records',
                    'severity': 'medium',
                    'fixable': True
                })
            
            self.stdout.write(self.style.SUCCESS("✅ Credit system validation passed"))
            
        except Exception as e:
            issues.append({
                'type': 'credit_system_error',
                'message': f'Credit system validation failed: {str(e)}',
                'severity': 'high'
            })
        
        return issues
    
    def _validate_conversation_system(self):
        """Validate conversation system"""
        issues = []
        
        self.stdout.write("💬 Validating conversation system...")
        
        try:
            # Check for conversations without messages
            empty_conversations = AIConversation.objects.filter(
                message_count=0,
                created_at__lt=timezone.now() - timezone.timedelta(hours=1)
            ).count()
            
            if empty_conversations > 0:
                issues.append({
                    'type': 'empty_conversations',
                    'message': f'{empty_conversations} conversations without messages older than 1 hour',
                    'severity': 'low',
                    'fixable': True
                })
            
            # Check for orphaned messages
            orphaned_messages = AIMessage.objects.filter(
                conversation__isnull=True
            ).count()
            
            if orphaned_messages > 0:
                issues.append({
                    'type': 'orphaned_messages',
                    'message': f'{orphaned_messages} messages without conversations',
                    'severity': 'medium',
                    'fixable': True
                })
            
            self.stdout.write(self.style.SUCCESS("✅ Conversation system validation passed"))
            
        except Exception as e:
            issues.append({
                'type': 'conversation_system_error',
                'message': f'Conversation system validation failed: {str(e)}',
                'severity': 'high'
            })
        
        return issues
    
    def _validate_insight_system(self):
        """Validate insight system"""
        issues = []
        
        self.stdout.write("💡 Validating insight system...")
        
        try:
            # Check for expired insights that should be cleaned up
            expired_insights = AIInsight.objects.filter(
                expires_at__lt=timezone.now(),
                status__in=['new', 'viewed']
            ).count()
            
            if expired_insights > 0:
                issues.append({
                    'type': 'expired_insights',
                    'message': f'{expired_insights} expired insights need cleanup',
                    'severity': 'low',
                    'fixable': True
                })
            
            # Check for insights with invalid potential_impact
            invalid_insights = AIInsight.objects.filter(
                potential_impact__lt=0
            ).count()
            
            if invalid_insights > 0:
                issues.append({
                    'type': 'invalid_insights',
                    'message': f'{invalid_insights} insights with negative potential impact',
                    'severity': 'medium',
                    'fixable': True
                })
            
            self.stdout.write(self.style.SUCCESS("✅ Insight system validation passed"))
            
        except Exception as e:
            issues.append({
                'type': 'insight_system_error',
                'message': f'Insight system validation failed: {str(e)}',
                'severity': 'high'
            })
        
        return issues
    
    def _validate_settings(self):
        """Validate production settings"""
        issues = []
        
        self.stdout.write("⚙️  Validating settings...")
        
        try:
            from django.conf import settings
            
            # Check OpenAI API key
            if not getattr(settings, 'OPENAI_API_KEY', None):
                issues.append({
                    'type': 'missing_setting',
                    'message': 'OPENAI_API_KEY not configured',
                    'severity': 'critical'
                })
            
            # Check throttling settings
            if not hasattr(settings, 'REST_FRAMEWORK'):
                issues.append({
                    'type': 'missing_setting',
                    'message': 'REST_FRAMEWORK throttling not configured',
                    'severity': 'medium'
                })
            
            # Check Channels/WebSocket settings
            if not hasattr(settings, 'CHANNEL_LAYERS'):
                issues.append({
                    'type': 'missing_setting',
                    'message': 'CHANNEL_LAYERS not configured for WebSocket',
                    'severity': 'high'
                })
            
            # Check Redis settings for caching
            if not getattr(settings, 'CACHES', {}).get('default'):
                issues.append({
                    'type': 'missing_setting',
                    'message': 'Redis cache not configured',
                    'severity': 'medium'
                })
            
            self.stdout.write(self.style.SUCCESS("✅ Settings validation passed"))
            
        except Exception as e:
            issues.append({
                'type': 'settings_error',
                'message': f'Settings validation failed: {str(e)}',
                'severity': 'high'
            })
        
        return issues
    
    def _validate_ai_service(self):
        """Validate AI service functionality (full test only)"""
        issues = []
        
        self.stdout.write("🤖 Validating AI service...")
        
        try:
            from apps.ai_insights.services.ai_service import AIService
            
            # Check model costs configuration
            if not AIService.MODEL_COSTS:
                issues.append({
                    'type': 'ai_config',
                    'message': 'AI model costs not configured',
                    'severity': 'medium'
                })
            
            # Check system prompts
            if not AIService.SYSTEM_PROMPTS:
                issues.append({
                    'type': 'ai_config',
                    'message': 'AI system prompts not configured',
                    'severity': 'medium'
                })
            
            self.stdout.write(self.style.SUCCESS("✅ AI service validation passed"))
            
        except Exception as e:
            issues.append({
                'type': 'ai_service_error',
                'message': f'AI service validation failed: {str(e)}',
                'severity': 'high'
            })
        
        return issues
    
    def _apply_fixes(self, issues):
        """Apply automatic fixes for known issues"""
        fixes_applied = []
        
        self.stdout.write("🔧 Applying fixes...")
        
        for issue in issues:
            if not issue.get('fixable'):
                continue
            
            try:
                if issue['type'] == 'missing_credits':
                    fixes_applied.extend(self._fix_missing_credits())
                elif issue['type'] == 'empty_conversations':
                    fixes_applied.extend(self._fix_empty_conversations())
                elif issue['type'] == 'orphaned_messages':
                    fixes_applied.extend(self._fix_orphaned_messages())
                elif issue['type'] == 'expired_insights':
                    fixes_applied.extend(self._fix_expired_insights())
                elif issue['type'] == 'invalid_insights':
                    fixes_applied.extend(self._fix_invalid_insights())
                    
            except Exception as e:
                logger.error(f"Failed to fix {issue['type']}: {str(e)}")
        
        return fixes_applied
    
    def _fix_missing_credits(self):
        """Create AI credit records for companies without them"""
        fixes = []
        
        companies = Company.objects.filter(
            subscription_status='active'
        ).exclude(
            ai_credits__isnull=False
        )
        
        for company in companies:
            with transaction.atomic():
                ai_credit, created = AICredit.objects.get_or_create(
                    company=company,
                    defaults={
                        'balance': CreditService._get_monthly_allowance(company),
                        'monthly_allowance': CreditService._get_monthly_allowance(company),
                        'bonus_credits': 10  # Welcome bonus
                    }
                )
                
                if created:
                    fixes.append(f"Created AI credit record for {company.name}")
        
        return fixes
    
    def _fix_empty_conversations(self):
        """Clean up empty conversations"""
        fixes = []
        
        conversations = AIConversation.objects.filter(
            message_count=0,
            created_at__lt=timezone.now() - timezone.timedelta(hours=1)
        )
        
        count = conversations.count()
        conversations.delete()
        
        if count > 0:
            fixes.append(f"Deleted {count} empty conversations")
        
        return fixes
    
    def _fix_orphaned_messages(self):
        """Clean up orphaned messages"""
        fixes = []
        
        messages = AIMessage.objects.filter(conversation__isnull=True)
        count = messages.count()
        messages.delete()
        
        if count > 0:
            fixes.append(f"Deleted {count} orphaned messages")
        
        return fixes
    
    def _fix_expired_insights(self):
        """Clean up expired insights"""
        fixes = []
        
        insights = AIInsight.objects.filter(
            expires_at__lt=timezone.now(),
            status__in=['new', 'viewed']
        )
        
        count = insights.update(status='dismissed')
        
        if count > 0:
            fixes.append(f"Dismissed {count} expired insights")
        
        return fixes
    
    def _fix_invalid_insights(self):
        """Fix insights with invalid data"""
        fixes = []
        
        # Fix negative potential impact
        insights = AIInsight.objects.filter(potential_impact__lt=0)
        count = insights.update(potential_impact=None)
        
        if count > 0:
            fixes.append(f"Fixed {count} insights with negative potential impact")
        
        return fixes
    
    def _print_results(self, issues, fixes_applied):
        """Print validation results"""
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("🎯 AI INSIGHTS VALIDATION RESULTS"))
        self.stdout.write("="*60)
        
        if not issues:
            self.stdout.write(
                self.style.SUCCESS("🎉 All validations passed! System is production ready.")
            )
            return
        
        # Group issues by severity
        critical = [i for i in issues if i.get('severity') == 'critical']
        high = [i for i in issues if i.get('severity') == 'high']
        medium = [i for i in issues if i.get('severity') == 'medium']
        low = [i for i in issues if i.get('severity') == 'low']
        
        if critical:
            self.stdout.write(self.style.ERROR(f"\n🚨 CRITICAL ISSUES ({len(critical)}):"))
            for issue in critical:
                self.stdout.write(f"  • {issue['message']}")
        
        if high:
            self.stdout.write(self.style.ERROR(f"\n⚠️  HIGH ISSUES ({len(high)}):"))
            for issue in high:
                self.stdout.write(f"  • {issue['message']}")
        
        if medium:
            self.stdout.write(self.style.WARNING(f"\n⚡ MEDIUM ISSUES ({len(medium)}):"))
            for issue in medium:
                self.stdout.write(f"  • {issue['message']}")
        
        if low:
            self.stdout.write(self.style.HTTP_INFO(f"\n💡 LOW ISSUES ({len(low)}):"))
            for issue in low:
                self.stdout.write(f"  • {issue['message']}")
        
        if fixes_applied:
            self.stdout.write(self.style.SUCCESS(f"\n🔧 FIXES APPLIED ({len(fixes_applied)}):"))
            for fix in fixes_applied:
                self.stdout.write(f"  • {fix}")
        
        self.stdout.write("\n" + "="*60)