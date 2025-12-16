"""
Management command to view user activity statistics
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from apps.authentication.models import UserActivityLog

User = get_user_model()


class Command(BaseCommand):
    help = 'Display user activity statistics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to look back (default: 30)'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Filter by specific user email or username'
        )
        parser.add_argument(
            '--event-type',
            type=str,
            help='Filter by event type (login, sync_started, etc.)'
        )

    def handle(self, *args, **options):
        days = options['days']
        user_filter = options.get('user')
        event_type = options.get('event_type')

        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Base queryset
        queryset = UserActivityLog.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )

        # Apply filters
        if user_filter:
            queryset = queryset.filter(
                Q(user__email__icontains=user_filter) |
                Q(user__username__icontains=user_filter)
            )

        if event_type:
            queryset = queryset.filter(event_type=event_type)

        # Display header
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS(f'User Activity Statistics'))
        self.stdout.write(self.style.SUCCESS(f'Period: {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")} ({days} days)'))
        if user_filter:
            self.stdout.write(self.style.SUCCESS(f'User filter: {user_filter}'))
        if event_type:
            self.stdout.write(self.style.SUCCESS(f'Event type: {event_type}'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        # Total events
        total_events = queryset.count()
        self.stdout.write(self.style.WARNING(f'Total Events: {total_events}'))
        self.stdout.write('')

        # Events by type
        self.stdout.write(self.style.HTTP_INFO('Events by Type:'))
        events_by_type = queryset.values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')

        for event in events_by_type:
            event_display = dict(UserActivityLog.EVENT_TYPES).get(event['event_type'], event['event_type'])
            self.stdout.write(f"  {event_display}: {event['count']}")
        self.stdout.write('')

        # Active users
        active_users = queryset.values('user__email', 'user__username').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        self.stdout.write(self.style.HTTP_INFO('Top 10 Most Active Users:'))
        for i, user in enumerate(active_users, 1):
            display_name = user['user__email'] or user['user__username']
            self.stdout.write(f"  {i}. {display_name}: {user['count']} events")
        self.stdout.write('')

        # Login statistics
        login_events = queryset.filter(event_type='login')
        unique_logins = login_events.values('user').distinct().count()

        self.stdout.write(self.style.HTTP_INFO('Login Statistics:'))
        self.stdout.write(f"  Total logins: {login_events.count()}")
        self.stdout.write(f"  Unique users who logged in: {unique_logins}")
        self.stdout.write('')

        # Bank connection statistics
        bank_events = queryset.filter(
            event_type__in=['bank_connection_created', 'bank_connection_updated', 'bank_connection_deleted']
        )

        self.stdout.write(self.style.HTTP_INFO('Bank Connection Activity:'))
        self.stdout.write(f"  Connections created: {queryset.filter(event_type='bank_connection_created').count()}")
        self.stdout.write(f"  Connections updated: {queryset.filter(event_type='bank_connection_updated').count()}")
        self.stdout.write(f"  Connections deleted: {queryset.filter(event_type='bank_connection_deleted').count()}")
        self.stdout.write('')

        # Sync statistics
        sync_started = queryset.filter(event_type='sync_started')
        sync_completed = queryset.filter(event_type='sync_completed')
        sync_failed = queryset.filter(event_type='sync_failed')

        self.stdout.write(self.style.HTTP_INFO('Synchronization Activity:'))
        self.stdout.write(f"  Syncs started: {sync_started.count()}")
        self.stdout.write(f"  Syncs completed: {sync_completed.count()}")
        self.stdout.write(f"  Syncs failed: {sync_failed.count()}")

        if sync_started.count() > 0:
            success_rate = (sync_completed.count() / sync_started.count()) * 100
            self.stdout.write(f"  Success rate: {success_rate:.1f}%")
        self.stdout.write('')

        # Signup statistics
        signups = queryset.filter(event_type='signup')
        self.stdout.write(self.style.HTTP_INFO('Signup Activity:'))
        self.stdout.write(f"  Total signups: {signups.count()}")

        # Signups by acquisition angle
        signup_angles = signups.exclude(metadata__acquisition_angle__isnull=True).values(
            'metadata__acquisition_angle'
        ).annotate(count=Count('id')).order_by('-count')

        if signup_angles:
            self.stdout.write('  By acquisition angle:')
            for angle in signup_angles:
                angle_name = angle.get('metadata__acquisition_angle', 'unknown')
                if angle_name:
                    self.stdout.write(f"    {angle_name}: {angle['count']}")
        self.stdout.write('')

        # Reports statistics
        report_events = queryset.filter(event_type='report_generated')
        pdf_exports = queryset.filter(event_type='report_exported_pdf')
        excel_exports = queryset.filter(event_type='report_exported_excel')

        self.stdout.write(self.style.HTTP_INFO('Reports Activity:'))
        self.stdout.write(f"  Reports generated: {report_events.count()}")
        self.stdout.write(f"  PDF exports: {pdf_exports.count()}")
        self.stdout.write(f"  Excel exports: {excel_exports.count()}")

        # Reports by type
        report_types = report_events.values('metadata__report_type').annotate(
            count=Count('id')
        ).order_by('-count')

        if report_types:
            self.stdout.write('  By report type:')
            for rt in report_types:
                rtype = rt.get('metadata__report_type', 'unknown')
                if rtype:
                    self.stdout.write(f"    {rtype}: {rt['count']}")
        self.stdout.write('')

        # AI Insights statistics
        ai_enabled = queryset.filter(event_type='ai_insights_enabled')
        ai_disabled = queryset.filter(event_type='ai_insights_disabled')
        ai_regenerated = queryset.filter(event_type='ai_insights_regenerated')
        ai_viewed = queryset.filter(event_type='ai_insights_viewed')

        self.stdout.write(self.style.HTTP_INFO('AI Insights Activity:'))
        self.stdout.write(f"  Insights enabled: {ai_enabled.count()}")
        self.stdout.write(f"  Insights disabled: {ai_disabled.count()}")
        self.stdout.write(f"  Insights regenerated: {ai_regenerated.count()}")
        self.stdout.write(f"  Insights viewed: {ai_viewed.count()}")
        self.stdout.write('')

        # Bills statistics
        bills_created = queryset.filter(event_type='bill_created')
        bills_updated = queryset.filter(event_type='bill_updated')
        bills_deleted = queryset.filter(event_type='bill_deleted')
        bills_payments = queryset.filter(event_type='bill_payment_registered')
        bills_linked = queryset.filter(event_type='bill_transaction_linked')
        bills_unlinked = queryset.filter(event_type='bill_transaction_unlinked')

        self.stdout.write(self.style.HTTP_INFO('Bills Activity:'))
        self.stdout.write(f"  Bills created: {bills_created.count()}")
        self.stdout.write(f"  Bills updated: {bills_updated.count()}")
        self.stdout.write(f"  Bills deleted: {bills_deleted.count()}")
        self.stdout.write(f"  Payments registered: {bills_payments.count()}")
        self.stdout.write(f"  Transactions linked: {bills_linked.count()}")
        self.stdout.write(f"  Transactions unlinked: {bills_unlinked.count()}")

        # Bills by type
        bills_by_type = bills_created.values('metadata__bill_type').annotate(
            count=Count('id')
        ).order_by('-count')

        if bills_by_type:
            self.stdout.write('  By bill type:')
            for bt in bills_by_type:
                btype = bt.get('metadata__bill_type', 'unknown')
                if btype:
                    self.stdout.write(f"    {btype}: {bt['count']}")
        self.stdout.write('')

        # Page view statistics
        page_views = queryset.filter(event_type='page_view')
        unique_page_viewers = page_views.values('user').distinct().count()

        self.stdout.write(self.style.HTTP_INFO('Page View Activity:'))
        self.stdout.write(f"  Total page views: {page_views.count()}")
        self.stdout.write(f"  Unique users: {unique_page_viewers}")

        # Top pages
        top_pages = page_views.values('metadata__page').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        if top_pages:
            self.stdout.write('  Top 10 pages:')
            for pg in top_pages:
                page_name = pg.get('metadata__page', 'unknown')
                if page_name:
                    self.stdout.write(f"    {page_name}: {pg['count']}")
        self.stdout.write('')

        # Recent activity
        self.stdout.write(self.style.HTTP_INFO('Recent Activity (Last 10 events):'))
        recent_events = queryset.select_related('user').order_by('-created_at')[:10]

        for event in recent_events:
            event_display = event.get_event_type_display()
            timestamp = event.created_at.strftime('%Y-%m-%d %H:%M:%S')
            self.stdout.write(f"  [{timestamp}] {event.user.email}: {event_display}")

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
