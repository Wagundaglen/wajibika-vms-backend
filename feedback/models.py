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

    SENTIMENT_CHOICES = [
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
    ]

    CATEGORY_CHOICES = [
        ('general', 'General Feedback'),
        ('issue', 'Issue Report'),
        ('task', 'Task Related'),
        ('training', 'Training Related'),
        ('survey', 'Survey Response'),
        ('other', 'Other'),
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

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    sentiment = models.CharField(max_length=10, choices=SENTIMENT_CHOICES, blank=True, null=True)

    message = models.TextField()
    response = models.TextField(blank=True, null=True)

    anonymous = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def display_sender(self):
        if self.anonymous:
            return "Anonymous"
        if self.from_user:
            full_name = getattr(self.from_user, "get_full_name", lambda: "")() or ""
            return full_name or getattr(self.from_user, "username", None) or str(self.from_user)
        return "Unknown"

    def __str__(self):
        target = self.to_user if self.to_user else "Admin/Staff"
        return f"{self.get_category_display()} → {target} ({self.status})"

    class Meta:
        ordering = ['-created_at']
