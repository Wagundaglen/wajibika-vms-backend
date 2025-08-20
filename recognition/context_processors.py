from .models import Recognition, RecognitionProfile, Badge, Leaderboard
from django.db.models import Sum, Count

def recognition_data(request):
    context = {}
    
    if request.user.is_authenticated:
        try:
            profile = RecognitionProfile.objects.get(volunteer=request.user)
            context['user_profile'] = profile
            context['total_points'] = profile.total_points
            
            # Get user's badges
            context['user_badges'] = Badge.objects.filter(
                recognition__volunteer=request.user
            ).distinct()
            
            # Get user's recent recognitions
            context['recent_recognitions'] = Recognition.objects.filter(
                volunteer=request.user
            ).order_by('-created_at')[:3]
            
            # Get user's rank
            try:
                leaderboard_entry = Leaderboard.objects.get(
                    volunteer=request.user,
                    timeframe='all_time'
                )
                context['user_rank'] = leaderboard_entry.rank
            except Leaderboard.DoesNotExist:
                context['user_rank'] = None
                
        except RecognitionProfile.DoesNotExist:
            context['user_profile'] = None
            context['total_points'] = 0
            context['user_badges'] = []
            context['recent_recognitions'] = []
            context['user_rank'] = None
    
    # Get system-wide stats for admin/coordinator
    if request.user.is_authenticated and request.user.role in ['Admin', 'Coordinator']:
        context['total_volunteers'] = RecognitionProfile.objects.count()
        context['total_badges'] = Badge.objects.count()
        context['total_recognitions'] = Recognition.objects.count()
        
        # Top performers
        context['top_performers'] = RecognitionProfile.objects.order_by(
            '-total_points'
        )[:5]
    
    return context