from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    # Static pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('volunteer/', views.volunteer, name='volunteer'),
    path('donate/', views.donate, name='donate'),
    path('donate/options/', views.payment_options, name='payment_options'),
    path('contact/', views.contact, name='contact'),

    # Authentication
    path('register/', views.register_form, name='register_form'),
    path('login/', views.login_form, name='login_form'),
    path('logout/', views.logout_user, name='logout_user'),

    # Profile (protected)
    path('profile/', login_required(views.profile_page), name='profile_page'),
    path("profile/edit/", login_required(views.edit_profile), name="edit_profile"),

    # Single dashboard route (protected)
    path("dashboard/", login_required(views.dashboard_redirect), name="dashboard"),

    # Role-specific dashboards (protected)
    path('dashboard/admin/', login_required(views.admin_dashboard), name='admin_dashboard'),
    path('dashboard/coordinator/', login_required(views.coordinator_dashboard), name='coordinator_dashboard'),
    path('dashboard/volunteer/', login_required(views.volunteer_dashboard), name='volunteer_dashboard'),

    # Modules (protected)
    path('modules/tasks/', login_required(views.tasks_module), name='tasks_module'),
    path('modules/recognition/', login_required(views.recognition_module), name='recognition_module'),
    path('modules/feedback/', login_required(views.feedback_module), name='feedback_module'),
    path('modules/communication/', login_required(views.communication_module), name='communication_module'),
    path('modules/training/', login_required(views.training_module), name='training_module'),
    path('modules/reports/', login_required(views.reports_module), name='reports_module'),
    path('modules/manage-users/', login_required(views.manage_users), name='manage_users'),
    path('modules/manage-users/<int:user_id>/toggle-status/', login_required(views.toggle_user_status), name='toggle_user_status'),
    path('modules/manage-users/<int:user_id>/delete/', login_required(views.delete_user), name='delete_user'),
    path('modules/settings/', login_required(views.settings_module), name='settings_module'),
]
