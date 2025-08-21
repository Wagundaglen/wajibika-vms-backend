from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from .models import Task
from communication.models import Notification

User = get_user_model()


# ---------------------------
# Task list (admin/coordinator see all, volunteers see theirs)
# ---------------------------
@login_required
def task_list(request):
    filter_status = request.GET.get("status")
    
    # Get base queryset based on user role
    if request.user.is_staff or request.user.role == "Coordinator":
        tasks = Task.objects.all().order_by("-created_at")
    else:
        tasks = Task.objects.filter(assigned_to=request.user).order_by("-created_at")
    
    # Apply status filter if provided
    if filter_status:
        tasks = tasks.filter(acceptance_status=filter_status)
    
    # Prepare context
    context = {
        "tasks": tasks,
        "filter_status": filter_status,
        "user": request.user,
        "status_choices": [
            ('Pending', 'Pending'),
            ('Accepted', 'Accepted'),
            ('Rejected', 'Rejected'),
            ('In Progress', 'In Progress'),
            ('Completed', 'Completed'),
        ]
    }
    
    return render(request, "tasks/tasks.html", context)


# ---------------------------
# Admin/Coordinator creates tasks
# ---------------------------
@login_required
def create_task(request):
    # ✅ Allow Admins OR Coordinators
    if not (request.user.is_staff or request.user.role == "Coordinator"):
        raise PermissionDenied("You do not have permission to create tasks.")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        due_date = request.POST.get("due_date")
        assigned_to_id = request.POST.get("assigned_to")

        if not title or not assigned_to_id:
            messages.error(request, "⚠️ Title and assigned user are required.")
            return redirect("create_task")

        assigned_user = get_object_or_404(User, id=assigned_to_id)

        task = Task.objects.create(
            title=title,
            description=description,
            due_date=due_date if due_date else None,
            assigned_to=assigned_user
        )

        Notification.objects.create(
            recipient=assigned_user,
            message=f"You have been assigned a new task: {task.title}"
        )

        messages.success(request, "✅ Task created successfully.")
        return redirect("tasks_module")

    # Show Volunteers & Coordinators as assignable
    users = User.objects.filter(role__in=["Volunteer", "Coordinator"])
    return render(request, "tasks/create_task.html", {
        "title": "Create Task",
        "users": users
    })
@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions
    if not (request.user.is_staff or request.user.role == "Coordinator" or task.assigned_to == request.user):
        raise PermissionDenied("You do not have permission to view this task.")
    
    return render(request, "tasks/task_detail.html", {"task": task})

@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions - only Admins or Coordinators can edit tasks
    if not (request.user.is_staff or request.user.role == "Coordinator"):
        raise PermissionDenied("You do not have permission to edit tasks.")
    
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        due_date = request.POST.get("due_date")
        assigned_to_id = request.POST.get("assigned_to")
        
        if not title or not assigned_to_id:
            messages.error(request, "⚠️ Title and assigned user are required.")
            return redirect("edit_task", task_id=task_id)
        
        assigned_user = get_object_or_404(User, id=assigned_to_id)
        
        # Update task fields
        task.title = title
        task.description = description
        task.due_date = due_date if due_date else None
        task.assigned_to = assigned_user
        task.save()
        
        # Send notification to the assigned user if changed
        if task.assigned_to != assigned_user:
            Notification.objects.create(
                recipient=assigned_user,
                message=f"Task '{task.title}' has been reassigned to you"
            )
        
        messages.success(request, "✅ Task updated successfully.")
        return redirect("task_detail", task_id=task.id)
    
    # Show Volunteers & Coordinators as assignable
    users = User.objects.filter(role__in=["Volunteer", "Coordinator"])
    return render(request, "tasks/edit_task.html", {
        "task": task,
        "users": users,
        "title": "Edit Task"
    })

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions - only Admins or Coordinators can delete tasks
    if not (request.user.is_staff or request.user.role == "Coordinator"):
        raise PermissionDenied("You do not have permission to delete tasks.")
    
    if request.method == "POST":
        # Send notification to the assigned user
        if task.assigned_to:
            Notification.objects.create(
                recipient=task.assigned_to,
                message=f"Task '{task.title}' assigned to you has been deleted"
            )
        
        task.delete()
        messages.success(request, "✅ Task deleted successfully.")
        return redirect("tasks_module")
    
    return render(request, "tasks/delete_task.html", {"task": task})

# ---------------------------
# Volunteer accepts a task
# ---------------------------
@login_required
def accept_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    task.acceptance_status = "Accepted"
    task.status = "In Progress"
    task.save()

    notify_admins(f"{request.user.username} accepted task '{task.title}'.")
    messages.success(request, "✅ You have accepted the task.")
    return redirect("tasks_module")


# ---------------------------
# Volunteer rejects a task
# ---------------------------
@login_required
def reject_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    task.acceptance_status = "Rejected"
    task.save()

    notify_admins(f"{request.user.username} rejected task '{task.title}'.")
    messages.info(request, "❌ You have rejected the task.")
    return redirect("tasks_module")


# ---------------------------
# Volunteer updates task status
# ---------------------------
@login_required
def update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in ["In Progress", "Completed"]:
            task.status = new_status
            task.save()
            notify_admins(f"{request.user.username} marked task '{task.title}' as {new_status}.")
            messages.success(request, f"✅ Task marked as {new_status}.")
        else:
            messages.error(request, "⚠️ Invalid status update.")

    return redirect("tasks_module")


# ---------------------------
# Helper function to notify admins
# ---------------------------
def notify_admins(message):
    admins = User.objects.filter(is_staff=True, is_superuser=True)
    for admin in admins:
        Notification.objects.create(recipient=admin, message=message)
