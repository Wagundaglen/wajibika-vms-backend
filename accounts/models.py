from django.contrib.auth.models import AbstractUser
from django.db import models

class Volunteer(AbstractUser):
    phone = models.CharField(max_length=15, blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    role = models.CharField(
        max_length=50,
        choices=(
            ('Volunteer', 'Volunteer'),
            ('Admin', 'Admin'),
            ('Coordinator', 'Coordinator'),
        ),
        default="Volunteer"
    )

    class Meta:
        verbose_name = "Volunteer"
        verbose_name_plural = "Volunteers"

    def __str__(self):
        return self.username

