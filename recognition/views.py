from rest_framework import viewsets, permissions
from .models import Recognition
from .serializers import RecognitionSerializer
from communication.models import Notification

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission: Admins can do anything, volunteers read-only.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class RecognitionViewSet(viewsets.ModelViewSet):
    queryset = Recognition.objects.all()  #  Required so DRF router can detect basename
    serializer_class = RecognitionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            # Admin sees all recognitions
            return self.queryset.order_by('-date_awarded')
        # Volunteer sees only their own recognitions
        return self.queryset.filter(recipient=user).order_by('-date_awarded')

    def perform_create(self, serializer):
        recognition = serializer.save()

        # Create a notification for the recipient
        Notification.objects.create(
            recipient=recognition.recipient,
            message=f"You've earned: {recognition.title}",
            category='recognition',
            link=f"/recognition/{recognition.id}"
        )
