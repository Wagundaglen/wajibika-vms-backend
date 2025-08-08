from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.db.utils import OperationalError, ProgrammingError
from tasks.models import Task


@receiver(post_save, sender=Task)
def award_points(sender, instance, created, **kwargs):
    """
    Awards points, badges, and certificates when a Task is completed.
    Skips execution during migrations or for unrelated models.
    """
    from .models import Recognition
    from communication.models import Notification

    # ✅ Skip unless status is Completed
    if getattr(instance, 'status', None) != 'Completed':
        return

    # ✅ Avoid running during migrations when DB tables might not exist
    try:
        volunteer = instance.assigned_to
    except (OperationalError, ProgrammingError):
        return

    task_title = instance.title

    # Award points
    points_awarded = 10
    recognition = Recognition.objects.create(
        recipient=volunteer,
        recognition_type='points',
        title=f"Completed Task: {task_title}",
        description=f"Task '{task_title}' completed successfully.",
        points_awarded=points_awarded
    )

    # Calculate total points
    total_points = Recognition.objects.filter(recipient=volunteer).aggregate(
        total=models.Sum('points_awarded')
    )['total'] or 0

    # Determine badge
    badge = None
    if 50 <= total_points < 100:
        badge = "Bronze Volunteer"
    elif 100 <= total_points < 200:
        badge = "Silver Volunteer"
    elif total_points >= 200:
        badge = "Gold Volunteer"

    if badge:
        recognition.badge = badge
        recognition.recognition_type = 'badge'
        recognition.save()

        Notification.objects.create(
            recipient=volunteer,
            message=f"🏅 You earned the '{badge}' badge! Keep up the amazing work."
        )

        # Gold → issue certificate
        if badge == "Gold Volunteer":
            certificate_pdf = generate_certificate(volunteer, badge)
            recognition.certificate.save(
                f"certificate_{volunteer.username}.pdf",
                ContentFile(certificate_pdf.getvalue())
            )
            recognition.recognition_type = 'certificate'
            recognition.save()

            Notification.objects.create(
                recipient=volunteer,
                message="📜 Congratulations! Your Gold Volunteer certificate is available for download."
            )

    # General task completion notification
    Notification.objects.create(
        recipient=volunteer,
        message=f"🎉 You earned {points_awarded} points for completing '{task_title}'."
    )


def generate_certificate(user, badge):
    """
    Generates a PDF certificate using ReportLab.
    """
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
    p.drawCentredString(width / 2, height - 280, f"For achieving the {badge} milestone in volunteering.")

    # Signature line
    p.line(100, 150, 300, 150)
    p.drawString(100, 130, "Project Coordinator")

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer
