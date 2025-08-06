from django.urls import path
from .views import (
    TaskCreateView,
    MyTasksView,
    TaskStatusUpdateView,
    TaskAcceptView,
    TaskRejectView
)

urlpatterns = [
    # Admin creates a task
    path('create/', TaskCreateView.as_view(), name='task-create'),

    # Volunteer views their own tasks
    path('my-tasks/', MyTasksView.as_view(), name='my-tasks'),

    # Volunteer updates status of an accepted task
    path('<int:pk>/update-status/', TaskStatusUpdateView.as_view(), name='task-update-status'),

    # Volunteer accepts a task
    path('<int:pk>/accept/', TaskAcceptView.as_view(), name='task-accept'),

    # Volunteer rejects a task
    path('<int:pk>/reject/', TaskRejectView.as_view(), name='task-reject'),
]

