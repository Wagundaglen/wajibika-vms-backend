from .models import Notification, Message

def notification_count(request):
    """Add unread notification count to the context"""
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).count()
        
        unread_messages = Message.objects.filter(
            recipient=request.user, 
            is_read=False,
            is_deleted_by_recipient=False
        ).count()
        
        return {
            'unread_count': unread_notifications + unread_messages,
            'unread_notifications': unread_notifications,
            'unread_messages': unread_messages
        }
    return {}

def user_role(request):
    """Add user role to the context"""
    if request.user.is_authenticated:
        return {'user_role': request.user.role}
    return {}