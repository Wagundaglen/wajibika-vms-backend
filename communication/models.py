from django.db import models
from django.conf import settings

class Notification(models.Model):
    CATEGORY_CHOICES = [
        ('feedback', 'Feedback'),
        ('task', 'Task'),
        ('training', 'Training'),
        ('recognition', 'Recognition'),
        ('general', 'General'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    message = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')  # NEW
    link = models.CharField(max_length=255, blank=True, null=True)  # NEW
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.category}] To: {self.recipient.username} - {self.message[:30]}"
