from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Recognition, Badge, RecognitionProfile, Leaderboard, Team
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

@login_required
def dashboard(request):
    user = request.user
    
    # Get user's recognition profile
    try:
        profile = RecognitionProfile.objects.get(volunteer=user)
    except RecognitionProfile.DoesNotExist:
        profile = None
    
    # Get user's recent recognitions
    recent_recognitions = Recognition.objects.filter(
        volunteer=user
    ).order_by('-created_at')[:5]
    
    # Get user's badges
    user_badges = Badge.objects.filter(
        recognition__volunteer=user
    ).distinct()
    
    # Get leaderboard position
    try:
        leaderboard_entry = Leaderboard.objects.get(
            volunteer=user,
            timeframe='all_time'
        )
        rank = leaderboard_entry.rank
    except Leaderboard.DoesNotExist:
        rank = None
    
    # Get team leaderboard if user is in a team
    team_leaderboard = None
    if profile and profile.team:
        team_leaderboard = Leaderboard.objects.filter(
            team=profile.team,
            timeframe='all_time'
        ).order_by('rank')[:10]
    
    # Get top badges (most awarded)
    top_badges = Badge.objects.annotate(
        award_count=Count('recognition')
    ).order_by('-award_count')[:5]
    
    # Get recent activity
    recent_activity = Recognition.objects.filter(
        team=profile.team if profile else None
    ).order_by('-created_at')[:10] if profile else Recognition.objects.none()
    
    context = {
        'profile': profile,
        'recent_recognitions': recent_recognitions,
        'user_badges': user_badges,
        'rank': rank,
        'team_leaderboard': team_leaderboard,
        'top_badges': top_badges,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'recognition/dashboard.html', context)