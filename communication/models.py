from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Notification(models.Model):
    CATEGORY_CHOICES = [
        ('feedback', 'Feedback'),
        ('task', 'Task'),
        ('training', 'Training'),
        ('recognition', 'Recognition'),
        ('general', 'General'),
        ('message', 'Message'),  # For communication module
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    message = models.TextField()
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='general'
    )
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.category}] To: {self.recipient} - {self.message[:30]}"

    class Meta:
        ordering = ['-created_at']


class Message(models.Model):
    """
    Represents a direct or broadcast message between users.
    Supports multiple recipients and read tracking.
    """
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    recipients = models.ManyToManyField(
        User,
        related_name='received_messages'
    )
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    is_broadcast = models.BooleanField(default=False)  # For announcements
    created_at = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(
        User,
        related_name='read_messages',
        blank=True
    )

    def __str__(self):
        return f"From {self.sender} - {self.subject or self.body[:30]}"

    def mark_as_read(self, user):
        """Mark the message as read for a specific user."""
        if user not in self.read_by.all():
            self.read_by.add(user)

    class Meta:
        ordering = ['-created_at']
