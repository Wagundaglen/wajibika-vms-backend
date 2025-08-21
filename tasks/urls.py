from django.urls import path
from . import views

urlpatterns = [
    # Unified task list for all roles (Admins, Coordinators, Volunteers)
    path("", views.task_list, name="tasks_module"),

    # Admin/Coordinator creates a task
    path("create/", views.create_task, name="create_task"),

    # Volunteer accepts a task
    path("<int:task_id>/accept/", views.accept_task, name="accept_task"),

    # Volunteer rejects a task
    path("<int:task_id>/reject/", views.reject_task, name="reject_task"),

    # Volunteer updates task status (In Progress / Completed)
    path("<int:task_id>/update-status/", views.update_task_status, name="update_task_status"),
]
