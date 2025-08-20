# training/urls.py

from django.urls import path
from . import views

app_name = 'training'

urlpatterns = [
    # Dashboard URLs
    path('', views.training_dashboard, name='training_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('coordinator/', views.coordinator_dashboard, name='coordinator_dashboard'),
    path('volunteer/', views.volunteer_dashboard, name='volunteer_dashboard'),
    
    # Course Management URLs
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/<int:pk>/update/', views.course_update, name='course_update'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),
    
    # Module Management URLs
    path('courses/<int:course_pk>/modules/create/', views.module_create, name='module_create'),
    path('modules/<int:pk>/update/', views.module_update, name='module_update'),
    path('modules/<int:pk>/delete/', views.module_delete, name='module_delete'),
    
    # Assignment Management URLs
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/assign/', views.assign_training, name='assign_training'),
    path('assignments/<int:pk>/', views.assignment_detail, name='assignment_detail'),
    path('assignments/<int:pk>/update/', views.assignment_update, name='assignment_update'),
    path('assignments/<int:pk>/delete/', views.assignment_delete, name='assignment_delete'),
    
    # Training Progress URLs
    path('assignments/<int:assignment_pk>/modules/<int:module_pk>/start/', 
         views.start_module, name='start_module'),
    path('assignments/<int:assignment_pk>/modules/<int:module_pk>/complete/', 
         views.complete_module, name='complete_module'),
    
    # Certificate URLs
    path('my-certificates/', views.my_certificates, name='my_certificates'),
    path('certificates/<int:pk>/', views.view_certificate, name='view_certificate'),
    path('certificates/<int:pk>/download/', views.download_certificate, name='download_certificate'),
    
    # Additional URLs for integrated views
    path('my-training/', views.my_training, name='my_training'),
    path('team-progress/', views.team_progress, name='team_progress'),
    
]