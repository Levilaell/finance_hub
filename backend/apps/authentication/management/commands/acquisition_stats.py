"""
Management command to view acquisition angle statistics.
Shows registrations and trial conversions by acquisition angle (UTM).
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Display acquisition statistics by angle (UTM tracking)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to look back (default: 30)'
        )
        parser.add_argument(
            '--angle',
            type=str,
            help='Filter by specific acquisition angle (time, price, delay, visibility)'
        )

    def handle(self, *args, **options):
        days = options['days']
        angle_filter = options.get('angle')

        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Base queryset - users created in the period
        users = User.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )

        # Apply angle filter if provided
        if angle_filter:
            users = users.filter(acquisition_angle=angle_filter)

        # Display header
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('Acquisition Statistics by Angle'))
        self.stdout.write(self.style.SUCCESS(f'Period: {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")} ({days} days)'))
        if angle_filter:
            self.stdout.write(self.style.SUCCESS(f'Angle filter: {angle_filter}'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        # Total registrations
        total_registrations = users.count()
        self.stdout.write(self.style.WARNING(f'Total Registrations: {total_registrations}'))
        self.stdout.write('')

        # Registrations by angle
        self.stdout.write(self.style.HTTP_INFO('Registrations by Acquisition Angle:'))
        registrations_by_angle = users.values('acquisition_angle').annotate(
            count=Count('id')
        ).order_by('-count')

        for item in registrations_by_angle:
            angle = item['acquisition_angle'] or '(not tracked)'
            self.stdout.write(f"  {angle}: {item['count']} registrations")
        self.stdout.write('')

        # Trial statistics (users with active subscription)
        self.stdout.write(self.style.HTTP_INFO('Trial Conversions by Angle:'))
        self.stdout.write('')

        # Import djstripe to check subscriptions
        try:
            from djstripe.models import Subscription

            # For each angle, count users with trials
            angles = users.values_list('acquisition_angle', flat=True).distinct()

            stats = []
            for angle in angles:
                angle_users = users.filter(acquisition_angle=angle)
                angle_count = angle_users.count()

                # Count users with any subscription (trial or active)
                users_with_trial = 0
                for user in angle_users:
                    has_sub = Subscription.objects.filter(
                        customer__subscriber=user,
                        status__in=['trialing', 'active', 'past_due']
                    ).exists()
                    if has_sub:
                        users_with_trial += 1

                conversion_rate = (users_with_trial / angle_count * 100) if angle_count > 0 else 0
                display_angle = angle or '(not tracked)'
                stats.append({
                    'angle': display_angle,
                    'registrations': angle_count,
                    'trials': users_with_trial,
                    'conversion_rate': conversion_rate
                })

            # Sort by registrations
            stats.sort(key=lambda x: x['registrations'], reverse=True)

            # Display table header
            self.stdout.write(f"  {'Angle':<20} {'Registrations':<15} {'Trials':<10} {'Conv. Rate':<12}")
            self.stdout.write(f"  {'-' * 20} {'-' * 15} {'-' * 10} {'-' * 12}")

            for stat in stats:
                self.stdout.write(
                    f"  {stat['angle']:<20} {stat['registrations']:<15} {stat['trials']:<10} {stat['conversion_rate']:.1f}%"
                )

            self.stdout.write('')

            # Summary
            total_with_trial = sum(s['trials'] for s in stats)
            overall_conversion = (total_with_trial / total_registrations * 100) if total_registrations > 0 else 0

            self.stdout.write(self.style.HTTP_INFO('Summary:'))
            self.stdout.write(f"  Total registrations: {total_registrations}")
            self.stdout.write(f"  Total trials started: {total_with_trial}")
            self.stdout.write(f"  Overall conversion rate: {overall_conversion:.1f}%")

        except ImportError:
            self.stdout.write(self.style.WARNING('  djstripe not available - cannot check trial status'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
