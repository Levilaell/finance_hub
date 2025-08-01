"""
Management command to check payment system health
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.payments.monitoring import run_monitoring_check, MonitoringConfig
import json


class Command(BaseCommand):
    help = 'Check payment system health and send alerts if needed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--config-file',
            type=str,
            help='Path to monitoring configuration JSON file'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run checks but do not send alerts'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Starting payment health check at {timezone.now()}')
        )

        try:
            # Load custom config if provided
            config = None
            if options['config_file']:
                try:
                    with open(options['config_file'], 'r') as f:
                        config_data = json.load(f)
                        config = MonitoringConfig(**config_data)
                        self.stdout.write(f'Loaded custom configuration from {options["config_file"]}')
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to load config file: {e}')
                    )
                    return

            # Run monitoring checks
            if options['dry_run']:
                self.stdout.write(self.style.WARNING('DRY RUN MODE - No alerts will be sent'))
            
            alerts = run_monitoring_check()
            
            if not alerts:
                self.stdout.write(
                    self.style.SUCCESS('✓ No alerts found - payment system is healthy')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ Found {len(alerts)} alert(s):')
                )
                
                for i, alert in enumerate(alerts, 1):
                    style = self.style.ERROR if alert['severity'] == 'critical' else self.style.WARNING
                    
                    self.stdout.write(f'\n  Alert {i}:')
                    self.stdout.write(f'    Type: {alert["type"]}')
                    self.stdout.write(style(f'    Severity: {alert["severity"].upper()}'))
                    self.stdout.write(f'    Message: {alert["message"]}')
                    self.stdout.write(f'    Timestamp: {alert["timestamp"]}')
                    
                    if options['verbose'] and 'metrics' in alert:
                        self.stdout.write('    Metrics:')
                        for key, value in alert['metrics'].items():
                            self.stdout.write(f'      {key}: {value}')
                    
                    if alert.get('action_required'):
                        self.stdout.write(
                            self.style.ERROR('    ⚠ IMMEDIATE ACTION REQUIRED')
                        )

            # Summary
            self.stdout.write(f'\nHealth check completed at {timezone.now()}')
            self.stdout.write(f'Total alerts: {len(alerts)}')
            
            if alerts:
                critical_count = sum(1 for alert in alerts if alert['severity'] == 'critical')
                warning_count = len(alerts) - critical_count
                
                if critical_count:
                    self.stdout.write(
                        self.style.ERROR(f'Critical alerts: {critical_count}')
                    )
                if warning_count:
                    self.stdout.write(
                        self.style.WARNING(f'Warning alerts: {warning_count}')
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Health check failed with error: {e}')
            )
            raise