from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import Volunteer
from .models import RecognitionProfile

@receiver(post_save, sender=Volunteer)
def create_recognition_profile(sender, instance, created, **kwargs):
    if created:
        try:
            RecognitionProfile.objects.create(volunteer=instance)
        except Exception:
            # If the table doesn't exist yet, silently fail
            pass

@receiver(post_save, sender=Volunteer)
def save_recognition_profile(sender, instance, **kwargs):
    try:
        # Check if the relation exists before trying to access it
        if hasattr(instance, '_state') and instance._state.adding:
            return
            
        # Only try to save if the recognitionprofile exists
        if RecognitionProfile.objects.filter(volunteer=instance).exists():
            instance.recognitionprofile.save()
    except Exception:
        # If the table doesn't exist yet, silently fail
        pass