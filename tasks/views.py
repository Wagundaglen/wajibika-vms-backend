from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from .models import Task
from communication.models import Notification

User = get_user_model()

# ---------------------------
# Admin creates tasks
# ---------------------------
@login_required
def create_task_view(request):
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to create tasks.")
        
    if request.method == "POST":
        # Handle task creation logic here
        task = Task.objects.create(
            title=request.POST['title'],
            description=request.POST['description'],
            assigned_to=request.POST['assigned_to']
        )
        Notification.objects.create(
            recipient=task.assigned_to,
            message=f"You have been assigned a new task: {task.title}"
        )
        messages.success(request, "Task created successfully.")
        return redirect('task_list')  # Replace with your task list URL

    return render(request, 'tasks/create_task.html')  # Your task creation template

# ---------------------------
# Volunteer views their own tasks
# ---------------------------
@login_required
def my_tasks_view(request):
    tasks = Task.objects.filter(assigned_to=request.user)
    print(f"Tasks for {request.user.username}: {tasks}")  # Debug line to check fetched tasks
    return render(request, 'tasks/my_tasks.html', {'tasks': tasks})

# ---------------------------
# Volunteer accepts a task
# ---------------------------
@login_required
def accept_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    task.acceptance_status = 'Accepted'
    task.status = 'In Progress'
    task.save()

    # Notify all admins
    notify_admins(f"{request.user.username} accepted task '{task.title}'.")

    messages.success(request, "✅ You have accepted the task.")
    return redirect('my_tasks')

# ---------------------------
# Volunteer rejects a task
# ---------------------------
@login_required
def reject_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    task.acceptance_status = 'Rejected'
    task.save()

    # Notify all admins
    notify_admins(f"{request.user.username} rejected task '{task.title}'.")

    messages.info(request, "❌ You have rejected the task.")
    return redirect('my_tasks')

# Helper function to notify admins
def notify_admins(message):
    admins = User.objects.filter(is_staff=True, is_superuser=True)
    for admin in admins:
        Notification.objects.create(recipient=admin, message=message)