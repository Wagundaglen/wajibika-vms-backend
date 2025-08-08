from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Feedback(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
    ]

    from_user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='feedback_sent'
    )
    to_user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='feedback_received'
    )
    message = models.TextField()
    anonymous = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # If anonymous, hide sender
        if self.anonymous:
            self.from_user = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Feedback to {self.to_user or 'Admin'} ({self.status})"
