from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, Max, ExpressionWrapper, F, DurationField
from django.core.paginator import Paginator
from .models import Task, TaskCategory, TimeEntry
from .forms import TaskForm, TimeEntryForm
from communication.models import Notification

User = get_user_model()

# Helper functions
def is_admin(user):
    """Check if user is admin"""
    return user.is_staff or user.role == "Admin"

def is_admin_or_coordinator(user):
    """Check if user is admin or coordinator"""
    return user.is_staff or user.role == "Coordinator"

def is_volunteer(user):
    """Check if user is volunteer"""
    return user.role == "Volunteer"

def notify_admins(message):
    """Send notification to all admin users"""
    admins = User.objects.filter(is_staff=True, is_superuser=True)
    for admin in admins:
        Notification.objects.create(recipient=admin, message=message)

def notify_user(user, message):
    """Send notification to a specific user"""
    Notification.objects.create(recipient=user, message=message)

def notify_coordinators(message):
    """Send notification to all coordinators"""
    coordinators = User.objects.filter(role="Coordinator")
    for coordinator in coordinators:
        Notification.objects.create(recipient=coordinator, message=message)

# ---------------------------
# Task list view
# ---------------------------
@login_required
def task_list(request):
    """Display tasks based on user role"""
    filter_status = request.GET.get("status")
    filter_priority = request.GET.get("priority")
    search_query = request.GET.get("search", "")
    
    # Get tasks based on user role
    if is_admin_or_coordinator(request.user):
        tasks = Task.objects.select_related('assigned_to', 'created_by', 'category')
    else:
        tasks = Task.objects.filter(assigned_to=request.user).select_related('created_by', 'category')
    
    # Apply filters
    if filter_status:
        tasks = tasks.filter(acceptance_status=filter_status)
    if filter_priority:
        tasks = tasks.filter(priority=filter_priority)
    
    # Apply search
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(assigned_to__username__icontains=search_query)
        )
    
    # Order by priority and creation date
    tasks = tasks.order_by('-priority', '-created_at')
    
    # Pagination
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        "tasks": page_obj,
        "filter_status": filter_status,
        "filter_priority": filter_priority,
        "search_query": search_query,
        "user": request.user,
        "status_choices": Task.ACCEPTANCE_CHOICES,
        "priority_choices": Task.PRIORITY_CHOICES,
    }
    
    return render(request, "tasks/task_list.html", context)

# ---------------------------
# Create task view
# ---------------------------
@login_required
@user_passes_test(is_admin_or_coordinator, login_url=reverse_lazy('login'))
def create_task(request):
    """Create a new task (admin/coordinator only)"""
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            
            # Send notification to assigned user
            notify_user(
                task.assigned_to,
                f"You have been assigned a new task: {task.title}. Please review and accept or reject."
            )
            
            messages.success(request, "✅ Task created successfully.")
            return redirect("tasks:task_detail", pk=task.pk)
    else:
        form = TaskForm()
    
    context = {
        "form": form,
        "title": "Create Task",
        "action": "Create",
    }
    
    return render(request, "tasks/task_form.html", context)

# ---------------------------
# Task detail view
# ---------------------------
@login_required
def task_detail(request, pk):
    """Display task details"""
    task = get_object_or_404(
        Task.objects.select_related('assigned_to', 'created_by', 'category'),
        pk=pk
    )
    
    # Check permissions
    if not (is_admin_or_coordinator(request.user) or task.assigned_to == request.user):
        raise PermissionDenied("You do not have permission to view this task.")
    
    # Get time entries for this task if user is assigned to it
    time_entries = None
    if task.assigned_to == request.user:
        time_entries = TimeEntry.objects.filter(task=task, volunteer=request.user)
    
    # Get task progress
    total_modules = 1  # For future extension if tasks have modules
    completed_modules = 1 if task.status == 'Completed' else 0
    progress_percent = int((completed_modules / total_modules) * 100) if total_modules > 0 else 0
    
    context = {
        "task": task,
        "user": request.user,
        "is_overdue": task.is_overdue,
        "days_until_due": task.days_until_due,
        "is_upcoming": task.is_upcoming,
        "time_entries": time_entries,
        "progress_percent": progress_percent,
    }
    
    return render(request, "tasks/task_detail.html", context)

# ---------------------------
# Accept task view
# ---------------------------
@login_required
def accept_task(request, pk):
    """Accept a task (volunteer only)"""
    task = get_object_or_404(Task, pk=pk, assigned_to=request.user)
    
    if task.acceptance_status != "Pending":
        messages.warning(request, "⚠️ This task has already been responded to.")
        return redirect("tasks:task_detail", pk=task.pk)
    
    task.acceptance_status = "Accepted"
    task.status = "In Progress"
    task.save()
    
    # Notify the task creator
    notify_user(
        task.created_by,
        f"{request.user.get_full_name() or request.user.username} has accepted the task: {task.title}"
    )
    
    # Also notify admins if task creator is not admin
    if not is_admin(task.created_by):
        notify_admins(
            f"{request.user.get_full_name() or request.user.username} has accepted the task: {task.title}"
        )
    
    messages.success(request, "✅ You have accepted the task.")
    return redirect("tasks:task_detail", pk=task.pk)

# ---------------------------
# Reject task view
# ---------------------------
@login_required
def reject_task(request, pk):
    """Reject a task (volunteer only)"""
    task = get_object_or_404(Task, pk=pk, assigned_to=request.user)
    
    if task.acceptance_status != "Pending":
        messages.warning(request, "⚠️ This task has already been responded to.")
        return redirect("tasks:task_detail", pk=task.pk)
    
    task.acceptance_status = "Rejected"
    task.save()
    
    # Notify the task creator
    notify_user(
        task.created_by,
        f"{request.user.get_full_name() or request.user.username} has rejected the task: {task.title}"
    )
    
    # Also notify admins if task creator is not admin
    if not is_admin(task.created_by):
        notify_admins(
            f"{request.user.get_full_name() or request.user.username} has rejected the task: {task.title}"
        )
    
    messages.info(request, "❌ You have rejected the task.")
    return redirect("tasks:task_detail", pk=task.pk)

# ---------------------------
# Update task status view
# ---------------------------
@login_required
def update_task_status(request, pk):
    """Update task status (volunteer only)"""
    task = get_object_or_404(Task, pk=pk, assigned_to=request.user)
    
    if task.acceptance_status != "Accepted":
        messages.error(request, "⚠️ You must accept the task before updating its status.")
        return redirect("tasks:task_detail", pk=task.pk)
    
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(Task.STATUS_CHOICES).keys():
            old_status = task.status
            task.status = new_status
            task.save()
            
            # If task is completed, set completion date
            if new_status == "Completed":
                task.completed_at = timezone.now()
                task.save()
            
            # Notify the task creator
            notify_user(
                task.created_by,
                f"{request.user.get_full_name() or request.user.username} marked task '{task.title}' as {new_status}."
            )
            
            # Also notify admins if task creator is not admin
            if not is_admin(task.created_by):
                notify_admins(
                    f"{request.user.get_full_name() or request.user.username} marked task '{task.title}' as {new_status}."
                )
            
            messages.success(request, f"✅ Task marked as {new_status}.")
        else:
            messages.error(request, "⚠️ Invalid status update.")
    
    return redirect("tasks:task_detail", pk=task.pk)

# ---------------------------
# Edit task view (admin/coordinator)
# ---------------------------
@login_required
@user_passes_test(is_admin_or_coordinator, login_url=reverse_lazy('login'))
def edit_task(request, pk):
    """Edit an existing task (admin/coordinator only)"""
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            old_assigned_to = task.assigned_to
            form.save()
            
            # If assigned user changed, notify both old and new users
            if old_assigned_to != task.assigned_to:
                notify_user(
                    old_assigned_to,
                    f"You have been unassigned from task: {task.title}"
                )
                notify_user(
                    task.assigned_to,
                    f"You have been assigned a new task: {task.title}"
                )
            
            messages.success(request, "✅ Task updated successfully.")
            return redirect("tasks:task_detail", pk=task.pk)
    else:
        form = TaskForm(instance=task)
    
    context = {
        "form": form,
        "task": task,
        "title": "Edit Task",
        "action": "Update",
    }
    
    return render(request, "tasks/task_form.html", context)

# ---------------------------
# Delete task view (admin/coordinator)
# ---------------------------
@login_required
@user_passes_test(is_admin_or_coordinator, login_url=reverse_lazy('login'))
def delete_task(request, pk):
    """Delete a task (admin/coordinator only)"""
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == "POST":
        task_title = task.title
        assigned_user = task.assigned_to
        
        # Notify assigned user that task was deleted
        notify_user(
            assigned_user,
            f"The task '{task_title}' assigned to you has been deleted."
        )
        
        task.delete()
        messages.success(request, f"✅ Task '{task_title}' has been deleted.")
        return redirect("tasks:task_list")
    
    context = {
        "task": task,
    }
    
    return render(request, "tasks/task_confirm_delete.html", context)

# ---------------------------
# Time tracking views
# ---------------------------
@login_required
def log_hours(request):
    """Log hours for a task (volunteer only)"""
    task_id = request.GET.get('task')
    task = None
    
    if task_id:
        task = get_object_or_404(Task, pk=task_id, assigned_to=request.user)
    
    if request.method == "POST":
        form = TimeEntryForm(request.POST)
        if form.is_valid():
            time_entry = form.save(commit=False)
            time_entry.volunteer = request.user
            time_entry.save()
            
            # Notify admins and coordinators about new hours entry
            notify_admins(
                f"{request.user.get_full_name() or request.user.username} has logged {time_entry.hours} hours for task '{time_entry.task.title}'"
            )
            notify_coordinators(
                f"{request.user.get_full_name() or request.user.username} has logged {time_entry.hours} hours for task '{time_entry.task.title}'"
            )
            
            messages.success(request, "✅ Hours logged successfully.")
            return redirect("tasks:task_detail", pk=time_entry.task.pk)
    else:
        form = TimeEntryForm(initial={'task': task})
    
    # Get available tasks for this volunteer
    available_tasks = Task.objects.filter(
        assigned_to=request.user,
        acceptance_status='Accepted',
        status__in=['Pending', 'In Progress']
    )
    
    context = {
        "form": form,
        "task": task,
        "available_tasks": available_tasks,
    }
    
    return render(request, "tasks/log_hours.html", context)

@login_required
def my_hours(request):
    """View logged hours (volunteer only)"""
    # Get filter parameters
    filter_month = request.GET.get('month')
    filter_year = request.GET.get('year')
    
    # Base queryset
    time_entries = TimeEntry.objects.filter(volunteer=request.user).select_related('task')
    
    # Apply filters
    if filter_month and filter_year:
        time_entries = time_entries.filter(date__month=filter_month, date__year=filter_year)
    
    # Calculate statistics
    total_hours = sum(entry.hours for entry in time_entries if entry.approved)
    pending_hours = sum(entry.hours for entry in time_entries if not entry.approved)
    
    # Group by month for chart
    monthly_hours = TimeEntry.objects.filter(
        volunteer=request.user,
        approved=True
    ).extra(
        select={'month': "EXTRACT(month FROM date)", 'year': "EXTRACT(year FROM date)"}
    ).values('month', 'year').annotate(
        total=Sum('hours')
    ).order_by('year', 'month')
    
    context = {
        "time_entries": time_entries,
        "total_hours": total_hours,
        "pending_hours": pending_hours,
        "monthly_hours": monthly_hours,
        "filter_month": filter_month,
        "filter_year": filter_year,
    }
    
    return render(request, "tasks/my_hours.html", context)

@login_required
@user_passes_test(is_admin_or_coordinator, login_url=reverse_lazy('login'))
def approve_hours(request):
    """Approve volunteer hours (admin/coordinator only)"""
    # Get filter parameters
    filter_volunteer = request.GET.get('volunteer')
    
    # Base queryset
    pending_entries = TimeEntry.objects.filter(approved=False).select_related('volunteer', 'task')
    
    # Apply filters
    if filter_volunteer:
        pending_entries = pending_entries.filter(volunteer_id=filter_volunteer)
    
    # Get volunteers for filter dropdown
    volunteers = User.objects.filter(role='Volunteer').order_by('username')
    
    if request.method == "POST":
        entry_id = request.POST.get('entry_id')
        action = request.POST.get('action')
        
        entry = get_object_or_404(TimeEntry, pk=entry_id)
        
        if action == 'approve':
            entry.approved = True
            entry.approved_by = request.user
            entry.save()
            
            notify_user(
                entry.volunteer,
                f"Your hours for task '{entry.task.title}' have been approved."
            )
            
            messages.success(request, "✅ Hours approved successfully.")
        elif action == 'reject':
            entry.delete()
            messages.info(request, "❌ Hours entry rejected and removed.")
        
        return redirect("tasks:approve_hours")
    
    context = {
        "pending_entries": pending_entries,
        "volunteers": volunteers,
        "filter_volunteer": filter_volunteer,
    }
    
    return render(request, "tasks/approve_hours.html", context)