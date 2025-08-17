from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

# -------------------------------------------------
# VOLUNTEER MODEL
# -------------------------------------------------
class Volunteer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return self.full_name

# -------------------------------------------------
# FEEDBACK MODEL
# -------------------------------------------------
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
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='feedback_sent',
        verbose_name="Sender"
    )

    to_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='feedback_received',
        verbose_name="Recipient"
    )

    reassigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='feedback_reassigned',
        verbose_name='Reassigned To',
        help_text="If reassigned, this staff member will handle the feedback."
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='general'
    )

    sentiment = models.CharField(
        max_length=10,
        choices=SENTIMENT_CHOICES,
        blank=True, null=True
    )

    message = models.TextField()

    response = models.TextField(
        blank=True, null=True,
        help_text="Coordinator/Admin reply to the volunteer"
    )

    anonymous = models.BooleanField(
        default=False,
        help_text="If checked, sender's identity will be hidden from recipients."
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='feedback_updated',
        verbose_name='Last Updated By'
    )

    resolved_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Date when feedback was marked as resolved."
    )

    survey_sent = models.BooleanField(
        default=False,
        help_text="Indicates if a follow-up survey was sent for this feedback."
    )

    @property
    def user(self):
        return self.from_user

    def display_sender(self):
        """Return display name, respecting anonymity."""
        if self.anonymous:
            return "Anonymous"
        if self.from_user:
            full_name = getattr(self.from_user, "get_full_name", lambda: "")() or ""
            return full_name or getattr(self.from_user, "username", None) or str(self.from_user)
        return "Unknown"

    def mark_resolved(self, user=None):
        """Mark this feedback as resolved."""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        if user:
            self.updated_by = user
        self.save()

    def __str__(self):
        target = self.reassigned_to or self.to_user or "Admin/Staff"
        return f"{self.get_category_display()} → {target} ({self.status})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Volunteer Feedback"
        verbose_name_plural = "Volunteer Feedback"


# -------------------------------------------------
# SURVEY MODEL
# -------------------------------------------------
class Survey(models.Model):
    title = models.CharField(max_length=255, default="General Survey")
    description = models.TextField(blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_surveys"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    assigned_users = models.ManyToManyField(
        User,
        related_name="assigned_surveys",
        blank=True,
        help_text="Users who should complete this survey"
    )

    def __str__(self):
        return f"{self.title} ({self.created_at.strftime('%Y-%m-%d')})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Survey"
        verbose_name_plural = "Surveys"


# -------------------------------------------------
# QUESTION MODEL
# -------------------------------------------------
class Question(models.Model):
    survey = models.ForeignKey(Survey, related_name='questions', on_delete=models.CASCADE)
    text = models.CharField(max_length=300)
    question_type = models.CharField(max_length=50, choices=[
        ('text', 'Text'),
        ('multiple_choice', 'Multiple Choice'),
        # Add more question types if needed
    ])
    required = models.BooleanField(default=False)

    def __str__(self):
        return self.text

    class Meta:
        ordering = ['id']
        verbose_name = "Question"
        verbose_name_plural = "Questions"


# -------------------------------------------------
# SURVEY RESPONSE MODEL
# -------------------------------------------------
class SurveyResponse(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
    ]

    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name="responses",
        null=True, blank=True
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="survey_responses"
    )

    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="survey_assignments",
        help_text="Coordinator/Admin who assigned the survey"
    )

    q1 = models.TextField("What did you enjoy most about the program?", blank=True, null=True)
    q2 = models.TextField("What could we improve?", blank=True, null=True)

    rating = models.IntegerField(
        "Overall rating (1–5)",
        choices=[(i, str(i)) for i in range(1, 6)],
        null=True, blank=True,
        help_text="Optional rating: 1–5 = actual rating"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        survey_title = self.survey.title if self.survey else 'No Survey'
        return f"{self.user} → {survey_title} ({self.status})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Survey Response"
        verbose_name_plural = "Survey Responses"