# communication/utils.py
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Notification

User = get_user_model()

def send_email_notification(notification):
    """Send email notification to user"""
    try:
        subject = f"New Notification: {notification.category}"
        message = f"""
        Dear {notification.recipient.get_full_name() or notification.recipient.username},
        
        You have a new notification:
        
        {notification.message}
        
        To view this notification, please visit: {settings.SITE_URL}{reverse('notifications_list')}
        
        Thank you,
        The Wajibika Initiative Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [notification.recipient.email],
            fail_silently=True,
        )
        return True
    except Exception as e:
        print(f"Error sending email notification: {e}")
        return False

def send_email_message(message):
    """Send email notification for new messages"""
    try:
        subject = f"New Message: {message.subject or 'No Subject'}"
        message_text = f"""
        Dear {message.recipient.get_full_name() or message.recipient.username},
        
        You have received a new message from {message.sender.get_full_name() or message.sender.username}:
        
        Subject: {message.subject or 'No Subject'}
        Message: {message.body}
        
        To view this message, please visit: {settings.SITE_URL}{reverse('read_message', args=[message.id])}
        
        Thank you,
        The Wajibika Initiative Team
        """
        
        send_mail(
            subject,
            message_text,
            settings.DEFAULT_FROM_EMAIL,
            [recipient.email for recipient in message.recipients.all()],
            fail_silently=True,
        )
        return True
    except Exception as e:
        print(f"Error sending email message: {e}")
        return False