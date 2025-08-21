from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task
from tasks.forms import TaskForm
from .forms import VolunteerRegistrationForm, EditProfileForm

User = get_user_model()

# ---------- Static Page Views ----------
def home(request):
    return render(request, "home.html")

def about(request):
    return render(request, "about.html")

def volunteer(request):
    return render(request, "volunteer.html")

def donate(request):
    return render(request, "donate.html")

def payment_options(request):
    return render(request, "payment_options.html", {
        'paypal_link': 'https://www.paypal.com/donate?hosted_button_id=YOUR_PAYPAL_ID',
        'mpesa_link': 'https://m-pesapay.com/YOUR_MPESA_LINK',
    })

@csrf_exempt
def donate_process(request):
    if request.method == "POST":
        amount = request.POST.get("amount")
        phone = request.POST.get("phone")
        if amount and phone:
            messages.success(request, f"✅ Thank you for donating KES {amount}! Confirmation will be sent to {phone}.")
        else:
            messages.error(request, "⚠️ Please enter both amount and phone number.")
    return redirect("donate")

def contact(request):
    return render(request, "contact.html")

# ---------- Account Views ----------
def register_form(request):
    if request.method == "POST":
        form = VolunteerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            role_group_map = {
                "Volunteer": "Volunteers",
                "Coordinator": "Coordinators",
                "Admin": "Admins"
            }
            group_name = role_group_map.get(user.role)
            if user.role == "Admin":
                user.is_staff = True
                user.is_superuser = True
            user.save()
            if group_name:
                group, _ = Group.objects.get_or_create(name=group_name)
                user.groups.add(group)
            messages.success(request, "✅ Account created successfully! Please log in.")
            return redirect("login_form")
        else:
            messages.error(request, "⚠️ Please correct the errors below.")
    else:
        form = VolunteerRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})

def login_form(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"👋 Welcome back, {user.username}!")
            return redirect("dashboard_redirect")
        else:
            messages.error(request, "❌ Invalid username or password.")
    return render(request, "accounts/login.html")

@login_required
def profile_page(request):
    return render(request, "accounts/profile.html", {"user": request.user})

@login_required
def edit_profile(request):
    """Edit own profile"""
    if request.method == "POST":
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Profile updated successfully!")
            return redirect("profile_page")
        else:
            messages.error(request, "⚠️ Please correct the errors below.")
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, "accounts/edit_profile.html", {"form": form})

@login_required
def edit_user(request, user_id):
    """Admins/Coordinators edit another user's profile"""
    if request.user.role not in ["Admin", "Coordinator"]:
        raise PermissionDenied("You are not authorized to edit users.")
    
    user_obj = get_object_or_404(User, id=user_id)
    
    # Coordinators can only edit Volunteers
    if request.user.role == "Coordinator" and user_obj.role != "Volunteer":
        raise PermissionDenied("Coordinators can only edit volunteers.")
    
    if request.method == "POST":
        form = EditProfileForm(request.POST, request.FILES, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ {user_obj.username}'s profile updated successfully.")
            return redirect("manage_users")
        else:
            messages.error(request, "⚠️ Please correct the errors below.")
    else:
        form = EditProfileForm(instance=user_obj)
    
    return render(request, "accounts/edit_user.html", {
        "form": form,
        "user_obj": user_obj,
        "is_editing_other_user": True
    })

@login_required
def logout_user(request):
    logout(request)
    messages.info(request, "✅ You have been logged out.")
    return redirect("login_form")

# ---------- Dashboard Views ----------
@login_required
def admin_dashboard(request):
    # Get statistics for admin dashboard
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    new_users_last_week = User.objects.filter(date_joined__gte=timezone.now() - timedelta(days=7)).count()
    
    # Task statistics
    total_tasks = Task.objects.count()
    pending_tasks = Task.objects.filter(status='Pending').count()
    in_progress_tasks = Task.objects.filter(status='In Progress').count()
    completed_tasks = Task.objects.filter(status='Completed').count()
    
    # Role counts
    volunteer_count = User.objects.filter(role='Volunteer').count()
    coordinator_count = User.objects.filter(role='Coordinator').count()
    
    # Recent activities
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_tasks = Task.objects.order_by('-created_at')[:5]
    
    # Additional counts for dashboard
    active_volunteers_week = User.objects.filter(
        role='Volunteer', 
        last_login__gte=timezone.now() - timedelta(days=7)
    ).count()
    active_coordinators = User.objects.filter(
        role='Coordinator', 
        last_login__gte=timezone.now() - timedelta(days=7)
    ).count()
    due_today_tasks = Task.objects.filter(
        due_date=timezone.now().date(),
        status__in=['Pending', 'In Progress']
    ).count()
    
    # Placeholder variables for other features
    pending_hours_count = 0
    unread_count = 0
    training_notifications_count = 0
    user_badges = []
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'new_users_last_week': new_users_last_week,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'volunteer_count': volunteer_count,
        'coordinator_count': coordinator_count,
        'recent_users': recent_users,
        'recent_tasks': recent_tasks,
        'active_volunteers_week': active_volunteers_week,
        'active_coordinators': active_coordinators,
        'due_today_tasks': due_today_tasks,
        'pending_hours_count': pending_hours_count,
        'unread_count': unread_count,
        'training_notifications_count': training_notifications_count,
        'user_badges': user_badges,
        'show_manage_users': True,
    }
    return render(request, "dashboards/admin_dashboard.html", context)

@login_required
def coordinator_dashboard(request):
    # Get statistics for coordinator dashboard
    total_volunteers = User.objects.filter(role='Volunteer').count()
    active_volunteers = User.objects.filter(role='Volunteer', is_active=True).count()
    
    # Task statistics for coordinator's volunteers
    volunteer_tasks = Task.objects.filter(assigned_to__role='Volunteer')
    total_tasks = volunteer_tasks.count()
    pending_tasks = volunteer_tasks.filter(status='Pending').count()
    in_progress_tasks = volunteer_tasks.filter(status='In Progress').count()
    completed_tasks = volunteer_tasks.filter(status='Completed').count()
    
    # Recent activities
    recent_volunteers = User.objects.filter(role='Volunteer').order_by('-date_joined')[:5]
    recent_tasks = volunteer_tasks.order_by('-created_at')[:5]
    
    context = {
        'total_volunteers': total_volunteers,
        'active_volunteers': active_volunteers,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'recent_volunteers': recent_volunteers,
        'recent_tasks': recent_tasks,
        'show_manage_users': True,
    }
    return render(request, "dashboards/coordinator_dashboard.html", context)

@login_required
def volunteer_dashboard(request):
    # Get statistics for volunteer dashboard
    user_tasks = Task.objects.filter(assigned_to=request.user)
    total_tasks = user_tasks.count()
    pending_tasks = user_tasks.filter(status='Pending').count()
    in_progress_tasks = user_tasks.filter(status='In Progress').count()
    completed_tasks = user_tasks.filter(status='Completed').count()
    
    # Recent activities
    recent_tasks = user_tasks.order_by('-created_at')[:5]
    
    context = {
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'recent_tasks': recent_tasks,
        'show_manage_users': False,
    }
    return render(request, "dashboards/volunteer_dashboard.html", context)

@login_required
def dashboard_redirect(request):
    if hasattr(request.user, 'role'):
        if request.user.role == "Admin":
            return redirect("admin_dashboard")
        elif request.user.role == "Coordinator":
            return redirect("coordinator_dashboard")
        elif request.user.role == "Volunteer":
            return redirect("volunteer_dashboard")
    
    # Fallback if role is not set
    return redirect("profile_page")

# ---------- Tasks Module ----------
@login_required
def tasks_module(request):
    if request.user.role == "Admin":
        tasks = Task.objects.all().order_by("-created_at")
    elif request.user.role == "Coordinator":
        tasks = Task.objects.filter(assigned_to__role="Volunteer").order_by("-created_at")
    else:
        tasks = Task.objects.filter(assigned_to=request.user).order_by("-created_at")
    return render(request, "tasks/tasks.html", {"tasks": tasks})

@login_required
def create_task(request):
    if request.user.role not in ["Admin", "Coordinator"]:
        messages.error(request, "You are not authorized to create tasks.")
        return redirect("tasks_module")
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_to = User.objects.get(id=request.POST.get("assigned_to"))
            task.save()
            messages.success(request, "✅ Task created successfully!")
            return redirect("tasks_module")
    else:
        form = TaskForm()
    return render(request, "modules/task_form.html", {"form": form, "title": "Create Task"})

@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.user.role not in ["Admin", "Coordinator"]:
        messages.error(request, "You are not authorized to edit tasks.")
        return redirect("tasks_module")
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Task updated successfully!")
            return redirect("tasks_module")
    else:
        form = TaskForm(instance=task)
    return render(request, "modules/task_form.html", {"form": form, "title": "Edit Task"})

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.user.role not in ["Admin", "Coordinator"]:
        messages.error(request, "You are not authorized to delete tasks.")
        return redirect("tasks_module")
    task.delete()
    messages.success(request, "✅ Task deleted successfully!")
    return redirect("tasks_module")

@login_required
def accept_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    task.acceptance_status = "Accepted"
    task.status = "In Progress"
    task.save()
    messages.success(request, "✅ You have accepted the task.")
    return redirect("tasks_module")

@login_required
def reject_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    task.acceptance_status = "Rejected"
    task.status = "Pending"
    task.save()
    messages.info(request, "❌ You have rejected the task.")
    return redirect("tasks_module")

# ---------- Other Modules ----------
@login_required
def communication_module(request):
    return render(request, "modules/communication.html")

@login_required
def training_module(request):
    return render(request, "modules/training.html")

# ---------- Manage Users ----------
@login_required
def manage_users(request):
    if request.user.role not in ["Admin", "Coordinator"]:
        messages.error(request, "You are not authorized to access this page.")
        return redirect("dashboard_redirect")
    
    # Get filter parameters
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    # Start with all users
    users = User.objects.all()
    
    # Apply filters
    if role_filter:
        users = users.filter(role=role_filter)
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) | 
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) | 
            Q(email__icontains=search_query)
        )
    
    # For Coordinators, only show Volunteers
    if request.user.role == "Coordinator":
        users = users.filter(role="Volunteer")
    
    # Order by join date
    users = users.order_by("-date_joined")
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(users, 10)  # Show 10 users per page
    
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    
    # Get counts for dashboard
    total_users = paginator.count
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()
    
    # Role counts
    role_counts = {
        'Admin': User.objects.filter(role='Admin').count(),
        'Coordinator': User.objects.filter(role='Coordinator').count(),
        'Volunteer': User.objects.filter(role='Volunteer').count(),
    }
    
    context = {
        "users": users,
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "role_counts": role_counts,
        "current_role_filter": role_filter,
        "current_status_filter": status_filter,
        "current_search": search_query,
        "page_title": "Manage Users",
    }
    return render(request, "accounts/manage_users.html", context)

@login_required
def user_list(request):
    # Get all users ordered by join date
    users = User.objects.all().order_by("-date_joined")
    
    # Calculate statistics
    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    inactive_users = users.filter(is_active=False).count()
    volunteer_users = users.filter(role='Volunteer').count()
    admin_users = users.filter(role='Admin').count()
    coordinator_users = users.filter(role='Coordinator').count()
    
    context = {
        "users": users,
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "volunteer_users": volunteer_users,
        "admin_users": admin_users,
        "coordinator_users": coordinator_users,
        "page_title": "User List",
    }
    return render(request, "accounts/user_list.html", context)

@login_required
def toggle_user_status(request, user_id):
    if request.user.role not in ["Admin", "Coordinator"]:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect("dashboard_redirect")
    
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.username} has been {status}.")
    return redirect("manage_users")

@login_required
def delete_user(request, user_id):
    if request.user.role not in ["Admin", "Coordinator"]:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect("dashboard_redirect")
    
    user = get_object_or_404(User, id=user_id)
    if user != request.user:
        user.delete()
        messages.success(request, f"User {user.username} has been deleted.")
    else:
        messages.error(request, "You cannot delete your own account.")
    return redirect("manage_users")

# ---------- Settings ----------
@login_required
def settings_module(request):
    return render(request, "modules/settings.html")

# ---------- Feedback Module ----------
@login_required
def feedback_module(request):
    """
    Entry point so /accounts/modules/feedback/ maps to the feedback app.
    """
    from feedback.views import submit_feedback  # local import avoids circular import
    return submit_feedback(request)