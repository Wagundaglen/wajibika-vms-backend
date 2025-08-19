from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.db.utils import OperationalError, ProgrammingError

from tasks.models import Task
from .models import Recognition, Badge, VolunteerBadge, Certificate
from communication.models import Notification
from accounts.models import Volunteer


@receiver(post_save, sender=Task)
def award_points(sender, instance, created, **kwargs):
    """
    Awards points, badges, and certificates when a Task is completed.
    """
    if getattr(instance, 'status', None) != 'Completed':
        return

    try:
        user = instance.assigned_to  # Volunteer
    except (OperationalError, ProgrammingError, AttributeError):
        return

    task_title = instance.title
    points_awarded = 10

    # --- Award base points recognition ---
    points_recognition = Recognition.objects.create(
        volunteer=user,
        recognition_type='points',
        title=f"Completed Task: {task_title}",
        description=f"Task '{task_title}' completed successfully.",
        points_awarded=points_awarded,
    )

    # --- Update total points ---
    if not hasattr(user, "total_points"):
        # If Volunteer model doesn't have this field, skip
        return
    user.total_points = models.F("total_points") + points_awarded
    user.save(update_fields=["total_points"])
    user.refresh_from_db(fields=["total_points"])

    # --- Check for badge milestones ---
    earned_badge = None
    for badge in Badge.objects.filter(criteria_type="points"):
        if user.total_points >= badge.criteria_value:
            earned_badge, created = VolunteerBadge.objects.get_or_create(
                volunteer=user,
                badge=badge
            )
            if created:
                # Create a badge recognition entry
                Recognition.objects.create(
                    volunteer=user,
                    recognition_type='badge',
                    title=f"Earned Badge: {badge.name}",
                    description=badge.description,
                    badge=badge,
                )
                Notification.objects.create(
                    recipient=user,
                    message=f"🏅 You earned the '{badge.name}' badge! Keep up the amazing work."
                )

                # Gold-level milestone → issue certificate
                if badge.name.lower().startswith("gold"):
                    pdf_buffer = generate_certificate(user, badge.name)
                    cert = Certificate.objects.create(
                        volunteer=user,
                        title=f"{badge.name} Certificate"
                    )
                    cert.file.save(
                        f"certificate_{user.username}.pdf",
                        ContentFile(pdf_buffer.getvalue())
                    )
                    cert.save()

                    Recognition.objects.create(
                        volunteer=user,
                        recognition_type="certificate",
                        title=f"{badge.name} Certificate",
                        description="Awarded for outstanding volunteering.",
                        certificate=cert.file
                    )

                    Notification.objects.create(
                        recipient=user,
                        message="📜 Congratulations! Your Gold Volunteer certificate is available for download."
                    )

    # --- General task completion notification ---
    Notification.objects.create(
        recipient=user,
        message=f"🎉 You earned {points_awarded} points for completing '{task_title}'."
    )


def generate_certificate(user, badge_name):
    """Generates a PDF certificate and returns a BytesIO buffer."""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Title
    p.setFont("Helvetica-Bold", 28)
    p.drawCentredString(width / 2, height - 100, "Certificate of Appreciation")

    # Award text
    p.setFont("Helvetica", 16)
    p.drawCentredString(width / 2, height - 200, "This certificate is proudly presented to")

    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width / 2, height - 240, f"{user.get_full_name() or user.username}")

    p.setFont("Helvetica", 16)
    p.drawCentredString(width / 2, height - 280, f"For achieving the {badge_name} milestone in volunteering.")

    # Signature line
    p.line(100, 150, 300, 150)
    p.drawString(100, 130, "Project Coordinator")

    # Finalize PDF
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer
