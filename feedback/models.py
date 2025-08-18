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

    # Quick single reply
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
# FEEDBACK RESPONSE MODEL
# -------------------------------------------------
class FeedbackResponse(models.Model):
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name="responses"
    )
    responded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="feedback_responses"
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response by {self.responded_by} on {self.feedback}"


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
        ('rating', 'Rating (1–5)'),
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
        default=1,
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

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    submitted_at = models.DateTimeField(auto_now_add=True)  # ✅ timestamp added

    def __str__(self):
        return f"{self.user} → {self.survey.title} ({self.status})"

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = "Survey Response"
        verbose_name_plural = "Survey Responses"


# -------------------------------------------------
# SURVEY ANSWER MODEL
# -------------------------------------------------
class SurveyAnswer(models.Model):
    response = models.ForeignKey(SurveyResponse, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.response.user} - {self.question.text}"
