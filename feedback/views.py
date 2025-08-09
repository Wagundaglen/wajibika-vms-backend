from rest_framework import viewsets, permissions
from .models import Feedback
from .serializers import FeedbackSerializer
from communication.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

class FeedbackViewSet(viewsets.ModelViewSet):
    # ✅ Added queryset so DRF router can determine basename automatically
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Feedback.objects.all().order_by('-created_at')
        # Volunteers can see feedback they sent OR feedback sent to them
        return Feedback.objects.filter(from_user=user) | Feedback.objects.filter(to_user=user)

    def perform_create(self, serializer):
        user = self.request.user

        # For volunteers
        if not user.is_staff:
            anonymous = serializer.validated_data.get('anonymous', False)

            # Set from_user unless anonymous
            if not anonymous:
                serializer.validated_data['from_user'] = user

            # Ensure volunteer feedback goes to admin by default
            serializer.validated_data['to_user'] = None

        feedback = serializer.save()

        # Send notification
        recipient = feedback.to_user
        if recipient:
            # Direct feedback to a specific user
            Notification.objects.create(
                recipient=recipient,
                message=f"New feedback from {feedback.from_user or 'Anonymous'}",
                category='feedback',
                link=f"/feedback/{feedback.id}"
            )
        else:
            # Send to all admins if `to_user` is None
            admins = User.objects.filter(is_staff=True)
            for admin in admins:
                Notification.objects.create(
                    recipient=admin,
                    message=f"New feedback from {feedback.from_user or 'Anonymous'}",
                    category='feedback',
                    link=f"/feedback/{feedback.id}"
                )
