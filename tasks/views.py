from rest_framework import generics, permissions
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import Task
from .serializers import TaskSerializer, TaskAcceptanceSerializer
from communication.models import Notification

User = get_user_model()

# ---------------------------
# Admin creates tasks
# ---------------------------
class TaskCreateView(generics.CreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        task = serializer.save()
        # Notify the volunteer who was assigned the task
        Notification.objects.create(
            recipient=task.assigned_to,
            message=f"You have been assigned a new task: {task.title}"
        )

# ---------------------------
# Volunteer views their own tasks
# ---------------------------
class MyTasksView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(assigned_to=self.request.user)

# ---------------------------
# Volunteer updates their own task status
# ---------------------------
class TaskStatusUpdateView(generics.UpdateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        task = super().get_object()
        if task.assigned_to != self.request.user:
            raise PermissionDenied("You do not have permission to update this task.")
        if task.acceptance_status != 'Accepted':
            raise PermissionDenied("You must accept the task before updating its status.")
        return task

    def perform_update(self, serializer):
        task = serializer.save()

        # Notify the volunteer themselves
        Notification.objects.create(
            recipient=task.assigned_to,
            message=f"Task '{task.title}' status updated to {task.status}"
        )

        # Notify all admins
        admins = User.objects.filter(is_staff=True, is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                message=f"Volunteer '{task.assigned_to.username}' updated task '{task.title}' to {task.status}"
            )

# ---------------------------
# Volunteer accepts a task
# ---------------------------
class TaskAcceptView(generics.UpdateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskAcceptanceSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        if task.assigned_to != request.user:
            raise PermissionDenied("You can only accept tasks assigned to you.")
        task.acceptance_status = 'Accepted'
        task.status = 'In Progress'
        task.save()

        # Notify all admins
        admins = User.objects.filter(is_staff=True, is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                message=f"{request.user.username} accepted task '{task.title}'."
            )

        return Response({"message": "Task accepted successfully."})

# ---------------------------
# Volunteer rejects a task
# ---------------------------
class TaskRejectView(generics.UpdateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskAcceptanceSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        if task.assigned_to != request.user:
            raise PermissionDenied("You can only reject tasks assigned to you.")
        task.acceptance_status = 'Rejected'
        task.save()

        # Notify all admins
        admins = User.objects.filter(is_staff=True, is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                message=f"{request.user.username} rejected task '{task.title}'."
            )

        return Response({"message": "Task rejected successfully."})

