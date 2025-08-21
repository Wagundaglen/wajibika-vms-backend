from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.urls import reverse
from .models import Notification, Message

User = get_user_model()


# ============================
# Notifications
# ============================
@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    return render(request, "communication/notifications.html", {
        "notifications": notifications
    })


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    messages.success(request, "Notification marked as read.")
    return redirect("notifications_list")


@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect("notifications_list")


# ============================
# Messaging
# ============================
@login_required
def inbox(request):
    messages_qs = Message.objects.filter(
        recipients=request.user
    ).order_by('-created_at')
    return render(request, "communication/inbox.html", {"messages_list": messages_qs})


@login_required
def sent_messages(request):
    messages_qs = Message.objects.filter(
        sender=request.user
    ).order_by('-created_at')
    return render(request, "communication/sent_messages.html", {"messages_list": messages_qs})


@login_required
def read_message(request, message_id):
    message_obj = get_object_or_404(
        Message,
        Q(recipients=request.user) | Q(sender=request.user),
        id=message_id
    )
    message_obj.mark_as_read(request.user)
    return render(request, "communication/read_message.html", {"message_obj": message_obj})


@login_required
def send_message(request):
    """
    Send a direct message or broadcast.
    Supports replying with `reply_to` query param.
    """
    reply_to = request.GET.get("reply_to")
    subject_prefill = request.GET.get("subject", "").strip()
    body_prefill = ""
    preselected_user = None

    # Pre-fill recipient & message content when replying
    if reply_to:
        preselected_user = get_object_or_404(User, id=reply_to)
        original_message = Message.objects.filter(
            sender=preselected_user,
            recipients=request.user
        ).order_by('-created_at').first()
        if original_message:
            body_prefill = f"\n\n--- Original message ---\n{original_message.body}"
        if subject_prefill and not subject_prefill.lower().startswith("re:"):
            subject_prefill = f"Re: {subject_prefill}"

    if request.method == "POST":
        subject = request.POST.get("subject", "").strip()
        body = request.POST.get("body", "").strip()
        recipients_ids = request.POST.getlist("recipients")
        is_broadcast = request.POST.get("is_broadcast") == "on"

        if not body:
            messages.error(request, "Message body is required.")
            return redirect("send_message")

        # Determine recipients
        if is_broadcast:
            if request.user.role == "Coordinator":
                recipients = User.objects.filter(role="Volunteer")
            elif request.user.role == "Admin":
                recipients = User.objects.exclude(id=request.user.id)
            else:
                raise PermissionDenied("Only Admins or Coordinators can send broadcast messages.")
        else:
            if reply_to:
                recipients = User.objects.filter(id=reply_to)
            else:
                recipients = User.objects.filter(id__in=recipients_ids)

        if not recipients.exists():
            messages.error(request, "No valid recipients found.")
            return redirect("send_message")

        # Create message
        message_obj = Message.objects.create(
            sender=request.user,
            subject=subject,
            body=body,
            is_broadcast=is_broadcast
        )
        message_obj.recipients.set(recipients)

        # Notify recipients
        for recipient in recipients:
            Notification.objects.create(
                recipient=recipient,
                message=f"📩 New message from {request.user.username}: {subject or body[:30]}",
                category="message",
                link=reverse('read_message', args=[message_obj.id])
            )

        messages.success(request, "Message sent successfully.")
        return redirect("sent_messages")

    # User list for selection
    if request.user.role == "Volunteer":
        users = User.objects.filter(Q(role="Admin") | Q(role="Coordinator"))
    else:
        users = User.objects.exclude(id=request.user.id)

    return render(request, "communication/send_message.html", {
        "users": users,
        "reply_to": reply_to,
        "reply_username": preselected_user.username if preselected_user else "",
        "subject_prefill": subject_prefill,
        "body_prefill": body_prefill
    })
