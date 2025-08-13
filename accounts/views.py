from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.views.decorators.csrf import csrf_exempt
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
    context = {
        'paypal_link': 'https://www.paypal.com/donate?hosted_button_id=YOUR_PAYPAL_ID',
        'mpesa_link': 'https://m-pesapay.com/YOUR_MPESA_LINK',
    }
    return render(request, "payment_options.html", context)

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
def logout_user(request):
    logout(request)
    messages.info(request, "✅ You have been logged out.")
    return redirect("login_form")


# ---------- Dashboard Views ----------
@login_required
def admin_dashboard(request):
    return render(request, "dashboards/admin_dashboard.html")

@login_required
def coordinator_dashboard(request):
    return render(request, "dashboards/coordinator_dashboard.html")

@login_required
def volunteer_dashboard(request):
    return render(request, "dashboards/volunteer_dashboard.html")

@login_required
def dashboard_redirect(request):
    if request.user.role == "Admin":
        return redirect("admin_dashboard")
    elif request.user.role == "Coordinator":
        return redirect("coordinator_dashboard")
    elif request.user.role == "Volunteer":
        return redirect("volunteer_dashboard")
    else:
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
    return render(request, "modules/tasks.html", {"tasks": tasks})

@login_required
def create_task(request):
    if request.user.role not in ["Admin", "Coordinator"]:
        messages.error(request, "You are not authorized to create tasks.")
        return redirect("tasks_module")
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_to = User.objects.get(id=request.POST.get("assigned_to"))  # Ensure to set the assigned user
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

# Volunteer task responses
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
def recognition_module(request):
    return render(request, "modules/recognition.html")

@login_required
def feedback_module(request):
    return render(request, "modules/feedback.html")

@login_required
def communication_module(request):
    return render(request, "modules/communication.html")

@login_required
def training_module(request):
    return render(request, "modules/training.html")

@login_required
def reports_module(request):
    return render(request, "modules/reports.html")


# ---------- Manage Users ----------
@login_required
def manage_users(request):
    if request.user.role not in ["Admin", "Coordinator"]:
        messages.error(request, "You are not authorized to access this page.")
        return redirect("dashboard_redirect")
    
    # If Coordinator, filter users to only show Volunteers
    if request.user.role == "Coordinator":
        users = User.objects.filter(role="Volunteer").order_by("-date_joined")
    else:
        users = User.objects.all().order_by("-date_joined")

    return render(request, "modules/manage_users.html", {"users": users})

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
    if user != request.user:  # Prevent self-deletion
        user.delete()
        messages.success(request, f"User {user.username} has been deleted.")
    else:
        messages.error(request, "You cannot delete your own account.")
    return redirect("manage_users")


# ---------- Settings ----------
@login_required
def settings_module(request):
    return render(request, "modules/settings.html")