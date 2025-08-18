from django.urls import path
from . import views

app_name = "feedback"

urlpatterns = [
    # ---------------------------------
    # Volunteer Feedback
    # ---------------------------------
    path("create/", views.FeedbackCreateView.as_view(), name="feedback_create"),
    path("dashboard/", views.FeedbackDashboardView.as_view(), name="feedback_dashboard"),
    path("feedback/<int:pk>/", views.FeedbackDetailView.as_view(), name="feedback_detail"),
    path("feedback/<int:pk>/update/", views.FeedbackUpdateView.as_view(), name="feedback_update"),
    path("feedback/<int:pk>/delete/", views.FeedbackDeleteView.as_view(), name="feedback_delete"),
    path("feedback/<int:pk>/response/", views.FeedbackResponseView.as_view(), name="feedback_response"),
    path("feedback/<int:pk>/resolve/", views.mark_feedback_resolved, name="mark_feedback_resolved"),
    path("my-feedback/", views.MyFeedbackListView.as_view(), name="my_feedback"),

    # ---------------------------------
    # Survey CRUD (Admin/Coordinator)
    # ---------------------------------
    path("surveys/", views.SurveyListView.as_view(), name="survey_list"),
    path("surveys/create/", views.SurveyCreateView.as_view(), name="survey_create"),
    path("surveys/<int:pk>/", views.SurveyDetailView.as_view(), name="survey_detail"),
    path("surveys/<int:pk>/update/", views.SurveyUpdateView.as_view(), name="survey_update"),
    path("surveys/<int:pk>/delete/", views.SurveyDeleteView.as_view(), name="survey_delete"),

    # ---------------------------------
    # Question CRUD (Admin/Coordinator)
    # ---------------------------------
    path("surveys/<int:survey_id>/questions/add/", views.add_question, name="question_add"),
    path("surveys/<int:survey_id>/questions/<int:pk>/update/", views.QuestionUpdateView.as_view(), name="question_update"),
    path("surveys/<int:survey_id>/questions/<int:pk>/delete/", views.QuestionDeleteView.as_view(), name="question_delete"),

    # ---------------------------------
    # Survey Sending (Admin/Coordinator)
    # ---------------------------------
    path("surveys/send/", views.send_survey, name="send_survey"),

    # ---------------------------------
    # Survey Participation (Volunteers)
    # ---------------------------------
    path("surveys/<int:pk>/submit/", views.submit_survey, name="submit_survey"),
    path("surveys/thanks/", views.SurveyThanksView.as_view(), name="survey_thanks"),

    # ---------------------------------
    # Survey Response Detail
    # ---------------------------------
    path("surveys/responses/<int:pk>/", views.SurveyResponseDetailView.as_view(), name="survey_response_detail"),

    # ---------------------------------
    # Surveys Assigned to Logged-in Volunteer
    # ---------------------------------
    path("my-surveys/", views.AssignedSurveyListView.as_view(), name="assigned_surveys"),

]

