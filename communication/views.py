from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
import logging

from .models import Notification, Message

User = get_user_model()
logger = logging.getLogger(__name__)

# ============================
# Notifications
# ============================
@login_required
def notifications_list(request):
    """List all notifications for the logged-in user"""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    
    # Calculate unread count
    unread_count = notifications.filter(is_read=False).count()
    
    # Return JSON if requested via AJAX
    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.GET.get('format') == 'json':
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'message': notification.message,
                'category': notification.category,
                'link': notification.link,
                'is_read': notification.is_read,
                'created_at': notification.created_at.strftime("%b %d, %Y %H:%M") if notification.created_at else ""
            })
        
        return JsonResponse({
            'notifications': notifications_data,
            'unread_count': unread_count
        })
    
    return render(request, "communication/notifications.html", {
        "notifications": notifications,
        "unread_count": unread_count
    })

@login_required
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    try:
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()
        
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": True, 
                "id": notification_id,
                "unread_count": Notification.objects.filter(recipient=request.user, is_read=False).count()
            })
        
        messages.success(request, "Notification marked as read.")
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        messages.error(request, "An error occurred while marking the notification as read.")
    
    return redirect("notifications_list")

@login_required
def mark_all_notifications_read(request):
    """Mark all unread notifications as read"""
    try:
        updated_count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True)
        
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": True, 
                "count": updated_count,
                "unread_count": 0
            })
        
        messages.success(request, f"Marked {updated_count} notifications as read.")
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}")
        messages.error(request, "An error occurred while marking notifications as read.")
    
    return redirect("notifications_list")

@login_required
def delete_notification(request, notification_id):
    """Delete a specific notification"""
    try:
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        
        if request.method == "POST":
            notification.delete()
            
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "success": True,
                    "unread_count": Notification.objects.filter(recipient=request.user, is_read=False).count()
                })
            
            messages.success(request, "Notification deleted successfully.")
            return redirect("notifications_list")
        
        return render(request, "communication/delete_notification.html", {
            "notification": notification
        })
    except Exception as e:
        logger.error(f"Error deleting notification: {str(e)}")
        messages.error(request, "An error occurred while deleting the notification.")
        return redirect("notifications_list")

# ============================
# Messaging
# ============================
@login_required
def inbox(request):
    """Inbox with messages received by user"""
    messages_qs = Message.objects.filter(
        recipients=request.user
    ).order_by('-created_at')
    
    # Calculate unread count
    unread_count = messages_qs.exclude(read_by=request.user).count()
    
    return render(request, "communication/inbox.html", {
        "messages_list": messages_qs,
        "unread_count": unread_count
    })

@login_required
def sent_messages(request):
    """Messages sent by user"""
    messages_qs = Message.objects.filter(
        sender=request.user
    ).order_by('-created_at')
    
    return render(request, "communication/sent_messages.html", {
        "messages_list": messages_qs
    })

@login_required
def read_message(request, message_id):
    """Read a specific message (mark as read for recipient)"""
    try:
        message_obj = get_object_or_404(
            Message,
            Q(recipients=request.user) | Q(sender=request.user),
            id=message_id
        )
        
        # Mark as read if the user is a recipient
        if request.user in message_obj.recipients.all():
            message_obj.mark_as_read(request.user)
        
        return render(request, "communication/read_message.html", {
            "message_obj": message_obj
        })
    except Exception as e:
        logger.error(f"Error reading message: {str(e)}")
        messages.error(request, "An error occurred while reading the message.")
        return redirect("inbox")

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
    
    # Pre-fill when replying
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
        
        try:
            # Create message
            message_obj = Message.objects.create(
                sender=request.user,
                subject=subject,
                body=body,
                is_broadcast=is_broadcast
            )
            message_obj.recipients.set(recipients)
            
            # Create notifications for recipients
            for recipient in recipients:
                Notification.objects.create(
                    recipient=recipient,
                    message=f"📩 New message from {request.user.username}: {subject or body[:30]}",
                    category="message",
                    link=reverse('read_message', args=[message_obj.id])
                )
            
            messages.success(request, "Message sent successfully.")
            return redirect("sent_messages")
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            messages.error(request, "An error occurred while sending the message.")
    
    # List possible recipients
    if request.user.role == "Volunteer":
        users = User.objects.filter(Q(role="Admin") | Q(role="Coordinator"))
    else:
        users = User.objects.exclude(id=request.user.id)
    
    return render(request, "communication/send_message.html", {
        "users": users,
        "reply_to": reply_to,
        "reply_username": preselected_user.username if preselected_user else "",
        "subject_prefill": subject_prefill,
        "body_prefill": body_prefill,
        "title": "Send Message" if not reply_to else "Reply to Message",
        "action": "Send" if not reply_to else "Reply"
    })

# ============================
# Utility Functions
# ============================
@login_required
def notification_settings(request):
    """Notification settings page"""
    if request.method == "POST":
        # Get form data
        email_notifications = request.POST.get("email_notifications") == "on"
        browser_notifications = request.POST.get("browser_notifications") == "on"
        
        # Save settings (this would typically be saved in a UserSettings model)
        # For now, we'll just show a success message
        messages.success(request, "Notification settings updated successfully.")
        return redirect("notification_settings")
    
    return render(request, "communication/notification_settings.html")

def create_system_notification(recipient, message, category='general', link=None):
    """
    Utility function to create a system notification
    Can be called from other parts of the application
    """
    try:
        notification = Notification.objects.create(
            recipient=recipient,
            message=message,
            category=category,
            link=link
        )
        return notification
    except Exception as e:
        logger.error(f"Error creating system notification: {str(e)}")
        return None

def get_unread_counts(user):
    """
    Utility function to get unread notification and message counts
    Returns a dictionary with counts
    """
    try:
        unread_notifications = Notification.objects.filter(recipient=user, is_read=False).count()
        unread_messages = Message.objects.filter(
            recipients=user
        ).exclude(
            read_by=user
        ).count()
        
        return {
            "unread_notifications": unread_notifications,
            "unread_messages": unread_messages,
            "total_unread": unread_notifications + unread_messages
        }
    except Exception as e:
        logger.error(f"Error getting unread counts: {str(e)}")
        return {
            "unread_notifications": 0,
            "unread_messages": 0,
            "total_unread": 0
        }