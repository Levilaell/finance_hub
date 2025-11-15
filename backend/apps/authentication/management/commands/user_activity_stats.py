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

        # Recent activity
        self.stdout.write(self.style.HTTP_INFO('Recent Activity (Last 10 events):'))
        recent_events = queryset.select_related('user').order_by('-created_at')[:10]

        for event in recent_events:
            event_display = event.get_event_type_display()
            timestamp = event.created_at.strftime('%Y-%m-%d %H:%M:%S')
            self.stdout.write(f"  [{timestamp}] {event.user.email}: {event_display}")

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
