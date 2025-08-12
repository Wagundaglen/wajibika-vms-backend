from django.contrib.auth.models import AbstractUser
from django.db import models

class Volunteer(AbstractUser):
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text="Enter phone number in international format e.g. +254712345678"
    )
    skills = models.TextField(
        blank=True,
        null=True,
        help_text="List skills separated by commas"
    )
    role = models.CharField(
        max_length=50,
        choices=(
            ('Volunteer', 'Volunteer'),
            ('Admin', 'Admin'),
            ('Coordinator', 'Coordinator'),
        ),
        default="Volunteer",
        help_text="Select the role for this user"
    )
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        help_text="Upload your profile picture"
    )
    bio = models.TextField(
        blank=True,
        null=True,
        help_text="Write a short bio about yourself"
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Enter your address"
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text="Enter your date of birth"
    )

    class Meta:
        verbose_name = "Volunteer"
        verbose_name_plural = "Volunteers"

    def __str__(self):
        return f"{self.username} ({self.role})"

    def full_contact(self):
        full_name = self.get_full_name().strip() or self.username
        phone_number = self.phone if self.phone else "No phone"
        return f"{full_name} - {phone_number}"
