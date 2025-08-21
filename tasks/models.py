from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import Volunteer

class TaskCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Task(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    ACCEPTANCE_CHOICES = [
        ('Pending', 'Pending'),   # Volunteer hasn't responded yet
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]
    
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),
    ]
    
    # Basic task information
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(TaskCategory, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Assignment details
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tasks',
        help_text="User who created this task"
    )
    
    # Scheduling details
    start_date = models.DateField(help_text="Date when task is scheduled to start")
    start_time = models.TimeField(help_text="Time when task is scheduled to start", null=True, blank=True)
    end_date = models.DateField(help_text="Date when task is scheduled to end", null=True, blank=True)
    end_time = models.TimeField(help_text="Time when task is scheduled to end", null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, help_text="Location where task will take place")
    
    # Skills and requirements
    skills_required = models.TextField(blank=True, help_text="Required skills separated by commas")
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )
    acceptance_status = models.CharField(
        max_length=20,
        choices=ACCEPTANCE_CHOICES,
        default='Pending'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='Medium'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateField()
    
    class Meta:
        ordering = ['-priority', '-created_at']
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
    
    def __str__(self):
        return f"{self.title} - {self.assigned_to.get_full_name() or self.assigned_to.username}"
    
    @property
    def is_overdue(self):
        """Check if task is overdue"""
        return self.due_date < timezone.now().date() and self.status != 'Completed'
    
    @property
    def days_until_due(self):
        """Calculate days remaining until due date"""
        delta = self.due_date - timezone.now().date()
        return delta.days
    
    @property
    def is_upcoming(self):
        """Check if task is scheduled for today or future"""
        today = timezone.now().date()
        return self.start_date >= today
    
    def get_absolute_url(self):
        """Get absolute URL for task detail view"""
        from django.urls import reverse
        return reverse('tasks:task_detail', kwargs={'pk': self.pk})

class TimeEntry(models.Model):
    """Model for tracking volunteer hours"""
    volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='time_entries'
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='time_entries'
    )
    date = models.DateField()
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField(blank=True)
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_time_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.volunteer.username} - {self.hours} hours on {self.date}"