from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import FileResponse, Http404
from django.conf import settings
from django.db import models
import os

from accounts.models import Volunteer
from .models import Recognition
from .utils import generate_certificate


# ========= Role Checks =========
def is_admin(user):
    return user.is_authenticated and user.role == "Admin"

def is_coordinator(user):
    return user.is_authenticated and user.role == "Coordinator"

def is_volunteer(user):
    return user.is_authenticated and user.role == "Volunteer"


# ========= Volunteer Views =========
@login_required
@user_passes_test(is_volunteer)
def recognition(request):
    """Volunteer: View all their earned recognitions and certificates."""
    recognitions = Recognition.objects.filter(volunteer=request.user).order_by("-created_at")
    return render(request, "recognition/volunteer_recognition.html", {
        "recognitions": recognitions
    })


@login_required
@user_passes_test(is_volunteer)
def download_certificate(request, recognition_id):
    """Volunteer: Download a certificate if available."""
    recognition = get_object_or_404(
        Recognition, id=recognition_id, volunteer=request.user, certificate__isnull=False
    )

    file_path = os.path.join(settings.MEDIA_ROOT, str(recognition.certificate))
    if not os.path.exists(file_path):
        messages.error(request, "Certificate file is missing. Please contact support.")
        raise Http404("Certificate not found.")

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename=os.path.basename(file_path)
    )


# ========= Coordinator Views =========
@login_required
@user_passes_test(is_coordinator)
def volunteer_recognition(request, volunteer_id):
    """Coordinator: View & manage recognitions for a specific volunteer."""
    volunteer = get_object_or_404(Volunteer, id=volunteer_id)
    recognitions = Recognition.objects.filter(volunteer=volunteer).order_by("-created_at")

    return render(request, "recognition/coordinator_volunteer.html", {
        "volunteer": volunteer,
        "recognitions": recognitions
    })


@login_required
@user_passes_test(is_coordinator)
def create_certificate(request, volunteer_id):
    """Coordinator: Generate a recognition certificate for a volunteer."""
    volunteer = get_object_or_404(Volunteer, id=volunteer_id)

    cert = generate_certificate(volunteer)
    recognition = Recognition.objects.create(volunteer=volunteer, certificate=cert)

    messages.success(request, f"Certificate successfully generated for {volunteer.get_full_name()}.")
    return redirect("recognition:volunteer_recognition", volunteer_id=volunteer.id)


@login_required
@user_passes_test(is_coordinator)
def delete_recognition(request, recognition_id):
    """Coordinator: Delete a recognition (if issued in error)."""
    recognition = get_object_or_404(Recognition, id=recognition_id)
    volunteer_id = recognition.volunteer.id
    recognition.delete()

    messages.warning(request, "Recognition deleted successfully.")
    return redirect("recognition:volunteer_recognition", volunteer_id=volunteer_id)


# ========= Admin Views =========
@login_required
@user_passes_test(is_admin)
def recognition_list(request):
    """Admin: View all recognitions across the platform."""
    recognitions = Recognition.objects.select_related("volunteer").order_by("-created_at")
    return render(request, "recognition/admin_list.html", {
        "recognitions": recognitions
    })


@login_required
@user_passes_test(is_admin)
def leaderboard(request):
    """Admin: View volunteer leaderboard by total recognitions."""
    leaderboard_data = (
        Volunteer.objects.annotate(total_recognitions=models.Count("recognition"))
        .order_by("-total_recognitions")
    )
    return render(request, "recognition/leaderboard.html", {
        "leaderboard": leaderboard_data
    })


# ========= Shared Dashboard =========
@login_required
def recognition_dashboard(request):
    """
    Single central Recognition dashboard for all roles
    """
    return render(request, "recognition/recognition_dashboard.html")
