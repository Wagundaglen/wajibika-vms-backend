from rest_framework import viewsets, permissions
from .models import Feedback
from .serializers import FeedbackSerializer
from communication.models import Notification

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()  # ✅ This is what was missing
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Feedback.objects.all()
        return Feedback.objects.filter(to_user=user) | Feedback.objects.filter(from_user=user)

    def perform_create(self, serializer):
        feedback = serializer.save(from_user=self.request.user)

        recipient = feedback.to_user
        if recipient:
            Notification.objects.create(
                recipient=recipient,
                message=f"New feedback from {feedback.from_user or 'Anonymous'}",
                category='feedback',
                link=f"/feedback/{feedback.id}"
            )
