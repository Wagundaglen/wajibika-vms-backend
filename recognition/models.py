from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Recognition(models.Model):
    TYPE_CHOICES = [
        ('points', 'Points'),
        ('badge', 'Badge'),
        ('certificate', 'Certificate'),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recognitions'
    )
    recognition_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)  # e.g. "100 Hours of Service", "Team Player Award"
    description = models.TextField(blank=True)
    points_awarded = models.PositiveIntegerField(default=0)
    date_awarded = models.DateTimeField(default=timezone.now)

    # New fields for badges and certificates
    badge = models.CharField(max_length=100, blank=True, null=True)  # Bronze, Silver, Gold
    certificate = models.FileField(upload_to='certificates/', blank=True, null=True)

    def __str__(self):
        return f"{self.title} → {self.recipient}"
