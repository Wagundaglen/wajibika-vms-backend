from django.urls import path
from .views import (
    FeedbackCreateView,
    MyFeedbackListView,
    FeedbackDashboardView,
    FeedbackUpdateView,
    FeedbackResponseView,   # ✅ added
    mark_feedback_resolved, # ✅ added
    delete_feedback,
)

urlpatterns = [
    path("create/", FeedbackCreateView.as_view(), name="feedback_create"),
    path("my/", MyFeedbackListView.as_view(), name="my_feedback"),
    path("dashboard/", FeedbackDashboardView.as_view(), name="feedback_dashboard"),
    path("update/<int:pk>/", FeedbackUpdateView.as_view(), name="feedback_update"),
    path("delete/<int:pk>/", delete_feedback, name="feedback_delete"),
    path("<int:pk>/response/", FeedbackResponseView.as_view(), name="feedback_response"),  # ✅ fixed
    path("<int:pk>/resolve/", mark_feedback_resolved, name="mark_feedback_resolved"),  # ✅ added
]
