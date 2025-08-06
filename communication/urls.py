from django.urls import path
from .views import (
    NotificationListView,
    NotificationUpdateView,
    MarkAllNotificationsAsReadView
)

urlpatterns = [
    # List all notifications for the logged-in user
    path('', NotificationListView.as_view(), name='notifications-list'),

    # Mark a single notification as read
    path('<int:pk>/mark-as-read/', NotificationUpdateView.as_view(), name='notification-mark-as-read'),

    # Mark all notifications as read
    path('mark-all-as-read/', MarkAllNotificationsAsReadView.as_view(), name='notifications-mark-all-as-read'),
]

