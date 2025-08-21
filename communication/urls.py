from django.urls import path
from . import views

urlpatterns = [
    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('notifications/settings/', views.notification_settings, name='notification_settings'),
    
    # Messaging
    path('inbox/', views.inbox, name='inbox'),
    path('sent/', views.sent_messages, name='sent_messages'),
    path('messages/<int:message_id>/', views.read_message, name='read_message'),
    path('send/', views.send_message, name='send_message'),
]