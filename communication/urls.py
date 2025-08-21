from django.urls import path
from . import views

urlpatterns = [
    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    # Messaging
    path('messages/inbox/', views.inbox, name='inbox'),
    path('messages/sent/', views.sent_messages, name='sent_messages'),
    path('messages/<int:message_id>/', views.read_message, name='read_message'),  # <-- THIS LINE
    path('messages/send/', views.send_message, name='send_message'),
]
