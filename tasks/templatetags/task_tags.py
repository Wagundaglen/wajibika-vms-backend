from django import template
from django.db.models import Count, Sum
from ..models import Task, TimeEntry

register = template.Library()

@register.simple_tag
def get_task_stats(user):
    """Get task statistics for a user"""
    if not user.is_authenticated:
        return {}
    
    if user.is_staff or user.role == "Admin":
        return {
            'total_tasks': Task.objects.count(),
            'pending_tasks': Task.objects.filter(acceptance_status='Pending').count(),
            'in_progress_tasks': Task.objects.filter(status='In Progress').count(),
            'completed_tasks': Task.objects.filter(status='Completed').count(),
        }
    elif user.role == "Coordinator":
        try:
            team_volunteers = user.team.volunteers.all()
        except:
            team_volunteers = []
        
        team_tasks = Task.objects.filter(assigned_to__in=team_volunteers)
        return {
            'team_total_tasks': team_tasks.count(),
            'team_pending_tasks': team_tasks.filter(acceptance_status='Pending').count(),
            'team_in_progress_tasks': team_tasks.filter(status='In Progress').count(),
            'team_completed_tasks': team_tasks.filter(status='Completed').count(),
        }
    elif user.role == "Volunteer":
        user_tasks = Task.objects.filter(assigned_to=user)
        return {
            'user_total_tasks': user_tasks.count(),
            'user_pending_tasks': user_tasks.filter(acceptance_status='Pending').count(),
            'user_accepted_tasks': user_tasks.filter(acceptance_status='Accepted').count(),
            'user_completed_tasks': user_tasks.filter(status='Completed').count(),
            'user_total_hours': TimeEntry.objects.filter(
                volunteer=user,
                approved=True
            ).aggregate(total=Sum('hours'))['total'] or 0,
        }
    
    return {}