from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from django.utils.timezone import now
from .models import TrainingModule, TrainingProgress
from .serializers import TrainingModuleSerializer, TrainingProgressSerializer


# LIST (public) + CREATE (admin only) for modules
class TrainingModuleListCreateView(generics.ListCreateAPIView):
    queryset = TrainingModule.objects.all()
    serializer_class = TrainingModuleSerializer

    # Allow anyone to GET the list, but require authentication for POST (checked below)
    def get_permissions(self):
        if self.request.method == 'GET':
            # Public: anyone can list modules (no credentials required)
            return [permissions.AllowAny()]
        # For POST (creating a module) require authentication
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        # Only admins can create modules
        if not self.request.user.is_staff:
            raise permissions.PermissionDenied("Only admins may create training modules.")
        serializer.save(created_by=self.request.user)


# Retrieve single module (public read)
class TrainingModuleDetailView(generics.RetrieveAPIView):
    queryset = TrainingModule.objects.all()
    serializer_class = TrainingModuleSerializer
    permission_classes = [permissions.AllowAny]


# Progress views
class TrainingProgressListCreateView(generics.ListCreateAPIView):
    """
    GET: list the requesting user's training progress (admins see all)
    POST: create a progress record (volunteer marks as started / added)
    """
    serializer_class = TrainingProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return TrainingProgress.objects.all().order_by('-created_at')
        return TrainingProgress.objects.filter(volunteer=user).order_by('-created_at')

    def perform_create(self, serializer):
        user = self.request.user

        if not user.is_staff:
            # Volunteers → always assign to themselves
            serializer.save(volunteer=user)
        else:
            # Admins → can pass volunteer or default to themselves
            volunteer_from_payload = serializer.validated_data.get('volunteer')
            if volunteer_from_payload:
                serializer.save()
            else:
                serializer.save(volunteer=user)


class TrainingProgressUpdateView(generics.UpdateAPIView):
    """
    PATCH: update status (e.g., in_progress / completed). When marking completed, set completed_at.
    """
    queryset = TrainingProgress.objects.all()
    serializer_class = TrainingProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return TrainingProgress.objects.all()
        return TrainingProgress.objects.filter(volunteer=user)

    def perform_update(self, serializer):
        # If status becomes 'completed' (case-insensitive), set completed_at
        status_value = serializer.validated_data.get('status', None)
        if status_value and str(status_value).lower() == 'completed':
            serializer.save(completed_at=now())
        else:
            serializer.save()
