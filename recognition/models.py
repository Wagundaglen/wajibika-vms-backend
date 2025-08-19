from django.db import models
from django.conf import settings
import os
from datetime import datetime


# --------------------------------------
# Central Recognition Log
# --------------------------------------
class Recognition(models.Model):
    RECOGNITION_TYPES = (
        ("points", "Points"),
        ("badge", "Badge"),
        ("certificate", "Certificate"),
        ("thankyou", "Thank You Note"),
    )

    volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # <-- Use your custom Volunteer model
        on_delete=models.CASCADE,
        related_name="recognitions"
    )
    recognition_type = models.CharField(max_length=20, choices=RECOGNITION_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    points_awarded = models.PositiveIntegerField(default=0)
    date_awarded = models.DateTimeField(auto_now_add=True)

    # Optional badge or certificate link
    badge = models.ForeignKey("Badge", on_delete=models.SET_NULL, null=True, blank=True)
    certificate = models.FileField(upload_to="certificates/", blank=True, null=True)

    def __str__(self):
        return f"{self.volunteer.username} - {self.recognition_type}: {self.title}"


# --------------------------------------
# Badge System
# --------------------------------------
class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.ImageField(upload_to="badges/", blank=True, null=True)
    criteria_type = models.CharField(
        max_length=50,
        choices=(
            ("tasks_completed", "Tasks Completed"),
            ("points", "Points Earned"),
            ("hours", "Volunteer Hours"),
        ),
    )
    criteria_value = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class VolunteerBadge(models.Model):
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    date_awarded = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("volunteer", "badge")

    def __str__(self):
        return f"{self.volunteer.username} - {self.badge.name}"


# --------------------------------------
# Certificates
# --------------------------------------
def certificate_upload_path(instance, filename):
    return os.path.join(
        "certificates",
        f"{instance.volunteer.username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    )


class Certificate(models.Model):
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to=certificate_upload_path, blank=True, null=True)
    date_issued = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Certificate: {self.title} - {self.volunteer.username}"
