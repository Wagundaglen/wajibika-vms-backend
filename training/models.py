from django.db import models
from django.conf import settings

class TrainingModule(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('text', 'Text'),
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('link', 'External Link'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default='text')
    content = models.TextField(
        blank=True,
        help_text="If content_type is 'text' paste text here. For video/pdf/link, put URL or storage path."
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class TrainingProgress(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not started'),
        ('in_progress', 'In progress'),
        ('completed', 'Completed'),
    ]

    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='training_progress')
    module = models.ForeignKey(TrainingModule, on_delete=models.CASCADE, related_name='progress_records')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # ✅ NEW FIELD

    class Meta:
        unique_together = ('volunteer', 'module')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.volunteer.username} - {self.module.title} ({self.status})"
