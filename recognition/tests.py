from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import VolunteerProfile, RecognitionEvent, Badge, VolunteerBadge, Certificate
from tasks.models import TaskCompletion   # Assuming you already have a Task app

# --- Award points when a task is completed ---
@receiver(post_save, sender=TaskCompletion)
def award_points_for_task(sender, instance, created, **kwargs):
    if created:  # only award when task is newly completed
        volunteer = instance.volunteer.recognition_profile  
        points_earned = 10  # you can adjust or make dynamic per task type

        # update volunteer points
        volunteer.points += points_earned
        volunteer.save()

        # log event
        RecognitionEvent.objects.create(
            volunteer=volunteer,
            event_type="task",
            points=points_earned,
            note=f"Completed task: {instance.task.title}"
        )

        # check for badges after points update
        check_for_badges(volunteer)


# --- Helper: Check for badges and award them ---
def check_for_badges(volunteer):
    badges = Badge.objects.all()
    for badge in badges:
        # check tasks completed criteria
        if badge.criteria_type == "tasks_completed":
            tasks_done = volunteer.user.taskcompletion_set.count()
            if tasks_done >= badge.criteria_value:
                assign_badge(volunteer, badge)

        # check points criteria
        elif badge.criteria_type == "points":
            if volunteer.points >= badge.criteria_value:
                assign_badge(volunteer, badge)


# --- Assign badge if not already awarded ---
def assign_badge(volunteer, badge):
    if not VolunteerBadge.objects.filter(volunteer=volunteer, badge=badge).exists():
        VolunteerBadge.objects.create(volunteer=volunteer, badge=badge)

        # log event
        RecognitionEvent.objects.create(
            volunteer=volunteer,
            event_type="milestone",
            points=0,
            note=f"Awarded badge: {badge.name}"
        )
