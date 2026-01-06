"""
Celery tasks for AI Insights
"""
from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
import logging

from apps.ai_insights.models import AIInsightConfig
from apps.ai_insights.services.insight_generator import InsightGenerator

User = get_user_model()
logger = logging.getLogger(__name__)


def _clear_generation_cache(user_id: int):
    """Clear the generation-in-progress cache for a user."""
    cache_key = f'ai_insight_generating_{user_id}'
    cache.delete(cache_key)


@shared_task(bind=True, max_retries=3)
def generate_insight_for_user(self, user_id: int):
    """
    Generate AI insight for a specific user.

    Args:
        user_id: User ID to generate insights for
    """
    try:
        user = User.objects.get(id=user_id)
        logger.info(f'🔄 Starting insight generation for user {user.email}')

        generator = InsightGenerator(user)
        insight = generator.generate(force=False)

        # Clear the generation-in-progress cache
        _clear_generation_cache(user_id)

        logger.info(f'✅ Generated insight {insight.id} for user {user.email}')
        return {
            'success': True,
            'user_id': user_id,
            'insight_id': str(insight.id),
            'health_score': float(insight.health_score)
        }

    except User.DoesNotExist:
        _clear_generation_cache(user_id)
        logger.error(f'❌ User {user_id} not found')
        return {'success': False, 'error': 'User not found'}

    except Exception as e:
        logger.error(f'❌ Error generating insight for user {user_id}: {str(e)}')

        # Retry with exponential backoff
        try:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            # Clear cache on final failure
            _clear_generation_cache(user_id)
            logger.error(f'❌ Max retries exceeded for user {user_id}')
            return {'success': False, 'error': str(e)}


@shared_task
def generate_weekly_insights():
    """
    Generate insights for all users with AI insights enabled.
    This task should be scheduled to run weekly via Celery Beat.
    """
    logger.info('🔄 Starting weekly insight generation for all users')

    # Get all users with AI insights enabled
    configs = AIInsightConfig.objects.filter(is_enabled=True).select_related('user')

    total = configs.count()
    logger.info(f'Found {total} users with AI insights enabled')

    scheduled_count = 0
    for config in configs:
        # Check if user should get a new insight
        if config.next_scheduled_at and config.next_scheduled_at > timezone.now():
            logger.info(f'Skipping user {config.user.email} - next scheduled at {config.next_scheduled_at}')
            continue

        # Schedule insight generation
        generate_insight_for_user.delay(config.user.id)
        scheduled_count += 1
        logger.info(f'Scheduled insight generation for user {config.user.email}')

    logger.info(f'✅ Scheduled {scheduled_count}/{total} insight generation tasks')

    return {
        'total_users': total,
        'scheduled_count': scheduled_count,
        'timestamp': timezone.now().isoformat()
    }


@shared_task
def cleanup_old_insights(days: int = 365):
    """
    Clean up insights older than specified days.
    Keep at least one insight per user for historical reference.

    Args:
        days: Number of days to keep insights (default: 365)
    """
    from apps.ai_insights.models import AIInsight
    from django.db.models import Min

    logger.info(f'🗑️  Starting cleanup of insights older than {days} days')

    cutoff_date = timezone.now() - timezone.timedelta(days=days)

    # Get the oldest insight for each user (to preserve)
    oldest_insights = AIInsight.objects.values('user').annotate(
        oldest_date=Min('generated_at')
    )

    oldest_ids = []
    for item in oldest_insights:
        oldest = AIInsight.objects.filter(
            user_id=item['user'],
            generated_at=item['oldest_date']
        ).first()
        if oldest:
            oldest_ids.append(oldest.id)

    # Delete old insights except the oldest one per user
    deleted_count, _ = AIInsight.objects.filter(
        generated_at__lt=cutoff_date
    ).exclude(
        id__in=oldest_ids
    ).delete()

    logger.info(f'✅ Cleaned up {deleted_count} old insights')

    return {
        'deleted_count': deleted_count,
        'cutoff_date': cutoff_date.isoformat(),
        'preserved_count': len(oldest_ids)
    }
