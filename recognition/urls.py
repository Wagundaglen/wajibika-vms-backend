from django.urls import path
from . import views

app_name = "recognition"

urlpatterns = [
    # Shared Dashboard (Landing page)
    path("", views.recognition_dashboard, name="recognition_home"),
    path("dashboard/", views.recognition_dashboard, name="recognition_dashboard"),

    # Volunteer
    path("download/<int:recognition_id>/", views.download_certificate, name="download_certificate"),

    # Coordinator
    path("volunteer/<int:volunteer_id>/", views.volunteer_recognition, name="volunteer_recognition"),
    path("generate/<int:volunteer_id>/", views.create_certificate, name="create_certificate"),
    path("delete/<int:recognition_id>/", views.delete_recognition, name="delete_recognition"),

    # Admin
    path("all/", views.recognition_list, name="recognition_list"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
]
