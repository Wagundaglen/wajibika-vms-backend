# training/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from accounts.models import Volunteer


class TrainingCourse(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration = models.DurationField(help_text="Expected duration to complete the course")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Training Course"
        verbose_name_plural = "Training Courses"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_total_modules(self):
        """Get the total number of modules in this course"""
        return self.modules.count()
    
    def get_total_assignments(self):
        """Get the total number of assignments for this course"""
        return self.trainingassignment_set.count()
    
    def get_completed_assignments(self):
        """Get the number of completed assignments for this course"""
        return self.trainingassignment_set.filter(status='completed').count()
    
    def get_completion_rate(self):
        """Calculate the completion rate for this course"""
        total = self.get_total_assignments()
        completed = self.get_completed_assignments()
        if total > 0:
            return round((completed / total) * 100, 2)
        return 0


class TrainingModule(models.Model):
    course = models.ForeignKey(TrainingCourse, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Training Module"
        verbose_name_plural = "Training Modules"
        ordering = ['order', 'course']
        unique_together = ('course', 'order')
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def get_progress_count(self):
        """Get the number of users who have completed this module"""
        return self.trainingprogress_set.filter(is_completed=True).count()
    
    def get_total_progress(self):
        """Get the total number of users who have started this module"""
        return self.trainingprogress_set.count()


class TrainingAssignment(models.Model):
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE, related_name='training_assignments')
    course = models.ForeignKey(TrainingCourse, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='assigned_trainings'
    )
    assigned_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    
    class Meta:
        verbose_name = "Training Assignment"
        verbose_name_plural = "Training Assignments"
        unique_together = ('volunteer', 'course')
        ordering = ['-assigned_date']
    
    def __str__(self):
        return f"{self.volunteer.username} - {self.course.title}"
    
    def get_progress_percentage(self):
        """Calculate the progress percentage for this assignment"""
        total_modules = self.course.modules.count()
        if total_modules == 0:
            return 0
        
        completed_modules = self.progress.filter(is_completed=True).count()
        return round((completed_modules / total_modules) * 100, 2)
    
    def get_completed_modules(self):
        """Get the number of completed modules for this assignment"""
        return self.progress.filter(is_completed=True).count()
    
    def is_overdue(self):
        """Check if the assignment is overdue"""
        if self.due_date and self.status != 'completed':
            return timezone.now() > self.due_date
        return False
    
    def get_last_activity(self):
        """Get the last activity date for this assignment"""
        last_progress = self.progress.order_by('-completed_at', '-started_at').first()
        if last_progress:
            return last_progress.completed_at or last_progress.started_at
        return self.assigned_date


class TrainingProgress(models.Model):
    assignment = models.ForeignKey(TrainingAssignment, on_delete=models.CASCADE, related_name='progress')
    module = models.ForeignKey(TrainingModule, on_delete=models.CASCADE)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    time_spent = models.DurationField(null=True, blank=True, help_text="Time spent on this module")
    
    class Meta:
        verbose_name = "Training Progress"
        verbose_name_plural = "Training Progress"
        unique_together = ('assignment', 'module')
        ordering = ['assignment', 'module']
    
    def __str__(self):
        return f"{self.assignment.volunteer.username} - {self.module.title}"
    
    def mark_completed(self):
        """Mark the module as completed and update assignment status"""
        self.is_completed = True
        self.completed_at = timezone.now()
        
        # Calculate time spent if started_at exists
        if self.started_at and not self.time_spent:
            self.time_spent = self.completed_at - self.started_at
        
        self.save()
        
        # Check if all modules in the course are completed
        all_modules = self.assignment.course.modules.count()
        completed_modules = TrainingProgress.objects.filter(
            assignment=self.assignment,
            is_completed=True
        ).count()
        
        if all_modules == completed_modules:
            self.assignment.status = 'completed'
            self.assignment.save()
            
            # Check if certificate already exists before creating a new one
            if not hasattr(self.assignment, 'certificate'):
                # Generate certificate
                Certificate.objects.create(
                    assignment=self.assignment,
                    issued_date=timezone.now()
                )
    
    def mark_started(self):
        """Mark the module as started"""
        if not self.started_at:
            self.started_at = timezone.now()
            self.save()
            
            # Update assignment status if it was just assigned
            if self.assignment.status == 'assigned':
                self.assignment.status = 'in_progress'
                self.assignment.save()


class Certificate(models.Model):
    assignment = models.OneToOneField(TrainingAssignment, on_delete=models.CASCADE, related_name='certificate')
    certificate_id = models.CharField(max_length=50, unique=True, editable=False)
    issued_date = models.DateTimeField()
    file = models.FileField(
        upload_to='certificates/', 
        null=True, 
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="Upload PDF certificate file"
    )
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_certificates'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Certificate"
        verbose_name_plural = "Certificates"
        ordering = ['-issued_date']
    
    def __str__(self):
        return f"Certificate for {self.assignment.volunteer.username} - {self.assignment.course.title}"
    
    def save(self, *args, **kwargs):
        if not self.certificate_id:
            # Generate a unique certificate ID
            import uuid
            self.certificate_id = f"CERT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def mark_verified(self, user):
        """Mark the certificate as verified"""
        self.is_verified = True
        self.verified_by = user
        self.verified_at = timezone.now()
        self.save()
    
    def get_file_url(self):
        """Get the URL for the certificate file"""
        if self.file:
            return self.file.url
        return None
    
    def can_download(self, user):
        """Check if a user can download this certificate"""
        # Admins can download any certificate
        if user.is_staff or user.role == 'Admin':
            return True
        
        # Certificate owner can download their own certificate
        if self.assignment.volunteer == user:
            return True
        
        # Coordinators can download certificates of their team members
        if user.role == 'Coordinator':
            # This would need to be adjusted based on your team structure
            return True
        
        return False