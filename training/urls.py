from django.urls import path
from .views import (
    TrainingModuleListCreateView,
    TrainingModuleDetailView,
    TrainingProgressListCreateView,
    TrainingProgressUpdateView,
)

urlpatterns = [
    # Modules
    path('modules/', TrainingModuleListCreateView.as_view(), name='training-modules'),
    path('modules/<int:pk>/', TrainingModuleDetailView.as_view(), name='training-module-detail'),

    # Progress
    path('progress/', TrainingProgressListCreateView.as_view(), name='training-progress-list-create'),
    path('progress/<int:pk>/', TrainingProgressUpdateView.as_view(), name='training-progress-update'),
]
