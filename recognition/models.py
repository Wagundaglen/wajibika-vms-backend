from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum  # Import Sum here
from accounts.models import Volunteer  # Import your custom Volunteer model

class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class RecognitionProfile(models.Model):
    """Additional profile information for volunteers related to recognition system"""
    volunteer = models.OneToOneField(Volunteer, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    total_points = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    join_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.volunteer.username} ({self.volunteer.role})"

class Badge(models.Model):
    SCOPE_CHOICES = [
        ('system', 'System-wide'),
        ('team', 'Team-specific'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True)  # Icon class name
    points_value = models.IntegerField(validators=[MinValueValidator(0)])
    criteria = models.JSONField(default=dict)  # Stores achievement rules
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES, default='system')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(Volunteer, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Recognition(models.Model):
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE, related_name='recognitions_received')
    giver = models.ForeignKey(Volunteer, on_delete=models.CASCADE, related_name='recognitions_given')
    badge = models.ForeignKey(Badge, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField(blank=True)
    points = models.IntegerField(validators=[MinValueValidator(0)])
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Update volunteer's total points
        profile, created = RecognitionProfile.objects.get_or_create(volunteer=self.volunteer)
        profile.total_points += self.points
        profile.save()
        
        # Log points
        PointsLog.objects.create(
            volunteer=self.volunteer,
            points=self.points,
            activity=f"Received recognition: {self.message or 'No message'}",
            related_recognition=self
        )
        
        super().save(*args, **kwargs)

class PointsLog(models.Model):
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE, related_name='points_logs')
    points = models.IntegerField()
    activity = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    related_recognition = models.ForeignKey(Recognition, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"{self.volunteer.username}: {self.points} points - {self.activity}"

class Leaderboard(models.Model):
    TIMEFRAME_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('all_time', 'All Time'),
    ]
    
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE)
    points = models.IntegerField()
    rank = models.IntegerField()
    timeframe = models.CharField(max_length=10, choices=TIMEFRAME_CHOICES)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['volunteer', 'timeframe', 'team']
    
    def __str__(self):
        return f"#{self.rank} {self.volunteer.username} ({self.timeframe})"
    
    @classmethod
    def update_leaderboard(cls, timeframe='all_time', team=None):
        """Update leaderboard for specified timeframe and team"""
        try:
            # Validate timeframe
            valid_timeframes = ['weekly', 'monthly', 'all_time']
            if timeframe not in valid_timeframes:
                raise ValueError(f"Invalid timeframe: {timeframe}. Valid options are: {valid_timeframes}")
            
            # Calculate date range based on timeframe
            now = timezone.now()
            if timeframe == 'weekly':
                start_date = now - timedelta(days=7)
            elif timeframe == 'monthly':
                start_date = now - timedelta(days=30)
            else:
                start_date = None
            
            # Filter recognitions based on timeframe and team
            recognitions = Recognition.objects.all()
            if start_date:
                recognitions = recognitions.filter(created_at__gte=start_date)
            if team:
                recognitions = recognitions.filter(team=team)
            
            # Calculate points for each volunteer
            volunteer_points = recognitions.values('volunteer').annotate(
                total_points=Sum('points')  # Use Sum directly, not models.Sum
            ).order_by('-total_points')
            
            # Clear existing leaderboard entries
            cls.objects.filter(timeframe=timeframe, team=team).delete()
            
            # Create new leaderboard entries
            for rank, entry in enumerate(volunteer_points, 1):
                cls.objects.create(
                    volunteer_id=entry['volunteer'],
                    points=entry['total_points'] or 0,
                    rank=rank,
                    timeframe=timeframe,
                    team=team
            )
                
            return f"Successfully updated {timeframe} leaderboard"
        except Exception as e:
            # Log the error for debugging
            print(f"Error updating leaderboard: {str(e)}")
            raise