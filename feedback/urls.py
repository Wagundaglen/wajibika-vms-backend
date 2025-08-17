from django.urls import path
from . import views

urlpatterns = [
    # ---------------------------------
    # Volunteer Feedback
    # ---------------------------------
    path("create/", views.FeedbackCreateView.as_view(), name="feedback_create"),
    path("dashboard/", views.FeedbackDashboardView.as_view(), name="feedback_dashboard"),
    path("feedback/<int:pk>/", views.FeedbackDetailView.as_view(), name="feedback_detail"),
    path("feedback/<int:pk>/update/", views.FeedbackUpdateView.as_view(), name="feedback_update"),
    path("feedback/<int:pk>/delete/", views.delete_feedback, name="feedback_delete"),
    path("feedback/<int:pk>/response/", views.FeedbackResponseView.as_view(), name="feedback_response"),
    path("feedback/<int:pk>/resolve/", views.mark_feedback_resolved, name="mark_feedback_resolved"),
    path("my-feedback/", views.MyFeedbackListView.as_view(), name="my_feedback"),

    # ---------------------------------
    # Survey CRUD (Admin/Coordinator)
    # ---------------------------------
    path("survey/create/", views.SurveyCreateView.as_view(), name="survey_create"),
    path("survey/list/", views.SurveyListView.as_view(), name="survey_list"),
    path("survey/<int:pk>/", views.SurveyDetailView.as_view(), name="survey_detail"),
    path("survey/<int:pk>/update/", views.SurveyUpdateView.as_view(), name="survey_update"),
    path("survey/<int:pk>/delete/", views.SurveyDeleteView.as_view(), name="survey_delete"),


    # ---------------------------------
    # Survey Participation (Volunteers)
    # ---------------------------------
    path("survey/<int:pk>/submit/", views.submit_survey, name="submit_survey"),
    path("survey/thanks/", views.SurveyThanksView.as_view(), name="survey_thanks"),

    # ---------------------------------
    # Question Management (Admin/Coordinator)
    # ---------------------------------
    path("survey/<int:survey_pk>/question/create/", views.QuestionCreateView.as_view(), name="question_create"),
    path("survey/<int:survey_pk>/question/<int:pk>/update/", views.QuestionUpdateView.as_view(), name="question_update"),
    path("survey/<int:survey_pk>/question/<int:pk>/delete/", views.QuestionDeleteView.as_view(), name="question_delete"),
]