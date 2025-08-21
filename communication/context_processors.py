from .models import Notification, Message

def unread_counts(request):
    if not request.user.is_authenticated:
        return {}

    # Count unread notifications
    unread_notifications = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    # Count unread inbox messages
    unread_inbox = Message.objects.filter(
        recipients=request.user
    ).exclude(read_by=request.user).count()

    return {
        'unread_notifications': unread_notifications,
        'unread_inbox': unread_inbox,
    }
