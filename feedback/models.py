from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()

class FeedbackCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Feedback(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    SENTIMENT_CHOICES = [
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
    ]
    
    FEEDBACK_TYPE_CHOICES = [
        ('general', 'General Feedback'),
        ('suggestion', 'Suggestion'),
        ('complaint', 'Complaint'),
        ('compliment', 'Compliment'),
        ('issue_report', 'Issue Report'),
    ]
    
    # Optional: If feedback is from a volunteer/staff
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='feedback_given'
    )
    
    # For anonymous feedback
    is_anonymous = models.BooleanField(default=False)
    anonymous_name = models.CharField(max_length=100, blank=True, null=True)
    anonymous_email = models.EmailField(blank=True, null=True)
    
    # Feedback details
    category = models.ForeignKey(
        FeedbackCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    feedback_type = models.CharField(
        max_length=20, 
        choices=FEEDBACK_TYPE_CHOICES, 
        default='general'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    sentiment = models.CharField(
        max_length=10, 
        choices=SENTIMENT_CHOICES, 
        default='neutral'
    )
    
    # For issue tracking
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='medium'
    )
    status = models.CharField(
        max_length=15, 
        choices=STATUS_CHOICES, 
        default='open'
    )
    
    # Assignment and resolution
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_feedback'
    )
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # If status is resolved, set resolved_at
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status != 'resolved' and self.resolved_at:
            self.resolved_at = None
            
        super().save(*args, **kwargs)

class FeedbackResponse(models.Model):
    feedback = models.ForeignKey(
        Feedback, 
        on_delete=models.CASCADE, 
        related_name='responses'
    )
    responder = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    message = models.TextField()
    is_internal = models.BooleanField(default=False)  # Internal notes vs public responses
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Response to {self.feedback.title}"

class FeedbackVote(models.Model):
    """For allowing users to vote on feedback (like/dislike)"""
    feedback = models.ForeignKey(
        Feedback, 
        on_delete=models.CASCADE, 
        related_name='votes'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE
    )
    vote_type = models.CharField(
        max_length=10, 
        choices=[('up', 'Upvote'), ('down', 'Downvote')]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['feedback', 'user']
    
    def __str__(self):
        return f"{self.user.username} {self.vote_type}d {self.feedback.title}"

class FeedbackAnalytics(models.Model):
    """Store aggregated analytics for feedback"""
    date = models.DateField()
    total_feedback = models.IntegerField(default=0)
    positive_count = models.IntegerField(default=0)
    neutral_count = models.IntegerField(default=0)
    negative_count = models.IntegerField(default=0)
    resolved_count = models.IntegerField(default=0)
    avg_resolution_time = models.FloatField(default=0.0)  # in hours
    
    class Meta:
        unique_together = ['date']
    
    def __str__(self):
        return f"Analytics for {self.date}"