from django.urls import path
from .views import (
    FeedbackCreateView,
    MyFeedbackListView,
    FeedbackDashboardView,
    FeedbackUpdateView
)

urlpatterns = [
    path('create/', FeedbackCreateView.as_view(), name='feedback_create'),
    path('my/', MyFeedbackListView.as_view(), name='my_feedback'),
    path('dashboard/', FeedbackDashboardView.as_view(), name='feedback_dashboard'),
    path('update/<int:pk>/', FeedbackUpdateView.as_view(), name='feedback_update'),
]
