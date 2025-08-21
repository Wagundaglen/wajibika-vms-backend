from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Unified task list for all roles (Admins, Coordinators, Volunteers)
    path("", views.task_list, name="tasks_module"),
    
    # Admin/Coordinator creates a task
    path("create/", views.create_task, name="create_task"),
    
    # Task detail view
    path("<int:task_id>/", views.task_detail, name="task_detail"),
    
    # Admin/Coordinator edits a task
    path("<int:task_id>/edit/", views.edit_task, name="edit_task"),

    # Admin/Coordinator deletes a task
    path('modules/tasks/delete/<int:task_id>/', views.delete_task, name='delete_task'),
    
    # Volunteer accepts a task
    path("<int:task_id>/accept/", views.accept_task, name="accept_task"),
    
    # Volunteer rejects a task
    path("<int:task_id>/reject/", views.reject_task, name="reject_task"),
    
    # Volunteer updates task status (In Progress / Completed)
    path("<int:task_id>/update-status/", views.update_task_status, name="update_task_status"),
]