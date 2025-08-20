from django.utils import timezone
from datetime import timedelta
from .models import Leaderboard, Team, Recognition
from django.db.models import Sum
from django.db import transaction

def update_leaderboard(timeframe='all_time', team=None, verbose=False):
    """
    Update leaderboard for specified timeframe and team.
    
    Args:
        timeframe (str): 'weekly', 'monthly', or 'all_time'
        team (Team): Team object or None for system-wide
        verbose (bool): Print detailed output
    
    Returns:
        dict: Result information including success status and counts
    """
    result = {
        'success': False,
        'timeframe': timeframe,
        'team': team.name if team else 'System-wide',
        'deleted': 0,
        'created': 0,
        'error': None
    }
    
    try:
        # Calculate date range based on timeframe
        now = timezone.now()
        if timeframe == 'weekly':
            start_date = now - timedelta(days=7)
        elif timeframe == 'monthly':
            start_date = now - timedelta(days=30)
        else:
            start_date = None
        
        # Filter recognitions
        recognitions = Recognition.objects.all()
        if start_date:
            recognitions = recognitions.filter(created_at__gte=start_date)
        if team:
            recognitions = recognitions.filter(team=team)
        
        # Calculate points for each volunteer
        volunteer_points = recognitions.values('volunteer').annotate(
            total_points=Sum('points')
        ).order_by('-total_points')
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            # Clear existing leaderboard entries
            deleted_count, _ = Leaderboard.objects.filter(
                timeframe=timeframe, 
                team=team
            ).delete()
            
            # Create new leaderboard entries
            created_count = 0
            for rank, entry in enumerate(volunteer_points, 1):
                Leaderboard.objects.create(
                    volunteer_id=entry['volunteer'],
                    points=entry['total_points'] or 0,
                    rank=rank,
                    timeframe=timeframe,
                    team=team
                )
                created_count += 1
        
        result.update({
            'success': True,
            'deleted': deleted_count,
            'created': created_count
        })
        
        if verbose:
            print(f"Updated {timeframe} leaderboard for {result['team']}: Deleted {deleted_count}, Created {created_count}")
        
    except Exception as e:
        result['error'] = str(e)
        if verbose:
            print(f"Error updating {timeframe} leaderboard for {result['team']}: {str(e)}")
    
    return result

def update_all_leaderboards(verbose=False):
    """
    Update all leaderboards for all timeframes and teams.
    
    Args:
        verbose (bool): Print detailed output
    
    Returns:
        dict: Summary of all updates
    """
    summary = {
        'total_updates': 0,
        'errors': [],
        'results': []
    }
    
    # Get all teams
    teams = Team.objects.all()
    teams = list(teams) + [None]  # Include None for system-wide
    
    timeframes = ['weekly', 'monthly', 'all_time']
    
    for team in teams:
        for timeframe in timeframes:
            result = update_leaderboard(timeframe, team, verbose)
            summary['results'].append(result)
            
            if result['success']:
                summary['total_updates'] += 1
            else:
                summary['errors'].append(result['error'])
    
    return summary