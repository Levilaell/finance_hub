"""
Create default system categories for users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.banking.models import Category

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default system categories for users'

    # Default categories based on Pluggy's common categories
    DEFAULT_CATEGORIES = {
        'income': [
            {'name': 'Salary', 'color': '#10b981', 'icon': '💰'},
            {'name': 'Freelance', 'color': '#3b82f6', 'icon': '💼'},
            {'name': 'Investments', 'color': '#8b5cf6', 'icon': '📈'},
            {'name': 'Gifts', 'color': '#ec4899', 'icon': '🎁'},
            {'name': 'Refunds', 'color': '#06b6d4', 'icon': '↩️'},
            {'name': 'Other Income', 'color': '#6366f1', 'icon': '➕'},
        ],
        'expense': [
            {'name': 'Food & Dining', 'color': '#ef4444', 'icon': '🍽️'},
            {'name': 'Groceries', 'color': '#f59e0b', 'icon': '🛒'},
            {'name': 'Transportation', 'color': '#3b82f6', 'icon': '🚗'},
            {'name': 'Shopping', 'color': '#ec4899', 'icon': '🛍️'},
            {'name': 'Entertainment', 'color': '#8b5cf6', 'icon': '🎬'},
            {'name': 'Bills & Utilities', 'color': '#6366f1', 'icon': '💡'},
            {'name': 'Healthcare', 'color': '#10b981', 'icon': '🏥'},
            {'name': 'Education', 'color': '#14b8a6', 'icon': '📚'},
            {'name': 'Travel', 'color': '#06b6d4', 'icon': '✈️'},
            {'name': 'Housing', 'color': '#64748b', 'icon': '🏠'},
            {'name': 'Insurance', 'color': '#475569', 'icon': '🛡️'},
            {'name': 'Subscriptions', 'color': '#7c3aed', 'icon': '📱'},
            {'name': 'Personal Care', 'color': '#db2777', 'icon': '💅'},
            {'name': 'Pets', 'color': '#f97316', 'icon': '🐾'},
            {'name': 'Gifts & Donations', 'color': '#84cc16', 'icon': '🎁'},
            {'name': 'Other Expenses', 'color': '#94a3b8', 'icon': '➖'},
        ]
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Create categories for specific user ID only'
        )
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Create categories for all users'
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        all_users = options.get('all_users')

        # Get target users
        if user_id:
            users = User.objects.filter(id=user_id)
            if not users.exists():
                self.stdout.write(
                    self.style.ERROR(f'❌ User with ID {user_id} not found')
                )
                return
        elif all_users:
            users = User.objects.all()
        else:
            self.stdout.write(
                self.style.ERROR('❌ Please specify either --user-id or --all-users')
            )
            return

        total_created = 0

        for user in users:
            self.stdout.write(f"\nCreating categories for user: {user.username}")

            user_created = 0

            for category_type, categories in self.DEFAULT_CATEGORIES.items():
                for cat_data in categories:
                    category, created = Category.objects.get_or_create(
                        user=user,
                        name=cat_data['name'],
                        type=category_type,
                        defaults={
                            'color': cat_data['color'],
                            'icon': cat_data['icon'],
                            'is_system': True
                        }
                    )

                    if created:
                        user_created += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  + Created {category_type} category: {cat_data['name']}"
                            )
                        )
                    else:
                        self.stdout.write(
                            f"  - Skipped (already exists): {cat_data['name']}"
                        )

            total_created += user_created
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {user_created} categories for {user.username}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTotal: Created {total_created} categories across {users.count()} user(s)"
            )
        )
