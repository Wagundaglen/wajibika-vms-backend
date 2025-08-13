from django.urls import path
from .views import (
    create_task_view,  # Updated to match traditional view
    my_tasks_view,     # Updated to match traditional view
    accept_task,       # Updated to match traditional view
    reject_task,       # Updated to match traditional view
)

urlpatterns = [
    # Admin creates a task
    path('create/', create_task_view, name='task-create'),

    # Volunteer views their own tasks
    path('my-tasks/', my_tasks_view, name='my-tasks'),

    # Volunteer accepts a task
    path('<int:task_id>/accept/', accept_task, name='task-accept'),

    # Volunteer rejects a task
    path('<int:task_id>/reject/', reject_task, name='task-reject'),
]