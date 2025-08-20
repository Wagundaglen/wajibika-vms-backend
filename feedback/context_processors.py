from .models import Feedback, FeedbackCategory
from django.db.models import Count, Q
from django.utils import timezone
from django.db.models import ExpressionWrapper, F, Avg, DurationField

def feedback_stats(request):
    context = {}
    
    if request.user.is_authenticated:
        if request.user.role == 'Admin':
            # Admin stats
            context['open_feedback_count'] = Feedback.objects.filter(status='open').count()
            context['total_feedback'] = Feedback.objects.count()
            context['resolved_this_week'] = Feedback.objects.filter(
                status='resolved',
                resolved_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).count()
            context['in_progress_feedback'] = Feedback.objects.filter(status='in_progress').count()
            
            # Recent feedback for dashboard
            context['recent_feedback'] = Feedback.objects.select_related('user').order_by('-created_at')[:5]
            
            # Top categories
            context['top_categories'] = Feedback.objects.values('category__name').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            # Resolution time stats
            resolved_feedback = Feedback.objects.filter(
                status='resolved',
                resolved_at__isnull=False
            ).annotate(
                resolution_time=ExpressionWrapper(
                    F('resolved_at') - F('created_at'),
                    output_field=DurationField()
                )
            )
            
            avg_resolution_time = resolved_feedback.aggregate(
                avg_time=Avg('resolution_time')
            )['avg_time']
            
            # Calculate average resolution time in days and hours
            avg_resolution_hours = None
            if avg_resolution_time:
                total_seconds = avg_resolution_time.total_seconds()
                avg_resolution_hours = {
                    'days': int(total_seconds // 86400),
                    'hours': int((total_seconds % 86400) // 3600)
                }
            
            context['avg_resolution_time'] = avg_resolution_time
            context['avg_resolution_hours'] = avg_resolution_hours
        
        elif request.user.role == 'Coordinator':
            # Coordinator stats
            context['assigned_feedback_count'] = Feedback.objects.filter(
                assigned_to=request.user,
                status__in=['open', 'in_progress']
            ).count()
            
            # Team feedback stats
            if hasattr(request.user, 'profile') and request.user.profile.team:
                team_feedback = Feedback.objects.filter(
                    Q(user__profile__team=request.user.profile.team) |
                    Q(assigned_to=request.user)
                )
                context['team_feedback_count'] = team_feedback.count()
                context['team_open_feedback'] = team_feedback.filter(status='open').count()
        
        # For all authenticated users
        context['user_feedback'] = Feedback.objects.filter(user=request.user).order_by('-created_at')
        
        # Categories for filter dropdown
        context['categories'] = FeedbackCategory.objects.all()
    
    return context