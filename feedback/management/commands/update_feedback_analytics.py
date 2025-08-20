from django.core.management.base import BaseCommand
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from django.utils import timezone
from feedback.models import Feedback, FeedbackAnalytics
from datetime import timedelta

class Command(BaseCommand):
    help = 'Update feedback analytics data'

    def handle(self, *args, **options):
        # Get yesterday's date
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Calculate analytics for yesterday
        feedback_data = Feedback.objects.filter(
            created_at__date=yesterday
        ).aggregate(
            total_feedback=Count('id'),
            positive_count=Count('id', filter=Q(sentiment='positive')),
            neutral_count=Count('id', filter=Q(sentiment='neutral')),
            negative_count=Count('id', filter=Q(sentiment='negative')),
            resolved_count=Count('id', filter=Q(status='resolved'))
        )
        
        # Calculate average resolution time
        resolved_feedback = Feedback.objects.filter(
            status='resolved',
            resolved_at__date=yesterday
        ).annotate(
            resolution_time=ExpressionWrapper(
                F('resolved_at') - F('created_at'),
                output_field=DurationField()
            )
        )
        
        avg_resolution_time = resolved_feedback.aggregate(
            avg_time=Avg('resolution_time')
        )['avg_time']
        
        # Convert to hours
        if avg_resolution_time:
            avg_resolution_time = avg_resolution_time.total_seconds() / 3600
        else:
            avg_resolution_time = 0.0
        
        # Update or create analytics record
        analytics, created = FeedbackAnalytics.objects.get_or_create(
            date=yesterday,
            defaults={
                'total_feedback': feedback_data['total_feedback'],
                'positive_count': feedback_data['positive_count'],
                'neutral_count': feedback_data['neutral_count'],
                'negative_count': feedback_data['negative_count'],
                'resolved_count': feedback_data['resolved_count'],
                'avg_resolution_time': avg_resolution_time
            }
        )
        
        if not created:
            analytics.total_feedback = feedback_data['total_feedback']
            analytics.positive_count = feedback_data['positive_count']
            analytics.neutral_count = feedback_data['neutral_count']
            analytics.negative_count = feedback_data['negative_count']
            analytics.resolved_count = feedback_data['resolved_count']
            analytics.avg_resolution_time = avg_resolution_time
            analytics.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Updated analytics for {yesterday}: "
                f"{feedback_data['total_feedback']} feedback entries"
            )
        )