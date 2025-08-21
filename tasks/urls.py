from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('create/', views.create_task, name='create_task'),  # This was missing
    path('<int:pk>/', views.task_detail, name='task_detail'),
    path('<int:pk>/accept/', views.accept_task, name='accept_task'),
    path('<int:pk>/reject/', views.reject_task, name='reject_task'),
    path('<int:pk>/update-status/', views.update_task_status, name='update_task_status'),
    path('<int:pk>/edit/', views.edit_task, name='edit_task'),
    path('<int:pk>/delete/', views.delete_task, name='delete_task'),
    path('log-hours/', views.log_hours, name='log_hours'),
    path('my-hours/', views.my_hours, name='my_hours'),
    path('approve-hours/', views.approve_hours, name='approve_hours'),
]