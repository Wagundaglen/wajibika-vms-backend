from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions
from .models import Recognition
from .serializers import RecognitionSerializer
from communication.models import Notification

class RecognitionViewSet(viewsets.ModelViewSet):
    queryset = Recognition.objects.all()
    serializer_class = RecognitionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        recognition = serializer.save()

        # Create a notification for the recipient
        Notification.objects.create(
            recipient=recognition.recipient,
            message=f"You've earned: {recognition.title}",
            category='recognition',
            link=f"/recognition/{recognition.id}"
        )
