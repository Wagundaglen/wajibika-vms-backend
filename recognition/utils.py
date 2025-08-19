import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from django.conf import settings
from django.utils import timezone
from .models import Certificate


def generate_certificate(volunteer, title="Certificate of Achievement"):
    """
    Generate a styled PDF certificate for a volunteer and save it in DB.
    """

    # --- File setup ---
    filename = f"{volunteer.user.username}_{timezone.now().strftime('%Y%m%d%H%M%S')}.pdf"
    directory = os.path.join(settings.MEDIA_ROOT, "certificates")
    file_path = os.path.join(directory, filename)

    os.makedirs(directory, exist_ok=True)

    # --- Create PDF canvas ---
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    # --- Border ---
    margin = 30
    c.setStrokeColor(colors.black)
    c.setLineWidth(4)
    c.rect(margin, margin, width - 2*margin, height - 2*margin)

    # --- Header ---
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width/2, height - 1.5*inch, "Wajibika Initiative")

    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width/2, height - 2.5*inch, title)

    # --- Recipient ---
    c.setFont("Helvetica", 16)
    c.drawCentredString(width/2, height - 3.5*inch, "This certificate is proudly presented to")

    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 4.5*inch,
                        volunteer.user.get_full_name() or volunteer.user.username)

    # --- Reason ---
    c.setFont("Helvetica", 14)
    c.drawCentredString(width/2, height - 5.5*inch,
                        "For outstanding contributions and dedication.")

    # --- Date & signature ---
    issue_date = timezone.now().strftime("%d %B %Y")
    c.setFont("Helvetica-Oblique", 12)
    c.drawString(1.5*inch, 1.5*inch, f"Issued on {issue_date}")

    c.line(width - 3.5*inch, 1.5*inch, width - 1.5*inch, 1.5*inch)
    c.setFont("Helvetica", 10)
    c.drawString(width - 3.3*inch, 1.2*inch, "Authorised Signature")

    # --- Finalise ---
    c.showPage()
    c.save()

    # --- Save record in DB ---
    cert = Certificate.objects.create(
        volunteer=volunteer,
        title=title,
        file=f"certificates/{filename}"
    )

    return cert
