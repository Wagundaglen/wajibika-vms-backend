from django.db.models import Count, Sum, Q
from django.utils import timezone
from .models import Task, TimeEntry


def task_notifications(request):
    """Add task-related notifications to the context"""
    if request.user.is_authenticated:
        # Import here to avoid circular imports
        from tasks.models import Task
        
        # Count pending tasks for the current user
        pending_tasks = Task.objects.filter(
            assigned_to=request.user,
            status__in=['pending', 'in_progress']
        ).count()
        
        # Count overdue tasks
        overdue_tasks = Task.objects.filter(
            assigned_to=request.user,
            due_date__lt=timezone.now(),
            status__in=['pending', 'in_progress']
        ).count()
        
        return {
            'pending_tasks_count': pending_tasks,
            'overdue_tasks_count': overdue_tasks,
            'total_task_notifications': pending_tasks + overdue_tasks
        }
    return {}

def task_statistics(request):
    """Provide task statistics for the current user"""
    if not request.user.is_authenticated:
        return {}
    
    context = {}
    
    if request.user.is_staff or request.user.role == "Admin":
        # Admin statistics
        context.update({
            'total_tasks': Task.objects.count(),
            'pending_tasks': Task.objects.filter(acceptance_status='Pending').count(),
            'in_progress_tasks': Task.objects.filter(status='In Progress').count(),
            'completed_tasks': Task.objects.filter(status='Completed').count(),
            'overdue_tasks': Task.objects.filter(
                due_date__lt=timezone.now().date(), 
                status__in=['Pending', 'In Progress']
            ).count(),
            'pending_hours_count': TimeEntry.objects.filter(approved=False).count(),
        })
    elif request.user.role == "Coordinator":
        # Coordinator statistics
        try:
            team_volunteers = request.user.team.volunteers.all()
        except:
            team_volunteers = []
        
        team_tasks = Task.objects.filter(assigned_to__in=team_volunteers)
        context.update({
            'team_total_tasks': team_tasks.count(),
            'team_pending_tasks': team_tasks.filter(acceptance_status='Pending').count(),
            'team_in_progress_tasks': team_tasks.filter(status='In Progress').count(),
            'team_completed_tasks': team_tasks.filter(status='Completed').count(),
            'team_pending_hours_count': TimeEntry.objects.filter(
                volunteer__in=team_volunteers,
                approved=False
            ).count(),
        })
    elif request.user.role == "Volunteer":
        # Volunteer statistics
        user_tasks = Task.objects.filter(assigned_to=request.user)
        context.update({
            'user_total_tasks': user_tasks.count(),
            'user_pending_tasks': user_tasks.filter(acceptance_status='Pending').count(),
            'user_accepted_tasks': user_tasks.filter(acceptance_status='Accepted').count(),
            'user_completed_tasks': user_tasks.filter(status='Completed').count(),
            'user_upcoming_tasks': user_tasks.filter(
                start_date__gte=timezone.now().date(),
                acceptance_status='Accepted'
            ).count(),
            'user_total_hours': TimeEntry.objects.filter(
                volunteer=request.user,
                approved=True
            ).aggregate(total=Sum('hours'))['total'] or 0,
            'user_pending_hours': TimeEntry.objects.filter(
                volunteer=request.user,
                approved=False
            ).aggregate(total=Sum('hours'))['total'] or 0,
        })
    
    return context